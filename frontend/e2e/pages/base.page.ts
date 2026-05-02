/**
 * Base Page Object Model
 * 
 * Foundation for all page objects with common functionality:
 * - Navigation
 * - Waiting strategies
 * - Common element interactions
 * - Error handling
 */

import { Page, Locator, expect } from '@playwright/test'

export abstract class BasePage {
  readonly page: Page
  
  // Common selectors
  protected readonly loadingSpinner = '[data-testid="loading"], .animate-spin, [class*="loading"]'
  protected readonly toastNotification = '[data-testid="toast"], [role="alert"], .sonner-toast'
  protected readonly errorMessage = '[data-testid="error"], [role="alert"][class*="error"], .text-red-'
  protected readonly successMessage = '[data-testid="success"], [role="alert"][class*="success"], .text-green-'
  
  constructor(page: Page) {
    this.page = page
  }
  
  /**
   * Navigate to a specific path
   */
  async goto(path: string = '') {
    const url = path.startsWith('/') ? path : `/${path}`
    await this.page.goto(url, { waitUntil: 'domcontentloaded' })
    await this.waitForPageLoad()
  }
  
  /**
   * Wait for page to fully load
   */
  async waitForPageLoad() {
    // Wait for any loading spinners to disappear
    const spinner = this.page.locator(this.loadingSpinner).first()
    if (await spinner.isVisible({ timeout: 1000 }).catch(() => false)) {
      await spinner.waitFor({ state: 'hidden', timeout: 30000 })
    }
    
    // Wait for network to be idle
    await this.page.waitForLoadState('networkidle', { timeout: 30000 }).catch(() => {
      // Network may not become fully idle, continue anyway
    })
  }
  
  /**
   * Wait for navigation to complete
   */
  async waitForNavigation(urlPattern?: string | RegExp) {
    if (urlPattern) {
      await this.page.waitForURL(urlPattern, { timeout: 15000 })
    }
    await this.waitForPageLoad()
  }
  
  /**
   * Get page title
   */
  async getTitle(): Promise<string> {
    return this.page.title()
  }
  
  /**
   * Get current URL
   */
  getCurrentUrl(): string {
    return this.page.url()
  }
  
  /**
   * Check if element is visible
   */
  async isVisible(selector: string): Promise<boolean> {
    return this.page.locator(selector).isVisible()
  }
  
  /**
   * Click element with retry
   */
  async clickWithRetry(selector: string, options?: { timeout?: number; retries?: number }) {
    const { timeout = 10000, retries = 3 } = options || {}
    let lastError: Error | null = null
    
    for (let i = 0; i < retries; i++) {
      try {
        await this.page.locator(selector).click({ timeout })
        return
      } catch (error) {
        lastError = error as Error
        await this.page.waitForTimeout(500)
      }
    }
    
    throw lastError
  }
  
  /**
   * Fill input with clear
   */
  async fillInput(selector: string, value: string) {
    const input = this.page.locator(selector)
    await input.clear()
    await input.fill(value)
  }
  
  /**
   * Select option from dropdown
   */
  async selectOption(selector: string, value: string) {
    await this.page.locator(selector).selectOption(value)
  }
  
  /**
   * Wait for toast notification
   */
  async waitForToast(type?: 'success' | 'error' | 'info'): Promise<string> {
    const toast = this.page.locator(this.toastNotification).first()
    await toast.waitFor({ state: 'visible', timeout: 10000 })
    return toast.textContent() || ''
  }
  
  /**
   * Dismiss toast notification
   */
  async dismissToast() {
    const closeButton = this.page.locator(`${this.toastNotification} button[aria-label="Close"], ${this.toastNotification} [data-dismiss]`).first()
    if (await closeButton.isVisible({ timeout: 1000 }).catch(() => false)) {
      await closeButton.click()
    }
  }
  
  /**
   * Check for error message
   */
  async hasError(): Promise<boolean> {
    return this.page.locator(this.errorMessage).isVisible({ timeout: 1000 }).catch(() => false)
  }
  
  /**
   * Get error message text
   */
  async getErrorMessage(): Promise<string> {
    const error = this.page.locator(this.errorMessage).first()
    if (await error.isVisible({ timeout: 1000 }).catch(() => false)) {
      return error.textContent() || ''
    }
    return ''
  }
  
  /**
   * Take screenshot
   */
  async screenshot(name: string) {
    await this.page.screenshot({ path: `test-results/screenshots/${name}.png`, fullPage: true })
  }
  
  /**
   * Scroll to element
   */
  async scrollTo(selector: string) {
    await this.page.locator(selector).scrollIntoViewIfNeeded()
  }
  
  /**
   * Wait for element to be stable (no animations)
   */
  async waitForStable(selector: string) {
    const element = this.page.locator(selector)
    await element.waitFor({ state: 'visible' })
    
    // Wait for any CSS animations to complete
    await this.page.waitForFunction(
      (sel) => {
        const el = document.querySelector(sel)
        if (!el) return true
        const animations = el.getAnimations()
        return animations.length === 0 || animations.every(a => a.playState === 'finished')
      },
      selector,
      { timeout: 5000 }
    ).catch(() => {
      // Animation check failed, continue anyway
    })
  }
  
  /**
   * Get table data
   */
  async getTableData(tableSelector: string): Promise<string[][]> {
    const rows = this.page.locator(`${tableSelector} tbody tr`)
    const count = await rows.count()
    const data: string[][] = []
    
    for (let i = 0; i < count; i++) {
      const cells = rows.nth(i).locator('td')
      const cellCount = await cells.count()
      const rowData: string[] = []
      
      for (let j = 0; j < cellCount; j++) {
        rowData.push(await cells.nth(j).textContent() || '')
      }
      
      data.push(rowData)
    }
    
    return data
  }
  
  /**
   * Check accessibility
   */
  async checkAccessibility() {
    // This will be implemented with axe-core in accessibility tests
    return true
  }
}
