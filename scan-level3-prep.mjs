import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import yaml from 'js-yaml';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Read portals.yml
const portalsContent = fs.readFileSync(path.join(__dirname, 'portals.yml'), 'utf-8');
const portalsConfig = yaml.load(portalsContent);

// Read scan history
const historyPath = path.join(__dirname, 'data/scan-history.tsv');
let scanHistory = new Set();
if (fs.existsSync(historyPath)) {
  const lines = fs.readFileSync(historyPath, 'utf-8').split('\n').slice(1);
  lines.forEach(line => {
    if (line.trim()) {
      const parts = line.split('\t');
      if (parts[0]) scanHistory.add(parts[0]);
    }
  });
}

// Read pipeline
const pipelinePath = path.join(__dirname, 'data/pipeline.md');
const pipelineContent = fs.readFileSync(pipelinePath, 'utf-8');
const pipelineUrls = new Set();
pipelineContent.split('\n').forEach(line => {
  const match = line.match(/https?:\/\/[^\s|]+/);
  if (match) pipelineUrls.add(match[0]);
});

console.log('Portal Scan — Configuration Summary');
console.log('===================================\n');

const enabledQueries = portalsConfig.search_queries.filter(q => q.enabled);
const enabledCompanies = portalsConfig.tracked_companies.filter(c => c.enabled);

console.log(`Search Queries (Level 3): ${enabledQueries.length} enabled`);
console.log(`Tracked Companies (Level 1+2): ${enabledCompanies.length} enabled\n`);

console.log('Sample Level 1 (Playwright) companies:');
enabledCompanies.slice(0, 5).forEach(c => {
  console.log(`  • ${c.name}`);
});
console.log(`  ... and ${enabledCompanies.length - 5} more\n`);

console.log('Sample Level 3 (WebSearch) queries:');
enabledQueries.slice(0, 5).forEach(q => {
  console.log(`  • ${q.name}`);
});
console.log(`  ... and ${enabledQueries.length - 5} more\n`);

console.log('Dedup sources:');
console.log(`  • Scan history: ${scanHistory.size} known URLs`);
console.log(`  • Pipeline: ${pipelineUrls.size} pending URLs\n`);

console.log('Title filter:');
console.log(`  • Positive keywords: ${portalsConfig.title_filter.positive.length}`);
console.log(`  • Negative keywords: ${portalsConfig.title_filter.negative.length}`);
console.log(`  • Seniority boost: ${portalsConfig.title_filter.seniority_boost.length}`);

