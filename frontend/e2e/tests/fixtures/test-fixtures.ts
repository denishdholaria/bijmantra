/**
 * Playwright Test Fixtures
 * 
 * Custom fixtures for BijMantra E2E tests providing:
 * - Authenticated pages
 * - API helpers
 * - Page object models
 * - Test data factories
 */

import { test as base, expect, Page, BrowserContext } from '@playwright/test'
import { LoginPage } from '../../pages/login.page'
import { DashboardPage } from '../../pages/dashboard.page'
import { NavigationHelper } from '../../helpers/navigation.helper'
import { ApiHelper } from '../../helpers/api.helper'
import { TestDataFactory } from '../../helpers/test-data.factory'

// Extend base test with custom fixtures
type CustomFixtures = {
  // Page Objects
  loginPage: LoginPage
  dashboardPage: DashboardPage
  
  // Helpers
  navigation: NavigationHelper
  api: ApiHelper
  testData: TestDataFactory
  
  // Authenticated contexts
  authenticatedPage: Page
  adminPage: Page
}

export const test = base.extend<CustomFixtures>({
  // Login Page Object
  loginPage: async ({ page }, use) => {
    await use(new LoginPage(page))
  },
  
  // Dashboard Page Object
  dashboardPage: async ({ page }, use) => {
    await use(new DashboardPage(page))
  },
  
  // Navigation Helper
  navigation: async ({ page }, use) => {
    await use(new NavigationHelper(page))
  },
  
  // API Helper
  api: async ({ request }, use) => {
    await use(new ApiHelper(request))
  },
  
  // Test Data Factory
  testData: async ({}, use) => {
    await use(new TestDataFactory())
  },
  
  // Pre-authenticated page (uses stored auth state)
  authenticatedPage: async ({ browser }, use) => {
    const context = await browser.newContext({
      storageState: 'playwright/.auth/user.json',
    })
    const page = await context.newPage()
    await use(page)
    await context.close()
  },
  
  // Admin authenticated page
  adminPage: async ({ browser }, use) => {
    const context = await browser.newContext({
      storageState: 'playwright/.auth/admin.json',
    })
    const page = await context.newPage()
    await use(page)
    await context.close()
  },
})

export { expect }

// Re-export common types
export type { Page, BrowserContext }
