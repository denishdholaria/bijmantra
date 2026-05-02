/**
 * Login Page Object Model
 * 
 * Handles authentication flows:
 * - Standard login
 * - Demo mode login
 * - Error handling
 * - Password visibility toggle
 */

import { Page, expect } from '@playwright/test'
import { BasePage } from './base.page'

export class LoginPage extends BasePage {
  // Selectors
  private readonly emailInput = 'input[type="email"], input[name="email"], input[placeholder*="email" i]'
  private readonly passwordInput = 'input[type="password"]'
  private readonly submitButton = 'button[type="submit"], button:has-text("Login"), button:has-text("Sign in")'
  private readonly errorAlert = '[role="alert"], .text-red-, [data-testid="login-error"]'
  private readonly forgotPasswordLink = 'a:has-text("Forgot"), a:has-text("Reset")'
  private readonly registerLink = 'a:has-text("Register"), a:has-text("Sign up")'
  private readonly passwordToggle = 'button[aria-label*="password"], [data-testid="password-toggle"]'
  private readonly rememberMeCheckbox = 'input[type="checkbox"][name*="remember"], [data-testid="remember-me"]'
  
  constructor(page: Page) {
    super(page)
  }
  
  /**
   * Navigate to login page
   */
  async navigate() {
    await this.goto('/login')
    await this.page.waitForSelector(this.emailInput, { timeout: 10000 })
  }
  
  /**
   * Fill email field
   */
  async fillEmail(email: string) {
    await this.page.locator(this.emailInput).first().fill(email)
  }
  
  /**
   * Fill password field
   */
  async fillPassword(password: string) {
    await this.page.locator(this.passwordInput).first().fill(password)
  }
  
  /**
   * Click submit button
   */
  async submit() {
    await this.page.locator(this.submitButton).first().click()
  }
  
  /**
   * Perform complete login
   */
  async login(email: string, password: string) {
    await this.fillEmail(email)
    await this.fillPassword(password)
    await this.submit()
  }
  
  /**
   * Login and wait for redirect
   */
  async loginAndWaitForRedirect(email: string, password: string, expectedUrl?: string | RegExp) {
    await this.login(email, password)
    
    const urlPattern = expectedUrl || /\/(dashboard|gateway)/
    await this.page.waitForURL(urlPattern, { timeout: 15000 })
    await this.waitForPageLoad()
  }
  
  /**
   * Login with demo credentials
   * Uses environment variables with fallbacks for flexibility
   */
  async loginAsDemo() {
    const email = process.env.E2E_TEST_EMAIL || 'demo@bijmantra.org'
    const password = process.env.E2E_TEST_PASSWORD || 'Demo123!'
    await this.loginAndWaitForRedirect(email, password)
  }
  
  /**
   * Login with admin credentials
   * Uses environment variables with fallbacks for flexibility
   */
  async loginAsAdmin() {
    const email = process.env.E2E_ADMIN_EMAIL || 'admin@bijmantra.org'
    const password = process.env.E2E_ADMIN_PASSWORD || 'Admin123!'
    await this.loginAndWaitForRedirect(email, password)
  }
  
  /**
   * Check if login error is displayed
   */
  async hasLoginError(): Promise<boolean> {
    return this.page.locator(this.errorAlert).isVisible({ timeout: 3000 }).catch(() => false)
  }
  
  /**
   * Get login error message
   */
  async getLoginError(): Promise<string> {
    const error = this.page.locator(this.errorAlert).first()
    if (await error.isVisible({ timeout: 3000 }).catch(() => false)) {
      return error.textContent() || ''
    }
    return ''
  }
  
  /**
   * Toggle password visibility
   */
  async togglePasswordVisibility() {
    const toggle = this.page.locator(this.passwordToggle).first()
    if (await toggle.isVisible()) {
      await toggle.click()
    }
  }
  
  /**
   * Check if password is visible
   */
  async isPasswordVisible(): Promise<boolean> {
    const input = this.page.locator(this.passwordInput).first()
    const type = await input.getAttribute('type')
    return type === 'text'
  }
  
  /**
   * Toggle remember me checkbox
   */
  async toggleRememberMe() {
    const checkbox = this.page.locator(this.rememberMeCheckbox).first()
    if (await checkbox.isVisible()) {
      await checkbox.click()
    }
  }
  
  /**
   * Click forgot password link
   */
  async clickForgotPassword() {
    await this.page.locator(this.forgotPasswordLink).first().click()
  }
  
  /**
   * Click register link
   */
  async clickRegister() {
    await this.page.locator(this.registerLink).first().click()
  }
  
  /**
   * Verify login page is displayed
   */
  async verifyLoginPage() {
    await expect(this.page.locator(this.emailInput).first()).toBeVisible()
    await expect(this.page.locator(this.passwordInput).first()).toBeVisible()
    await expect(this.page.locator(this.submitButton).first()).toBeVisible()
  }
  
  /**
   * Verify successful login redirect
   */
  async verifySuccessfulLogin() {
    // Should be redirected away from login page
    await expect(this.page).not.toHaveURL(/\/login/)
    
    // Should have auth token in localStorage
    const token = await this.page.evaluate(() => localStorage.getItem('auth_token'))
    expect(token).toBeTruthy()
  }
}
