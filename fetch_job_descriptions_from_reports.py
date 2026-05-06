#!/usr/bin/env python3
"""
Career-Ops CSV Exporter
Reads directly from evaluation reports in reports/, validates URLs,
filters dead links, deduplicates, and exports a clean CSV.
"""

import csv
import os
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path
import requests

# Headers to avoid blocking
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}


def extract_report_data(report_path):
    """Extract key data from an evaluation report markdown file. No HTML, no JD parsing."""
    try:
        with open(report_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Extract report number from filename (first segment before first dash)
        report_num = Path(report_path).stem.split('-')[0]

        # Extract company and role from title line
        # Handles: "# Evaluación: Company — Role" or "# Evaluation: Company — Role"
        title_match = re.search(
            r'^#\s+Evalu[a-z]+:\s+(.+?)\s+[—\-]{1,3}\s+(.+?)$',
            content,
            re.MULTILINE | re.IGNORECASE
        )
        if not title_match:
            return None

        company = title_match.group(1).strip()
        role = title_match.group(2).strip()

        # Extract date (Fecha / Date)
        date_match = re.search(r'\*\*(?:Fecha|Date):\*\*\s+(\d{4}-\d{2}-\d{2})', content)
        date_saved = date_match.group(1) if date_match else ""

        # Extract score
        score_match = re.search(r'\*\*Score:\*\*\s+([\d.]+)/5', content)
        score = score_match.group(1) if score_match else "N/A"

        # Extract URL (first URL line, strip trailing [EXPIRED ...] annotations)
        url_match = re.search(r'\*\*(?:URL|Original URL):\*\*\s+(https?://[^\s\[]+)', content)
        url = url_match.group(1).strip() if url_match else ""

        # Extract recommendation note — plain text only, first 150 chars
        rec_match = re.search(r'\*\*Recommendation:\*\*\s+(.+?)(?:\n---|\Z)', content, re.DOTALL)
        rec_text = rec_match.group(1).strip() if rec_match else ""
        # Strip any markdown bold/italic from the note
        rec_text = re.sub(r'\*\*(.*?)\*\*', r'\1', rec_text)
        rec_text = re.sub(r'\*(.*?)\*', r'\1', rec_text)
        rec_text = rec_text.replace('\n', ' ').strip()[:150]

        notes = f"Report #{report_num} ({score}/5): {rec_text}" if rec_text else f"Report #{report_num} ({score}/5)"

        return {
            'report_num': int(report_num) if report_num.isdigit() else 0,
            'Job Position': role,
            'Company': company,
            'Status': 'Evaluated',
            'Date Saved': date_saved,
            'Date Applied': '',
            'URL': url,
            'Type': '',
            'Resume': '',
            'Cover Letter': '',
            'Notes': notes,
            'Tasks': '',
            'Location': '',
            'Job Description': '',   # intentionally empty — avoids HTML leakage
            'Salary': '',
            'Contact': '',
            'Source': 'Career-Ops Evaluation'
        }

    except Exception as e:
        print(f"  WARNING: Error reading {report_path.name}: {e}")
        return None


def is_job_still_valid(url):
    """Return True if the URL resolves to an active job posting."""
    if not url:
        return False
    try:
        response = requests.get(url, headers=HEADERS, timeout=10, allow_redirects=True)

        if response.status_code in (404, 410):
            print(f"    Status: {response.status_code}")
            return False
        if response.status_code == 403:
            print(f"    Status: 403 Forbidden / Cloudflare")
            return False
        if response.status_code >= 500:
            print(f"    Status: {response.status_code} Server Error")
            return False

        content_lower = response.text.lower()

        # Cloudflare JS-challenge page
        if 'cloudflare' in content_lower and 'please enable js' in content_lower:
            print(f"    Status: Cloudflare JS challenge (inaccessible)")
            return False

        # Generic JS-required page
        if 'please enable' in content_lower and (
            'javascript' in content_lower or 'js' in content_lower
        ):
            print(f"    Status: JavaScript required (inaccessible)")
            return False

        # Soft-404 / closed posting patterns (English + German)
        closed_patterns = [
            r'job.*?no.*?longer.*?open',
            r'job.*?closed',
            r'position.*?no.*?longer.*?available',
            r'job.*?not.*?found',
            r'posting.*?expired',
            r'position.*?filled',
            r'stelle.*?nicht.*?mehr.*?verf[üu]gbar',
            r'ausschreibung.*?geschlossen',
            r'stelle.*?geschlossen',
            r'diese stelle existiert nicht',
            r'stelle wurde bereits vergeben',
        ]
        for pattern in closed_patterns:
            if re.search(pattern, content_lower):
                print(f"    Status: Posting closed (pattern match)")
                return False

        print(f"    Status: Valid ({response.status_code})")
        return True

    except requests.Timeout:
        print(f"    Status: Timeout")
        return False
    except requests.ConnectionError:
        print(f"    Status: Connection error")
        return False
    except Exception as e:
        print(f"    Status: Error — {e}")
        return False


def load_previous_jobs():
    """Load (Job Position, Company) tuples from all previous CSV files for deduplication."""
    previous_jobs = {}
    for csv_file in sorted(Path('data').glob('enhancv_import_set_*.csv')):
        try:
            with open(csv_file, 'r', encoding='utf-8') as f:
                for row in csv.DictReader(f):
                    job_pos = row.get('Job Position', '').strip()
                    company  = row.get('Company', '').strip()
                    date_saved = row.get('Date Saved', '').strip()
                    if job_pos and company:
                        key = (job_pos.lower(), company.lower())
                        if key not in previous_jobs or date_saved < previous_jobs[key]:
                            previous_jobs[key] = date_saved
        except Exception as e:
            print(f"  WARNING: Could not read {csv_file.name}: {e}")
    return previous_jobs


def process_reports(output_file, days_back=7, skip_url_check=False):
    """
    Main pipeline:
    1. Scan reports/ directory for evaluation markdown files
    2. Extract metadata (no JD / no HTML)
    3. Optionally validate URLs and filter dead links
    4. Deduplicate against previous CSVs
    5. Filter to last `days_back` days
    6. Write clean CSV
    """
    reports_dir = Path('reports')
    if not reports_dir.exists():
        print("ERROR: reports/ directory not found")
        return False

    report_files = sorted(reports_dir.glob('*.md'), reverse=True)
    print(f"Found {len(report_files)} report files in reports/\n")

    today_str = datetime.now().strftime('%Y-%m-%d')
    cutoff_dt  = datetime.now() - timedelta(days=days_back)
    cutoff_str = cutoff_dt.strftime('%Y-%m-%d')

    previous_jobs = load_previous_jobs()
    print(f"Deduplication: {len(previous_jobs)} jobs tracked in previous CSVs")
    print(f"Date filter: including jobs from {cutoff_str} onwards\n")

    data       = []
    dead_links = []
    skipped_old = skipped_dup = skipped_dead = 0

    for report_file in report_files:
        row = extract_report_data(report_file)
        if not row:
            continue

        company    = row['Company']
        role       = row['Job Position']
        date_saved = row['Date Saved']
        url        = row['URL']
        report_num = row.pop('report_num')   # internal field, not in CSV

        print(f"[#{report_num:03d}] {company} — {role[:50]}")
        print(f"       Date: {date_saved}  URL: {url[:70] if url else '(none)'}")

        # --- Date filter ---
        if date_saved and date_saved < cutoff_str:
            print(f"       SKIP: older than {days_back} days\n")
            skipped_old += 1
            continue

        # --- Deduplication ---
        key = (role.lower(), company.lower())
        if key in previous_jobs:
            print(f"       SKIP: duplicate (previously in {previous_jobs[key]})\n")
            skipped_dup += 1
            continue

        # --- URL validation (dead link check) ---
        if url and not skip_url_check:
            if not is_job_still_valid(url):
                print(f"       SKIP: dead link\n")
                skipped_dead += 1
                dead_links.append({'company': company, 'role': role,
                                   'url': url, 'date': date_saved})
                continue
        elif not url:
            print(f"       NOTE: no URL — including without validation")

        print(f"       INCLUDE\n")
        data.append(row)

    # --- Write CSV ---
    print("=" * 70)
    print("PROCESSING SUMMARY")
    print("=" * 70)
    print(f"  Reports scanned:        {len(report_files)}")
    print(f"  Skipped (too old):      {skipped_old}")
    print(f"  Skipped (duplicate):    {skipped_dup}")
    print(f"  Skipped (dead link):    {skipped_dead}")
    print(f"  Final entries in CSV:   {len(data)}")
    print("=" * 70)

    if not data:
        print("\nNo entries to export after filtering.")
        return False

    os.makedirs(os.path.dirname(output_file) or '.', exist_ok=True)

    fieldnames = [
        'Job Position', 'Company', 'Status', 'Date Saved', 'Date Applied',
        'URL', 'Type', 'Resume', 'Cover Letter', 'Notes', 'Tasks',
        'Location', 'Job Description', 'Salary', 'Contact', 'Source'
    ]

    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)

    print(f"\nCSV saved: {output_file}")

    if dead_links:
        dead_file = output_file.replace('.csv', '_dead-links.txt')
        with open(dead_file, 'w', encoding='utf-8') as f:
            f.write(f"DEAD LINKS — {datetime.now():%Y-%m-%d %H:%M}\n")
            f.write(f"Total: {len(dead_links)}\n{'='*80}\n\n")
            for i, d in enumerate(dead_links, 1):
                f.write(f"[{i}] {d['company']} — {d['role']}\n")
                f.write(f"    Date: {d['date']}\n    URL:  {d['url']}\n\n")
        print(f"Dead links report: {dead_file}  ({len(dead_links)} links)")

    return True


if __name__ == '__main__':
    project_dir = Path(__file__).parent
    os.chdir(project_dir)

    today      = datetime.now().strftime('%Y-%m-%d')
    output_file = str(project_dir / 'data' / f'enhancv_import_set_{today}.csv')

    print("Career-Ops CSV Exporter")
    print("=" * 50)
    print(f"Project : {project_dir}")
    print(f"Reports : {project_dir / 'reports'}")
    print(f"Output  : {output_file}")
    print("=" * 50 + "\n")

    success = process_reports(output_file, days_back=7)
    sys.exit(0 if success else 1)
