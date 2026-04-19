# Helper: JD Slug Generation

Use this helper whenever a company + role title needs to be converted to a filename slug for `jds/` storage.

Reference this from: `modes/scan.md`, `modes/pipeline.md`, `modes/auto-pipeline.md`, `modes/oferta.md`

---

## Algorithm

Normalize company and role into URL-safe, filesystem-safe slugs:

### Company Slug
```
company_slug = company
  .toLowerCase()
  .replace(/[&\/\\#,+()$~%.'":*?<>{}]/g, '')  # remove special chars
  .replace(/\s+/g, '-')                        # spaces → dashes
  .replace(/-+/g, '-')                         # collapse multiple dashes
  .trim('-')                                   # remove leading/trailing dashes
```

### Role Slug
```
role_slug = title
  .toLowerCase()
  .replace(/[&\/\\#,+()$~%.'":*?<>{}]/g, '')  # remove special chars
  .replace(/\s+/g, '-')                        # spaces → dashes
  .replace(/-+/g, '-')                         # collapse multiple dashes
  .substring(0, 50)                            # max 50 chars
  .trim('-')                                   # remove leading/trailing dashes
```

### File Path
```
filename = "{company_slug}-{role_slug}.md"
filepath = "jds/{filename}"
```

---

## Examples

| Company | Role | Company Slug | Role Slug | Filename |
|---------|------|--------------|-----------|----------|
| Bank Julius Baer | IT Service Owner Rule Engine | bank-julius-baer | it-service-owner-rule-engine | bank-julius-baer-it-service-owner-ru.md |
| Anthropic | Senior ML Engineer, Austin | anthropic | senior-ml-engineer-austin | anthropic-senior-ml-engineer-austin.md |
| J. Safra Sarasin | Trading Application Engineer (FIS Front Arena) | j-safra-sarasin | trading-application-engineer-fis-fr | j-safra-sarasin-trading-application-e.md |
| Stripe / Clearco | Backend Engineer — Payments Platform | stripe-clearco | backend-engineer-payments-platform | stripe-clearco-backend-engineer-paym.md |
| Raiffeisen Schweiz | IT-Application Manager (w/m/d) | raiffeisen-schweiz | it-application-manager-wmd | raiffeisen-schweiz-it-application-mana.md |

---

## Special Cases

### Ampersand (&)
- Input: `"Smith & Sons"` → Output: `smith-sons`

### Slashes
- Input: `"C++ Developer / Low-Level Systems"` → Output: `c-developer-low-level-systems`

### Unicode
- Input: `"Ångström Labs"` → Output: `angstrom-labs` (if normalized)
- Recommend: Use ASCII-safe company names from `portals.yml`

### Multiple Spaces
- Input: `"Senior   ML    Engineer"` → Output: `senior-ml-engineer` (collapsed)

### Long Titles
- Input: `"Principal Staff Engineer - Cloud Infrastructure & Cost Optimization"` (70+ chars)
- Output: `principal-staff-engineer-cloud-infra` (truncated at 50 chars)

---

## Deduplication

### Same Company + Role
- File exists: `jds/anthropic-senior-ml-engineer.md`
- New capture with **same** content → Skip, mark as `jd_dup` in `scan-history.tsv`
- New capture with **different** content → Save as `anthropic-senior-ml-engineer_v2.md`

### Same URL, Different Content (Job Updated)
- Previous: `jds/company-role.md` (captured 2026-01-15)
- Updated: `jds/company-role_v2.md` (captured 2026-02-20)
- Mark in `pipeline.md` as: `- [ ] local:jds/company-role_v2.md | Company | Role (Updated)`

---

## Usage in Modes

### In scan.md (Level 1, 2, 3)
After extracting title + URL + company:
```
1. Generate slug using this algorithm
2. Save JD to jds/{filename}
3. Add to pipeline.md as: - [ ] local:jds/{filename} | {Company} | {Title}
4. Mark in scan-history.tsv as: jd_saved
```

### In pipeline.md / auto-pipeline.md
When processing URLs:
```
1. If URL starts with local:jds/ → read local file
2. If URL normal → fetch JD, then save to jds/{slug} for future reference
```

### In oferta.md
When creating Block I:
```
1. Get company + role from JD
2. Generate slug
3. Reference in Block I header: [jds/{slug}.md](../../jds/{slug}.md)
```

---

## Validation

Before saving, check:
- [ ] Filename is <= 255 chars (filesystem limit)
- [ ] No leading/trailing dashes
- [ ] No consecutive dashes (except if already in content)
- [ ] Directory `jds/` exists
- [ ] File is writable (permissions)

---

## Troubleshooting

**Slug looks wrong:**
- Check for typos in company name or role
- Verify special characters are removed (not just replaced with dashes)
- Use example mapping above as reference

**Filename collision (two roles with same slug):**
- This is OK — slug doesn't need to be globally unique
- Company+role combinations are rare duplicates
- If collision detected, append `_area-of-focus` (e.g., `_backend`, `_frontend`)

**File already exists:**
- Compare content (use hash if available)
- If same → keep existing (mark as `jd_dup`)
- If different → save as `{slug}_v2` or `{slug}_v{N}`
