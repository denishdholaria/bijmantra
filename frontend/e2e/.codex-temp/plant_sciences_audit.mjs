import fs from 'fs/promises'
import path from 'path'
import { fileURLToPath } from 'url'
import { chromium } from 'playwright'

const __filename = fileURLToPath(import.meta.url)
const __dirname = path.dirname(__filename)
const repoRoot = path.resolve(__dirname, '../../..')
const outputRoot = path.join(repoRoot, 'output/playwright')
const screenshotDir = path.join(outputRoot, 'screenshots')
const reportDir = path.join(outputRoot, 'reports')

const BASE_URL = process.env.E2E_BASE_URL || 'http://localhost:5656'
const TEST_USER = process.env.E2E_TEST_EMAIL || 'demo@bijmantra.org'
const TEST_PASSWORD = process.env.E2E_TEST_PASSWORD || 'Demo123!'

const GLOBAL_BACKGROUND_FAILURES = [
  'http://localhost:5656/brapi/v2/germplasm',
  '/brapi/v2/germplasm',
]

const PRIMARY_BUTTONS = {
  '/programs': 'New Program',
  '/trials': 'New Trial',
  '/studies': 'New Study',
  '/locations': 'New Location',
  '/seasons': 'New Season',
  '/germplasm': 'Add Germplasm',
}

async function ensureDirs() {
  await fs.mkdir(screenshotDir, { recursive: true })
  await fs.mkdir(reportDir, { recursive: true })
}

async function loadPlantSciencesRoutes() {
  const registryPath = path.join(repoRoot, 'frontend/src/framework/registry/divisions.ts')
  const source = await fs.readFile(registryPath, 'utf8')
  const start = source.indexOf("id: 'plant-sciences'")
  const end = source.indexOf('// Division 3:', start)

  if (start === -1 || end === -1) {
    throw new Error('Unable to locate Plant Sciences registry block in frontend/src/framework/registry/divisions.ts')
  }

  const block = source.slice(start, end)
  const itemRegex = /\{\s*id:\s*'([^']+)',\s*name:\s*'([^']+)',\s*route:\s*'([^']+)',\s*isAbsolute:\s*true\s*\}/g
  const seenPaths = new Set(['/dashboard', '/plant-sciences'])
  const routes = [
    { id: 'dashboard', path: '/dashboard', expectedText: 'Dashboard' },
    { id: 'plant_sciences_hub', path: '/plant-sciences', expectedText: 'Plant Sciences' },
  ]

  for (const match of block.matchAll(itemRegex)) {
    const [, id, expectedText, routePath] = match
    if (seenPaths.has(routePath)) {
      continue
    }
    seenPaths.add(routePath)
    routes.push({
      id: id.replace(/-/g, '_'),
      path: routePath,
      expectedText,
      primaryButton: PRIMARY_BUTTONS[routePath] || null,
    })
  }

  return routes
}

async function login(page) {
  await page.goto(`${BASE_URL}/login`, { waitUntil: 'networkidle' })
  await page.locator('input[type="email"], input[name="email"]').first().fill(TEST_USER)
  await page.locator('input[type="password"]').first().fill(TEST_PASSWORD)
  await page.locator('button[type="submit"], button:has-text("Login"), button:has-text("Sign in")').first().click()
  await page.waitForTimeout(2000)
  await page.waitForLoadState('networkidle').catch(() => {})
}

function normalizeTexts(values) {
  return values
    .map((value) => value.replace(/\s+/g, ' ').trim())
    .filter(Boolean)
}

async function collectVisibleTexts(page, selector, limit = 10) {
  const values = await page.locator(selector).evaluateAll((nodes, max) => {
    return nodes
      .map((node) => {
        const element = node
        const text = element.textContent || ''
        const style = window.getComputedStyle(element)
        const rect = element.getBoundingClientRect()
        const isVisible = style.display !== 'none' && style.visibility !== 'hidden' && rect.width > 0 && rect.height > 0
        return isVisible ? text : ''
      })
      .filter(Boolean)
      .slice(0, max)
  }, limit)
  return normalizeTexts(values)
}

async function collectPageData(page, route) {
  const consoleErrors = []
  const pageErrors = []
  const requestFailures = []
  const failedResponses = []

  const onConsole = (msg) => {
    if (msg.type() === 'error') {
      consoleErrors.push(msg.text())
    }
  }
  const onPageError = (error) => {
    pageErrors.push(error.message)
  }
  const onRequestFailed = (request) => {
    requestFailures.push(`${request.method()} ${request.url()} :: ${request.failure()?.errorText || 'request failed'}`)
  }
  const onResponse = (response) => {
    if (response.status() >= 400) {
      failedResponses.push(`${response.status()} ${response.request().method()} ${response.url()}`)
    }
  }

  page.on('console', onConsole)
  page.on('pageerror', onPageError)
  page.on('requestfailed', onRequestFailed)
  page.on('response', onResponse)

  try {
    await page.goto(`${BASE_URL}${route.path}`, { waitUntil: 'domcontentloaded' })
    await page.waitForTimeout(1000)
    await page.waitForLoadState('networkidle', { timeout: 4000 }).catch(() => {})

    const headings = await collectVisibleTexts(page, 'h1, h2, [role="heading"]')
    const buttons = await collectVisibleTexts(page, 'button, a[role="button"]')
    const alerts = await collectVisibleTexts(page, '[role="alert"], .alert, [data-sonner-toast]')
    const bodyText = await page.locator('body').innerText()
    const mainTextSnippet = bodyText.replace(/\s+/g, ' ').trim().slice(0, 400)
    const foundExpectedText = bodyText.toLowerCase().includes(route.expectedText.toLowerCase())
    const bodyLower = bodyText.toLowerCase()
    const primaryButtonSelector = route.primaryButton
      ? `button:has-text("${route.primaryButton}"), a:has-text("${route.primaryButton}")`
      : null
    const foundPrimaryButton = primaryButtonSelector
      ? await page.locator(primaryButtonSelector).first().isVisible().catch(() => false)
      : null
    const nonGlobalFailedResponses = failedResponses.filter(
      (value) => !GLOBAL_BACKGROUND_FAILURES.some((ignored) => value.includes(ignored))
    )
    const hasAccessDenied = bodyLower.includes('capability access denied')
    const hasWorkspaceFallback =
      bodyLower.includes('research workspace') && bodyLower.includes('workspace editor')

    let status = 'pass'
    if (hasAccessDenied) {
      status = 'blocked'
    } else if (route.path === '/dashboard' && !foundExpectedText) {
      status = 'fail'
    } else if (!foundExpectedText || alerts.length > 0 || nonGlobalFailedResponses.length > 0) {
      status = 'warning'
    } else if (hasWorkspaceFallback && route.path !== '/dashboard') {
      status = 'warning'
    }

    const screenshotPath = path.join(screenshotDir, `${route.id}.png`)
    await page.screenshot({ path: screenshotPath, fullPage: true })

    const interactions = []
    if (route.primaryButton && foundPrimaryButton && primaryButtonSelector) {
      const button = page.locator(primaryButtonSelector).first()
      if (await button.isVisible().catch(() => false)) {
        await button.click().catch(() => {})
        await page.waitForTimeout(1000)
        interactions.push({
          action: `click:${route.primaryButton}`,
          urlAfterClick: page.url(),
          headingsAfterClick: await collectVisibleTexts(page, 'h1, h2, [role="heading"]', 6),
        })
        await page.screenshot({
          path: path.join(screenshotDir, `${route.id}_after_primary_action.png`),
          fullPage: true,
        })
      }
    }

    if (route.id === 'linkage_disequilibrium') {
      const tabs = await collectVisibleTexts(page, '[role="tab"]', 8)
      interactions.push({ action: 'collect-tabs', tabs })
      const refreshButton = page.locator('button:has-text("Refresh"), button:has-text("Retry")').first()
      if (await refreshButton.isVisible().catch(() => false)) {
        await refreshButton.click().catch(() => {})
        await page.waitForTimeout(1000)
        interactions.push({
          action: 'click:refresh-or-retry',
          urlAfterClick: page.url(),
          alertsAfterClick: await collectVisibleTexts(page, '[role="alert"], .alert', 6),
        })
      }
    }

    return {
      id: route.id,
      path: route.path,
      expectedText: route.expectedText,
      primaryButton: route.primaryButton || null,
      finalUrl: page.url(),
      title: await page.title(),
      headings,
      buttons: buttons.slice(0, 12),
      alerts,
      mainTextSnippet,
      foundExpectedText,
      foundPrimaryButton,
      consoleErrors: consoleErrors.slice(0, 12),
      pageErrors: pageErrors.slice(0, 12),
      requestFailures: requestFailures.slice(0, 12),
      failedResponses: failedResponses.slice(0, 20),
      nonGlobalFailedResponses: nonGlobalFailedResponses.slice(0, 20),
      screenshotPath,
      interactions,
      status,
    }
  } finally {
    page.off('console', onConsole)
    page.off('pageerror', onPageError)
    page.off('requestfailed', onRequestFailed)
    page.off('response', onResponse)
  }
}

async function run() {
  await ensureDirs()
  const routes = await loadPlantSciencesRoutes()
  const browser = await chromium.launch({ headless: true })
  const context = await browser.newContext({
    viewport: { width: 1440, height: 960 },
  })
  const page = await context.newPage()

  try {
    await login(page)

    const loginState = {
      urlAfterLogin: page.url(),
      headingsAfterLogin: await collectVisibleTexts(page, 'h1, h2, [role="heading"]'),
      buttonsAfterLogin: await collectVisibleTexts(page, 'button, a[role="button"]'),
    }

    await page.screenshot({
      path: path.join(screenshotDir, 'post_login.png'),
      fullPage: true,
    })

    const results = []
    for (const route of routes) {
      results.push(await collectPageData(page, route))
    }

    const report = {
      generatedAt: new Date().toISOString(),
      baseUrl: BASE_URL,
      loginUser: TEST_USER,
      loginState,
      totals: {
        routesTested: results.length,
        passed: results.filter((result) => result.status === 'pass').length,
        warnings: results.filter((result) => result.status === 'warning').length,
        blocked: results.filter((result) => result.status === 'blocked').length,
        failed: results.filter((result) => result.status === 'fail').length,
      },
      results,
    }

    const reportPath = path.join(reportDir, 'plant_sciences_audit.json')
    await fs.writeFile(reportPath, JSON.stringify(report, null, 2))
    console.log(reportPath)
    console.log(JSON.stringify(report.totals))
  } finally {
    await context.close()
    await browser.close()
  }
}

run().catch((error) => {
  console.error(error)
  process.exitCode = 1
})
