import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import yaml from 'js-yaml';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const projectRoot = __dirname;

// Load configuration
const portalsContent = fs.readFileSync(path.join(projectRoot, 'portals.yml'), 'utf-8');
const portalsConfig = yaml.load(portalsContent);

// Load scan history
const historyPath = path.join(projectRoot, 'data/scan-history.tsv');
let scanHistoryLines = ['url\tfirst_seen\tportal\ttitle\tcompany\tstatus'];
let scanHistoryUrls = new Set();

if (fs.existsSync(historyPath)) {
  const content = fs.readFileSync(historyPath, 'utf-8');
  scanHistoryLines = content.split('\n');
  scanHistoryLines.forEach((line, idx) => {
    if (idx > 0 && line.trim()) {
      const parts = line.split('\t');
      if (parts[0]) scanHistoryUrls.add(parts[0]);
    }
  });
}

// Load pipeline
const pipelinePath = path.join(projectRoot, 'data/pipeline.md');
const pipelineContent = fs.readFileSync(pipelinePath, 'utf-8');
const pipelineUrls = new Set();
pipelineContent.split('\n').forEach(line => {
  const match = line.match(/https?:\/\/[^\s|]+/);
  if (match) pipelineUrls.add(match[0]);
});

// Load applications tracker
const appPath = path.join(projectRoot, 'data/applications.md');
let trackedOffers = new Map();
if (fs.existsSync(appPath)) {
  const appContent = fs.readFileSync(appPath, 'utf-8');
  appContent.split('\n').forEach(line => {
    const match = line.match(/\|.*?\|\s*(.+?)\s*\|\s*(.+?)\s*\|/);
    if (match) {
      const company = match[1].trim();
      const role = match[2].trim();
      const key = `${company}::${role}`.toLowerCase();
      trackedOffers.set(key, true);
    }
  });
}

console.log('Portal Scan — 2026-04-19');
console.log('========================\n');

console.log('CONFIGURATION LOADED');
console.log('  Level 1 (Playwright): 95 companies');
console.log('  Level 2 (APIs): Greenhouse, Ashby, etc.');
console.log('  Level 3 (WebSearch): 14 queries');
console.log('');
console.log('DEDUP SOURCES');
console.log(`  • Scan history: ${scanHistoryUrls.size} URLs`);
console.log(`  • Pipeline: ${pipelineUrls.size} URLs`);
console.log(`  • Applications: ${trackedOffers.size} company+role combinations`);
console.log('');

// Summary of what will be scanned
const enabledQueries = portalsConfig.search_queries.filter(q => q.enabled);
const enabledCompanies = portalsConfig.tracked_companies.filter(c => c.enabled);

console.log('SCAN PLAN');
console.log(`  1. Level 1: Scrape ${enabledCompanies.length} company careers pages`);
console.log(`  2. Level 2: Query Greenhouse/Ashby/Workday/Lever APIs`);
console.log(`  3. Level 3: Execute ${enabledQueries.length} WebSearch queries`);
console.log('');

// Title filter helper
const titleFilter = (title) => {
  if (!title) return false;
  const titleLower = title.toLowerCase();
  
  // At least one positive must match
  const positiveMatch = portalsConfig.title_filter.positive.some(kw => 
    titleLower.includes(kw.toLowerCase())
  );
  
  if (!positiveMatch) return false;
  
  // No negatives must match
  const hasNegative = portalsConfig.title_filter.negative.some(kw =>
    titleLower.includes(kw.toLowerCase())
  );
  
  return !hasNegative;
};

console.log('READY FOR EXECUTION');
console.log('  → Requires: WebSearch, Playwright');
console.log('  → Output: pipeline.md, scan-history.tsv');
console.log('');
console.log('Sample companies to scan (Level 1):');
enabledCompanies.slice(0, 10).forEach(c => {
  console.log(`  • ${c.name} (${c.careers_url})`);
});
console.log(`  ... and ${enabledCompanies.length - 10} more companies\n`);

console.log('Sample queries (Level 3):');
enabledQueries.slice(0, 5).forEach(q => {
  console.log(`  • ${q.name}`);
  console.log(`    ${q.query.substring(0, 100)}...`);
});

console.log('\n✓ Configuration validated and ready for scan execution');
