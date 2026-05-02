/**
 * Global Teardown for Playwright E2E Tests
 * 
 * Handles:
 * - Test data cleanup
 * - Report generation
 * - Resource cleanup
 */

import type { FullConfig } from '@playwright/test'
import type { JSONReport, JSONReportSuite } from '@playwright/test/reporter'
import * as fs from 'fs'
import * as path from 'path'
import { fileURLToPath } from 'url'

const __filename = fileURLToPath(import.meta.url)
const __dirname = path.dirname(__filename)

async function globalTeardown(_config: FullConfig) {
  console.log('🧹 Running global teardown...')
  
  // Clean up any test artifacts if needed
  const tempDir = path.join(__dirname, '../playwright/.temp')
  if (fs.existsSync(tempDir)) {
    fs.rmSync(tempDir, { recursive: true, force: true })
  }
  
  // Generate summary report
  const resultsPath = path.join(__dirname, '../test-results/results.json')
  if (fs.existsSync(resultsPath)) {
    try {
      const results = JSON.parse(fs.readFileSync(resultsPath, 'utf-8')) as JSONReport
      const summary = generateSummary(results)
      console.log('\n📊 Test Summary:')
      console.log(`   Total: ${summary.total}`)
      console.log(`   Passed: ${summary.passed} ✅`)
      console.log(`   Failed: ${summary.failed} ❌`)
      console.log(`   Skipped: ${summary.skipped} ⏭️`)
      console.log(`   Duration: ${summary.duration}s`)
    } catch {
      // Results file may not exist yet
    }
  }
  
  console.log('✅ Global teardown complete')
}

function generateSummary(results: JSONReport) {
  const suites = results.suites || []
  let total = 0
  let passed = 0
  let failed = 0
  let skipped = 0
  
  function countTests(suite: JSONReportSuite) {
    for (const spec of suite.specs || []) {
      for (const test of spec.tests || []) {
        total++
        const status = test.results?.[0]?.status
        if (status === 'passed') passed++
        else if (status === 'failed') failed++
        else if (status === 'skipped') skipped++
      }
    }
    for (const child of suite.suites || []) {
      countTests(child)
    }
  }
  
  for (const suite of suites) {
    countTests(suite)
  }
  
  return {
    total,
    passed,
    failed,
    skipped,
    duration: Math.round((results.stats?.duration || 0) / 1000),
  }
}

export default globalTeardown
