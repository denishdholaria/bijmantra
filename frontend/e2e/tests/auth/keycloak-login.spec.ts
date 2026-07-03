/**
 * Keycloak browser login regression.
 *
 * This test intentionally bypasses the legacy local-password global setup.
 * Run it with:
 *   E2E_KEYCLOAK_EMAIL=admin@bijmantra.org E2E_KEYCLOAK_PASSWORD='Admin123!' bun run test:auth:keycloak
 */

import { expect, test, type Page } from '@playwright/test'

const KEYCLOAK_EMAIL = process.env.E2E_KEYCLOAK_EMAIL || process.env.E2E_ADMIN_EMAIL
const KEYCLOAK_PASSWORD = process.env.E2E_KEYCLOAK_PASSWORD || process.env.E2E_ADMIN_PASSWORD
const KEYCLOAK_ISSUER =
  process.env.E2E_KEYCLOAK_ISSUER || 'http://localhost:8084/realms/bijmantra'
const KEYCLOAK_AUDIENCE = process.env.E2E_KEYCLOAK_AUDIENCE || 'bijmantra-api'

type JwtPayload = {
  sub?: string
  aud?: string | string[]
  iss?: string
}

function isTokenEndpoint(url: string) {
  return url.includes('/realms/bijmantra/protocol/openid-connect/token')
}

function hasAudience(payload: JwtPayload, audience: string) {
  if (Array.isArray(payload.aud)) {
    return payload.aud.includes(audience)
  }

  return payload.aud === audience
}

function decodeJwtPayload(token: string): JwtPayload {
  const payload = token.split('.')[1]
  if (!payload) {
    throw new Error('Token is not a JWT')
  }

  const normalized = payload.replace(/-/g, '+').replace(/_/g, '/')
  const padded = normalized.padEnd(normalized.length + ((4 - (normalized.length % 4)) % 4), '=')
  return JSON.parse(Buffer.from(padded, 'base64').toString('utf8')) as JwtPayload
}

async function completeKeycloakLogin(page: Page) {
  await expect(page.locator('input[name="username"], input#username').first()).toBeVisible({
    timeout: 20_000,
  })
  await page.locator('input[name="username"], input#username').first().fill(KEYCLOAK_EMAIL!)
  await page.locator('input[name="password"], input#password').first().fill(KEYCLOAK_PASSWORD!)

  await page.locator('input[name="login"], button[type="submit"], #kc-login').first().click()
}

test.describe('Keycloak auth', () => {
  test('logs in through Keycloak and exchanges a backend-accepted API token', async ({ page }) => {
    test.skip(
      !KEYCLOAK_EMAIL || !KEYCLOAK_PASSWORD,
      'Set E2E_KEYCLOAK_EMAIL and E2E_KEYCLOAK_PASSWORD to run the Keycloak login regression.'
    )

    const consoleErrors: string[] = []
    const pageErrors: string[] = []
    let tokenRequestHeaders: Record<string, string> | null = null

    page.on('console', (message) => {
      if (message.type() === 'error') {
        consoleErrors.push(message.text())
      }
    })
    page.on('pageerror', (error) => pageErrors.push(error.message))
    page.on('request', (request) => {
      if (isTokenEndpoint(request.url())) {
        tokenRequestHeaders = request.headers()
      }
    })

    const tokenResponsePromise = page.waitForResponse(
      (response) => isTokenEndpoint(response.url()) && response.request().method() === 'POST',
      { timeout: 45_000 }
    )
    const meResponsePromise = page.waitForResponse(
      (response) => response.url().includes('/api/auth/me') && response.status() === 200,
      { timeout: 45_000 }
    )

    await page.goto('/gateway')

    const loginVisible = await page
      .locator('input[name="username"], input#username')
      .first()
      .waitFor({ state: 'visible', timeout: 30_000 })
      .then(() => true)
      .catch(() => false)
    if (loginVisible) {
      await completeKeycloakLogin(page)
    }

    const [tokenResponse, meResponse] = await Promise.all([
      tokenResponsePromise,
      meResponsePromise,
    ])

    expect(tokenResponse.status()).toBe(200)
    expect(meResponse.status()).toBe(200)
    expect(tokenRequestHeaders?.['x-trace-id']).toBeUndefined()

    const tokenBody = (await tokenResponse.json()) as { access_token?: string }
    expect(tokenBody.access_token).toBeTruthy()

    const jwtPayload = decodeJwtPayload(tokenBody.access_token!)
    expect(jwtPayload.sub).toBeTruthy()
    expect(jwtPayload.iss).toBe(KEYCLOAK_ISSUER)
    expect(hasAudience(jwtPayload, KEYCLOAK_AUDIENCE)).toBe(true)

    await expect(page).toHaveURL(/\/(gateway|dashboard)(\?|$)/, { timeout: 30_000 })
    await expect(
      page
        .getByRole('button', { name: /open strata application launcher/i })
        .or(page.getByText('BijMantra').first())
        .first()
    ).toBeVisible({ timeout: 20_000 })

    const storedToken = await page.evaluate(() => window.localStorage.getItem('auth_token'))
    expect(storedToken).toBeTruthy()

    const authConsoleErrors = consoleErrors.filter((message) =>
      /cors|x-trace-id|openid-connect|keycloak|err_failed/i.test(message)
    )
    expect(authConsoleErrors).toEqual([])
    expect(pageErrors).toEqual([])
  })
})
