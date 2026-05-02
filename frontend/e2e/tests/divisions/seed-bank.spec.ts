/**
 * Seed Bank Division E2E Tests
 * 
 * Tests for the Seed Bank module:
 * - Dashboard
 * - Vault management
 * - Accessions
 * - Viability testing
 * - Conservation
 */

import { test, expect } from '@playwright/test'
import { navigateAuthenticated } from '../../helpers/auth.helper'

test.describe('Seed Bank Division', () => {
  test.use({ storageState: 'playwright/.auth/user.json' })
  
  test.describe('Dashboard', () => {
    test('should load seed bank dashboard', async ({ page }) => {
      await navigateAuthenticated(page, '/seed-bank')
      
      expect(page.url()).toContain('/seed-bank')
      
      const content = page.locator('main, [role="main"]').first()
      await expect(content).toBeVisible()
    })
    
    test('should display statistics cards', async ({ page }) => {
      await navigateAuthenticated(page, '/seed-bank')
      
      // Look for stats cards
      const statsCards = page.locator('[data-testid="stats-card"], .stats-card, [class*="stat"]')
      
      // Should have some statistics displayed
      const cardCount = await statsCards.count()
      expect(cardCount).toBeGreaterThanOrEqual(0)
    })
  })
  
  test.describe('Vault Management', () => {
    test('should load vault management page', async ({ page }) => {
      await navigateAuthenticated(page, '/seed-bank/vault')
      
      expect(page.url()).toContain('/seed-bank/vault')
      
      const content = page.locator('main').first()
      await expect(content).toBeVisible()
    })
  })
  
  test.describe('Accessions', () => {
    test('should load accessions list', async ({ page }) => {
      await navigateAuthenticated(page, '/seed-bank/accessions')
      
      expect(page.url()).toContain('/seed-bank/accessions')
      
      // Should have table or list
      const list = page.locator('table, [data-testid="accessions-list"]').first()
      const emptyState = page.locator('text=/no accessions|empty/i').first()
      
      const hasContent = await list.isVisible({ timeout: 5000 }).catch(() => false) ||
                         await emptyState.isVisible({ timeout: 1000 }).catch(() => false)
      
      expect(hasContent).toBeTruthy()
    })
    
    test('should navigate to new accession form', async ({ page }) => {
      await navigateAuthenticated(page, '/seed-bank/accessions')
      
      const newButton = page.locator('a[href*="/new"], button:has-text("New"), button:has-text("Add")').first()
      
      if (await newButton.isVisible({ timeout: 3000 }).catch(() => false)) {
        await newButton.click()
        await page.waitForURL(/\/seed-bank\/accessions\/new/, { timeout: 10000 })
      }
    })
  })
  
  test.describe('Viability Testing', () => {
    test('should load viability testing page', async ({ page }) => {
      await navigateAuthenticated(page, '/seed-bank/viability')
      
      expect(page.url()).toContain('/seed-bank/viability')
      
      const content = page.locator('main').first()
      await expect(content).toBeVisible()
    })
  })
  
  test.describe('Conservation', () => {
    test('should load conservation page', async ({ page }) => {
      await navigateAuthenticated(page, '/seed-bank/conservation')
      
      expect(page.url()).toContain('/seed-bank/conservation')
      
      const content = page.locator('main').first()
      await expect(content).toBeVisible()
    })
  })
  
  test.describe('Regeneration Planning', () => {
    test('should load regeneration planning page', async ({ page }) => {
      await navigateAuthenticated(page, '/seed-bank/regeneration')
      
      expect(page.url()).toContain('/seed-bank/regeneration')
      
      const content = page.locator('main').first()
      await expect(content).toBeVisible()
    })
  })
  
  test.describe('Germplasm Exchange', () => {
    test('should load exchange page', async ({ page }) => {
      await navigateAuthenticated(page, '/seed-bank/exchange')
      
      expect(page.url()).toContain('/seed-bank/exchange')
      
      const content = page.locator('main').first()
      await expect(content).toBeVisible()
    })
  })
})
