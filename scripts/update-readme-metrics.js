#!/usr/bin/env node
/**
 * Update README.md metrics from /metrics.json (project root)
 * 
 * Run manually: node scripts/update-readme-metrics.js
 * Or add to pre-commit hook for automatic updates
 */

const fs = require('fs');
const path = require('path');

// Try primary location first, then legacy
const METRICS_PATHS = [
  path.join(__dirname, '..', 'metrics.json'),           // /metrics.json (primary)
  path.join(__dirname, '..', '.kiro', 'metrics.json'),  // /.kiro/metrics.json (legacy)
];
const README_FILE = path.join(__dirname, '..', 'README.md');

function findMetricsFile() {
  for (const metricsPath of METRICS_PATHS) {
    if (fs.existsSync(metricsPath)) {
      return metricsPath;
    }
  }
  return null;
}

function main() {
  // Read metrics
  const METRICS_FILE = findMetricsFile();
  if (!METRICS_FILE) {
    console.error('❌ Metrics file not found in any location:', METRICS_PATHS);
    process.exit(1);
  }
  
  const metrics = JSON.parse(fs.readFileSync(METRICS_FILE, 'utf8'));
  console.log('📊 Loaded metrics from', METRICS_FILE);
  
  // Read README
  if (!fs.existsSync(README_FILE)) {
    console.error('❌ README file not found:', README_FILE);
    process.exit(1);
  }
  
  let readme = fs.readFileSync(README_FILE, 'utf8');
  
  // Define replacements using special markers in README
  // Format: <!-- METRIC:key --> value <!-- /METRIC -->
  const replacements = {
    'PAGES_TOTAL': metrics.pages.total,
    'PAGES_FUNCTIONAL': metrics.pages.functional,
    'PAGES_FUNCTIONAL_PERCENT': Math.round(metrics.pages.functional / metrics.pages.total * 100),
    'PAGES_DEMO': metrics.pages.demo,
    'PAGES_UI_ONLY': metrics.pages.uiOnly,
    'API_TOTAL': metrics.api.totalEndpoints,
    'API_BRAPI': metrics.api.brapiEndpoints,
    'API_BRAPI_COVERAGE': metrics.api.brapiCoverage,
    'API_CUSTOM': metrics.api.customEndpoints,
    'DB_MODELS': metrics.database.models,
    'DB_MIGRATIONS': metrics.database.migrations,
    'DB_SEEDERS': metrics.database.seeders,
    'MODULES_TOTAL': metrics.modules.total,
    'WORKSPACES_TOTAL': metrics.workspaces.total,
    'BUILD_STATUS': metrics.build.status,
    'BUILD_SIZE': metrics.build.sizeMB,
    'BUILD_PWA_ENTRIES': metrics.build.pwaEntries,
    'LAST_UPDATED': metrics.lastUpdated,
  };
  
  let updatedCount = 0;
  
  for (const [key, value] of Object.entries(replacements)) {
    // Pattern: <!-- METRIC:KEY -->anything<!-- /METRIC -->
    const pattern = new RegExp(
      `<!-- METRIC:${key} -->.*?<!-- /METRIC -->`,
      'g'
    );
    const replacement = `<!-- METRIC:${key} -->${value}<!-- /METRIC -->`;
    
    if (readme.match(pattern)) {
      readme = readme.replace(pattern, replacement);
      updatedCount++;
    }
  }
  
  if (updatedCount > 0) {
    fs.writeFileSync(README_FILE, readme);
    console.log(`✅ Updated ${updatedCount} metrics in README.md`);
  } else {
    console.log('ℹ️  No metric markers found in README.md');
    console.log('   Add markers like: <!-- METRIC:PAGES_TOTAL -->220<!-- /METRIC -->');
  }
  
  // Also output current metrics for reference
  console.log('\n📈 Current Metrics:');
  console.log(`   Pages: ${metrics.pages.functional}/${metrics.pages.total} functional`);
  console.log(`   Endpoints: ${metrics.api.totalEndpoints} (${metrics.api.brapiEndpoints} BrAPI)`);
  console.log(`   Models: ${metrics.database.models}`);
  console.log(`   Build: ${metrics.build.sizeMB}`);
}

main();
