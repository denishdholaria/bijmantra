/**
 * Dashboard Page Object Model
 * 
 * Handles main dashboard interactions:
 * - Navigation menu
 * - Quick actions
 * - Statistics cards
 * - Recent activity
 */

import { Page, expect } from '@playwright/test'
import { BasePage } from './base.page'

export class DashboardPage extends BasePage {
  // Selectors
  private readonly sidebar = '[data-testid="sidebar"], nav[class*="sidebar"], aside'
  private readonly mainContent = 'main, [data-testid="main-content"], [role="main"]'
  private readonly statsCards = '[data-testid="stats-card"], .stats-card, [class*="stat-card"]'
  private readonly quickActions = '[data-testid="quick-actions"], .quick-actions'
  private readonly recentActivity = '[data-testid="recent-activity"], .recent-activity'
  private readonly userMenu = '[data-testid="user-menu"], [aria-label="User menu"], button:has([class*="avatar"])'
  private readonly searchInput = 'input[type="search"], input[placeholder*="Search" i], [data-testid="search"]'
  private readonly notificationBell = '[data-testid="notifications"], button[aria-label*="notification" i]'
  
  constructor(page: Page) {
    super(page)
  }
  
  /**
   * Navigate to dashboard
   */
  async navigate() {
    await this.goto('/dashboard')
    await this.waitForPageLoad()
  }
  
  /**
   * Verify dashboard is loaded
   */
  async verifyDashboardLoaded() {
    await expect(this.page.locator(this.mainContent).first()).toBeVisible()
    await this.waitForPageLoad()
  }
  
  /**
   * Get statistics card values
   */
  async getStatsCardValues(): Promise<Map<string, string>> {
    const cards = this.page.locator(this.statsCards)
    const count = await cards.count()
    const values = new Map<string, string>()
    
    for (let i = 0; i < count; i++) {
      const card = cards.nth(i)
      const title = await card.locator('h3, .title, [class*="title"]').first().textContent() || `card-${i}`
      const value = await card.locator('.value, [class*="value"], .text-2xl, .text-3xl').first().textContent() || ''
      values.set(title.trim(), value.trim())
    }
    
    return values
  }
  
  /**
   * Click sidebar navigation item
   */
  async clickSidebarItem(text: string) {
    const item = this.page.locator(`${this.sidebar} a:has-text("${text}"), ${this.sidebar} button:has-text("${text}")`).first()
    await item.click()
    await this.waitForNavigation()
  }
  
  /**
   * Expand sidebar section
   */
  async expandSidebarSection(sectionName: string) {
    const section = this.page.locator(`${this.sidebar} [data-testid="section-${sectionName}"], ${this.sidebar} button:has-text("${sectionName}")`).first()
    const isExpanded = await section.getAttribute('aria-expanded')
    
    if (isExpanded !== 'true') {
      await section.click()
    }
  }
  
  /**
   * Search using global search
   */
  async search(query: string) {
    const searchInput = this.page.locator(this.searchInput).first()
    await searchInput.fill(query)
    await this.page.keyboard.press('Enter')
    await this.waitForPageLoad()
  }
  
  /**
   * Open user menu
   */
  async openUserMenu() {
    await this.page.locator(this.userMenu).first().click()
  }
  
  /**
   * Logout via user menu
   */
  async logout() {
    await this.openUserMenu()
    await this.page.locator('button:has-text("Logout"), a:has-text("Logout"), [data-testid="logout"]').first().click()
    await this.page.waitForURL(/\/login/, { timeout: 10000 })
  }
  
  /**
   * Open notifications
   */
  async openNotifications() {
    await this.page.locator(this.notificationBell).first().click()
  }
  
  /**
   * Get notification count
   */
  async getNotificationCount(): Promise<number> {
    const badge = this.page.locator(`${this.notificationBell} .badge, ${this.notificationBell} [class*="badge"]`).first()
    if (await badge.isVisible({ timeout: 1000 }).catch(() => false)) {
      const text = await badge.textContent() || '0'
      return parseInt(text, 10) || 0
    }
    return 0
  }
  
  /**
   * Navigate to profile
   */
  async goToProfile() {
    await this.openUserMenu()
    await this.page.locator('a:has-text("Profile"), button:has-text("Profile"), [data-testid="profile"]').first().click()
    await this.waitForNavigation(/\/profile/)
  }
  
  /**
   * Navigate to settings
   */
  async goToSettings() {
    await this.openUserMenu()
    await this.page.locator('a:has-text("Settings"), button:has-text("Settings"), [data-testid="settings"]').first().click()
    await this.waitForNavigation(/\/settings/)
  }
  
  /**
   * Check if sidebar is collapsed
   */
  async isSidebarCollapsed(): Promise<boolean> {
    const sidebar = this.page.locator(this.sidebar).first()
    const width = await sidebar.evaluate(el => el.getBoundingClientRect().width)
    return width < 100 // Collapsed sidebar is typically narrow
  }
  
  /**
   * Toggle sidebar
   */
  async toggleSidebar() {
    const toggleButton = this.page.locator('[data-testid="sidebar-toggle"], button[aria-label*="sidebar" i]').first()
    if (await toggleButton.isVisible()) {
      await toggleButton.click()
    }
  }
  
  /**
   * Get quick action buttons
   */
  async getQuickActions(): Promise<string[]> {
    const actions = this.page.locator(`${this.quickActions} button, ${this.quickActions} a`)
    const count = await actions.count()
    const labels: string[] = []
    
    for (let i = 0; i < count; i++) {
      const text = await actions.nth(i).textContent()
      if (text) labels.push(text.trim())
    }
    
    return labels
  }
  
  /**
   * Click quick action
   */
  async clickQuickAction(actionText: string) {
    await this.page.locator(`${this.quickActions} button:has-text("${actionText}"), ${this.quickActions} a:has-text("${actionText}")`).first().click()
    await this.waitForNavigation()
  }
}
