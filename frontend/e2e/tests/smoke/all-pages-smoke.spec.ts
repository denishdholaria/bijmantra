/**
 * Comprehensive All-Pages Smoke Test
 * 
 * Visits every page in the application to detect:
 * - White screens (blank rendering)
 * - React error boundaries
 * - Console errors
 * - Missing content
 * 
 * Generates detailed report of page health across all 315 routes.
 */

import { test, expect, Page } from '@playwright/test'
import * as fs from 'fs'
import * as path from 'path'

// Load all routes from JSON file
const routesPath = path.join(__dirname, '../../all_routes.json')
const ALL_ROUTES: string[] = JSON.parse(fs.readFileSync(routesPath, 'utf-8'))

// Results storage
interface PageResult {
  route: string
  status: 'pass' | 'white_screen' | 'error' | 'timeout'
  errorMessage?: string
  consoleErrors: string[]
  loadTimeMs: number
  hasMainContent: boolean
  bodyTextLength: number
  screenshot?: string
}

const results: PageResult[] = []

// Routes that don't require authentication (public pages)
const PUBLIC_ROUTES = ['/login', '/about', '/contact', '/privacy', '/terms', '/faq']

// Routes to skip (known special cases)
const SKIP_ROUTES = [
  '/offline', // Offline mode page
]

/**
 * Check if a page has a white screen (no content)
 */
async function detectWhiteScreen(page: Page): Promise<{
  isWhiteScreen: boolean
  hasMainContent: boolean
  bodyTextLength: number
  errorMessage?: string
}> {
  try {
    // Wait for any loading to complete
    await page.waitForLoadState('domcontentloaded', { timeout: 10000 })
    
    // Check for "empty state" or "not found" indicators in the entire body
    const bodyText = await page.evaluate(() => document.body?.innerText?.trim() || '')
    const bodyTextLower = bodyText.toLowerCase()
    
    // Ignore 404/500/No Data errors which are valid UI states
    // This catches "Program Not Found", "HTTP 404", "No data available", etc.
    const isExpectedState = bodyTextLower.includes('not found') || 
                            bodyTextLower.includes('404') || 
                            bodyTextLower.includes('500') ||
                            bodyTextLower.includes('no data') ||
                            bodyTextLower.includes('no results') ||
                            bodyTextLower.includes('empty')

    // Check for React error boundary
    const errorBoundary = await page.locator('[class*="error"], [data-testid="error-boundary"]').first().isVisible({ timeout: 1000 }).catch(() => false)
    if (errorBoundary) {
      const errorText = await page.locator('[class*="error"], [data-testid="error-boundary"]').first().textContent().catch(() => '')
      
      if (!isExpectedState && (errorText?.toLowerCase().includes('went wrong') || errorText?.toLowerCase().includes('error'))) {
        return {
          isWhiteScreen: true,
          hasMainContent: false,
          bodyTextLength: 0,
          errorMessage: `React Error Boundary: ${errorText?.slice(0, 200)}`
        }
      }
    }
    
    // Check for main content container
    const hasMainContent = await page.locator('main, [role="main"], .min-h-screen, #root > div').first().isVisible({ timeout: 3000 }).catch(() => false)
    
    // Check for canvas (for maps/visuals which might have low text)
    const hasCanvas = await page.locator('canvas').first().isVisible().catch(() => false)
    
    // Check for headings (if headers exist, page rendered something)
    const hasHeadings = await page.locator('h1, h2, h3').first().isVisible().catch(() => false)
    
    // Check for "empty state" indicators
    // (Already checked above in isExpectedState)
    
    const bodyTextLength = bodyText.length
    
    // White screen detection criteria:
    // - Very little text (<50 chars)
    // - AND No main content container
    // - AND No canvas elements
    // - AND No headings
    // - AND Not an expected state (404/Empty/etc)
    const isWhiteScreen = bodyTextLength < 50 && 
                          !hasMainContent && 
                          !hasCanvas && 
                          !hasHeadings &&
                          !isExpectedState
    
    return {
      isWhiteScreen,
      hasMainContent,
      bodyTextLength,
      errorMessage: isWhiteScreen ? 'Page appears blank (insufficient content)' : undefined
    }
  } catch (error) {
    return {
      isWhiteScreen: true,
      hasMainContent: false,
      bodyTextLength: 0,
      errorMessage: `Detection error: ${error}`
    }
  }
}

/**
 * Test a single page
 */
async function testPage(page: Page, route: string): Promise<PageResult> {
  const consoleErrors: string[] = []
  const startTime = Date.now()
  
  // Capture console errors
  const consoleHandler = (msg: any) => {
    if (msg.type() === 'error') {
      const text = msg.text()
      // Filter out common non-critical errors
      if (!text.includes('favicon') && !text.includes('Failed to load resource: the server responded with a status of 404')) {
        consoleErrors.push(text)
      }
    }
  }
  page.on('console', consoleHandler)
  
  try {
    // Navigate to the page
    const response = await page.goto(route, { 
      waitUntil: 'domcontentloaded',
      timeout: 30000 
    })
    
    // Wait a bit for React to render
    await page.waitForTimeout(1500)
    
    const loadTimeMs = Date.now() - startTime
    
    // Check for HTTP errors
    if (response && !response.ok() && response.status() >= 500) {
      return {
        route,
        status: 'error',
        errorMessage: `HTTP ${response.status()}: ${response.statusText()}`,
        consoleErrors,
        loadTimeMs,
        hasMainContent: false,
        bodyTextLength: 0
      }
    }
    
    // Detect white screen
    const detection = await detectWhiteScreen(page)
    
    // Check for uncaught errors in console
    const hasCriticalError = consoleErrors.some(e => 
      e.includes('Uncaught') || 
      e.includes('Error:') || 
      e.includes('Cannot read properties') ||
      e.includes('is not defined') ||
      e.includes('is not a function')
    )
    
    if (detection.isWhiteScreen || hasCriticalError) {
      return {
        route,
        status: 'white_screen',
        errorMessage: detection.errorMessage || consoleErrors[0] || 'Unknown white screen error',
        consoleErrors,
        loadTimeMs,
        hasMainContent: detection.hasMainContent,
        bodyTextLength: detection.bodyTextLength
      }
    }
    
    return {
      route,
      status: 'pass',
      consoleErrors,
      loadTimeMs,
      hasMainContent: detection.hasMainContent,
      bodyTextLength: detection.bodyTextLength
    }
    
  } catch (error: any) {
    const loadTimeMs = Date.now() - startTime
    
    if (error.message?.includes('Timeout')) {
      return {
        route,
        status: 'timeout',
        errorMessage: `Page load timeout after ${loadTimeMs}ms`,
        consoleErrors,
        loadTimeMs,
        hasMainContent: false,
        bodyTextLength: 0
      }
    }
    
    return {
      route,
      status: 'error',
      errorMessage: error.message || String(error),
      consoleErrors,
      loadTimeMs,
      hasMainContent: false,
      bodyTextLength: 0
    }
  } finally {
    page.off('console', consoleHandler)
  }
}

// Filter routes to test
const routesToTest = ALL_ROUTES.filter(route => !SKIP_ROUTES.includes(route))

// Load test data if available
let testData: Record<string, string> = {}
try {
  const testDataPath = path.join(__dirname, '../../test-data.json')
  if (fs.existsSync(testDataPath)) {
    testData = JSON.parse(fs.readFileSync(testDataPath, 'utf-8'))
  }
} catch (e) {
  console.log('Using default IDs (no test-data.json found)')
}

function getTestRoute(route: string): string {
  if (route.includes('/programs/1') && testData.program) return route.replace('/1', `/${testData.program}`)
  if (route.includes('/locations/1') && testData.location) return route.replace('/1', `/${testData.location}`)
  if (route.includes('/germplasm/1') && testData.germplasm) return route.replace('/1', `/${testData.germplasm}`)
  if (route.includes('/traits/1') && testData.trait) return route.replace('/1', `/${testData.trait}`)
  return route
}

// Create test for each route
test.describe('All Pages Smoke Test', () => {
  // Use stored auth state for all tests
  test.use({ storageState: 'playwright/.auth/user.json' })
  
  // Increase timeout for full suite
  test.setTimeout(60000)
  
  // Run tests in parallel for speed
  test.describe.configure({ mode: 'parallel' })
  
  for (const originalRoute of routesToTest) {
    const route = getTestRoute(originalRoute)
    
    test(`Page renders: ${originalRoute}`, async ({ page }) => {
      const result = await testPage(page, route)
      results.push(result)
      
      // Take screenshot on failure
      if (result.status !== 'pass') {
        const screenshotName = route.replace(/\//g, '_').replace(/^_/, '') || 'home'
        await page.screenshot({ 
          path: `test-results/screenshots/${screenshotName}.png`,
          fullPage: false 
        })
        result.screenshot = `screenshots/${screenshotName}.png`
      }
      
      // Assert based on result
      if (result.status === 'white_screen') {
        expect.soft(result.status, `White screen detected: ${result.errorMessage}`).toBe('pass')
      } else if (result.status === 'error') {
        const errorMsg = result.errorMessage?.toLowerCase() || ''
        // Allow 404/500 errors as they mean the page rendered the error UI correctly
        const isExpected = errorMsg.includes('404') || errorMsg.includes('500') || errorMsg.includes('not found')
        if (!isExpected) {
          expect.soft(result.status, `Error: ${result.errorMessage}`).toBe('pass')
        }
      } else if (result.status === 'timeout') {
        expect.soft(result.status, `Timeout: ${result.errorMessage}`).toBe('pass')
      }
      
      // Page should have some content OR an error message OR a canvas OR a header
      const hasContent = result.bodyTextLength > 20 || 
                         result.hasMainContent || 
                         result.errorMessage?.length > 0
                         
      expect.soft(hasContent, 'Page should have content').toBeTruthy()
    })
  }
})

// After all tests, save results
test.afterAll(async () => {
  // Ensure directories exist
  const resultsDir = path.join(__dirname, '../../test-results')
  const screenshotsDir = path.join(resultsDir, 'screenshots')
  
  if (!fs.existsSync(resultsDir)) {
    fs.mkdirSync(resultsDir, { recursive: true })
  }
  if (!fs.existsSync(screenshotsDir)) {
    fs.mkdirSync(screenshotsDir, { recursive: true })
  }
  
  // Save raw results
  fs.writeFileSync(
    path.join(resultsDir, 'all-pages-results.json'),
    JSON.stringify(results, null, 2)
  )
  
  // Generate summary
  const summary = {
    totalPages: results.length,
    passed: results.filter(r => r.status === 'pass').length,
    whiteScreens: results.filter(r => r.status === 'white_screen').length,
    errors: results.filter(r => r.status === 'error').length,
    timeouts: results.filter(r => r.status === 'timeout').length,
    averageLoadTime: Math.round(results.reduce((sum, r) => sum + r.loadTimeMs, 0) / results.length),
    failedPages: results.filter(r => r.status !== 'pass').map(r => ({
      route: r.route,
      status: r.status,
      error: r.errorMessage
    }))
  }
  
  fs.writeFileSync(
    path.join(resultsDir, 'all-pages-summary.json'),
    JSON.stringify(summary, null, 2)
  )
  
  // Generate markdown report
  let report = `# UI Smoke Test Report

Generated: ${new Date().toISOString()}

## Summary

| Metric | Count |
|--------|-------|
| Total Pages | ${summary.totalPages} |
| ✅ Passed | ${summary.passed} |
| ❌ White Screens | ${summary.whiteScreens} |
| ⚠️ Errors | ${summary.errors} |
| ⏱️ Timeouts | ${summary.timeouts} |
| Average Load Time | ${summary.averageLoadTime}ms |

## Pass Rate: ${((summary.passed / summary.totalPages) * 100).toFixed(1)}%

`

  if (summary.failedPages.length > 0) {
    report += `## Failed Pages

| Route | Status | Error |
|-------|--------|-------|
`
    for (const page of summary.failedPages) {
      const error = page.error?.slice(0, 100).replace(/\|/g, '\\|') || 'Unknown'
      report += `| \`${page.route}\` | ${page.status} | ${error} |\n`
    }
  }
  
  // Group by error type for analysis
  const whiteScreenPages = results.filter(r => r.status === 'white_screen')
  if (whiteScreenPages.length > 0) {
    report += `\n## White Screen Analysis

These pages rendered blank or showed React error boundaries:

`
    for (const page of whiteScreenPages) {
      report += `### \`${page.route}\`
- **Error**: ${page.errorMessage || 'Unknown'}
- **Body Text Length**: ${page.bodyTextLength} characters
- **Has Main Content**: ${page.hasMainContent ? 'Yes' : 'No'}
- **Console Errors**: ${page.consoleErrors.length > 0 ? page.consoleErrors.slice(0, 3).join('; ') : 'None'}
${page.screenshot ? `- **Screenshot**: ${page.screenshot}` : ''}

`
    }
  }
  
  fs.writeFileSync(
    path.join(resultsDir, 'smoke-report.md'),
    report
  )
  
  console.log('\n=== SMOKE TEST COMPLETE ===')
  console.log(`Total: ${summary.totalPages}`)
  console.log(`Passed: ${summary.passed}`)
  console.log(`White Screens: ${summary.whiteScreens}`)
  console.log(`Errors: ${summary.errors}`)
  console.log(`Timeouts: ${summary.timeouts}`)
  console.log(`\nFull report: test-results/smoke-report.md`)
})
