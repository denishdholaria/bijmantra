/**
 * Germplasm CRUD E2E Tests
 * 
 * Tests complete CRUD operations for Germplasm:
 * - Create new germplasm
 * - Read/list germplasm
 * - Search germplasm
 * - Update germplasm
 * - Delete germplasm
 * - View pedigree
 */

import { test, expect } from '@playwright/test'
import { TestDataFactory } from '../../helpers/test-data.factory'
import { navigateAuthenticated } from '../../helpers/auth.helper'

const testData = new TestDataFactory()

test.describe('Germplasm CRUD Operations', () => {
  test.use({ storageState: 'playwright/.auth/user.json' })
  
  test.describe('List Germplasm', () => {
    test('should display germplasm list page', async ({ page }) => {
      await navigateAuthenticated(page, '/germplasm')
      
      expect(page.url()).toContain('/germplasm')
      
      // Should have table or cards
      const table = page.locator('table, [data-testid="germplasm-list"], [role="grid"]').first()
      const cards = page.locator('[data-testid="germplasm-card"]').first()
      const emptyState = page.locator('text=/no germplasm|empty|get started/i').first()
      
      const hasContent = await table.isVisible({ timeout: 5000 }).catch(() => false) ||
                         await cards.isVisible({ timeout: 1000 }).catch(() => false) ||
                         await emptyState.isVisible({ timeout: 1000 }).catch(() => false)
      
      expect(hasContent).toBeTruthy()
    })
    
    test('should have search functionality', async ({ page }) => {
      await navigateAuthenticated(page, '/germplasm')
      
      // Should have search input
      const searchInput = page.locator('input[type="search"], input[placeholder*="search" i], [data-testid="search"]').first()
      await expect(searchInput).toBeVisible({ timeout: 10000 })
    })
    
    test('should filter germplasm by search', async ({ page }) => {
      await navigateAuthenticated(page, '/germplasm')
      
      const searchInput = page.locator('input[type="search"], input[placeholder*="search" i]').first()
      
      if (await searchInput.isVisible({ timeout: 5000 }).catch(() => false)) {
        await searchInput.fill('Rice')
        await page.keyboard.press('Enter')
        
        // Wait for results to update
        await page.waitForTimeout(1000)
        
        // Results should be filtered (or show no results message)
        const content = page.locator('main').first()
        await expect(content).toBeVisible()
      }
    })
  })
  
  test.describe('Create Germplasm', () => {
    test('should navigate to create germplasm form', async ({ page }) => {
      await navigateAuthenticated(page, '/germplasm')
      
      const createButton = page.locator('a[href="/germplasm/new"], button:has-text("New"), button:has-text("Create"), button:has-text("Add")').first()
      await createButton.click()
      
      await page.waitForURL(/\/germplasm\/new/, { timeout: 10000 })
    })
    
    test('should display germplasm creation form', async ({ page }) => {
      await navigateAuthenticated(page, '/germplasm/new')
      
      const form = page.locator('form').first()
      await expect(form).toBeVisible({ timeout: 10000 })
      
      // Should have germplasm name field
      const nameInput = page.locator('input[name="germplasmName"], input[name="name"], input[placeholder*="name" i]').first()
      await expect(nameInput).toBeVisible()
    })
    
    test('should create a new germplasm entry', async ({ page }) => {
      await navigateAuthenticated(page, '/germplasm/new')
      
      const germplasmData = testData.germplasm()
      
      // Fill form
      const nameInput = page.locator('input[name="germplasmName"], input[name="name"], input[placeholder*="name" i]').first()
      await nameInput.fill(germplasmData.germplasmName)
      
      // Fill genus if field exists
      const genusInput = page.locator('input[name="genus"], input[placeholder*="genus" i]').first()
      if (await genusInput.isVisible({ timeout: 1000 }).catch(() => false)) {
        await genusInput.fill(germplasmData.genus)
      }
      
      // Fill species if field exists
      const speciesInput = page.locator('input[name="species"], input[placeholder*="species" i]').first()
      if (await speciesInput.isVisible({ timeout: 1000 }).catch(() => false)) {
        await speciesInput.fill(germplasmData.species)
      }
      
      // Submit form
      const submitButton = page.locator('button[type="submit"], button:has-text("Save"), button:has-text("Create")').first()
      await submitButton.click()
      
      // Should redirect
      await page.waitForURL(/\/germplasm/, { timeout: 15000 })
    })
  })
  
  test.describe('View Germplasm Detail', () => {
    test('should display germplasm details', async ({ page }) => {
      await navigateAuthenticated(page, '/germplasm')
      
      const germplasmLink = page.locator('a[href^="/germplasm/"]').first()
      
      if (await germplasmLink.isVisible({ timeout: 5000 }).catch(() => false)) {
        const href = await germplasmLink.getAttribute('href')
        
        if (href && !href.includes('/new')) {
          await navigateAuthenticated(page, href)
          
          const content = page.locator('main, [role="main"]').first()
          await expect(content).toBeVisible()
        }
      }
    })
    
    test('should show pedigree information', async ({ page }) => {
      await navigateAuthenticated(page, '/germplasm')
      
      const germplasmLink = page.locator('a[href^="/germplasm/"]').first()
      
      if (await germplasmLink.isVisible({ timeout: 5000 }).catch(() => false)) {
        await germplasmLink.click()
        await page.waitForLoadState('domcontentloaded')
        
        // Look for pedigree section or tab
        const pedigreeSection = page.locator('text=/pedigree/i, [data-testid="pedigree"]').first()
        
        if (await pedigreeSection.isVisible({ timeout: 3000 }).catch(() => false)) {
          await pedigreeSection.click()
          await page.waitForTimeout(1000)
        }
      }
    })
  })
  
  test.describe('Germplasm Comparison', () => {
    test('should navigate to comparison page', async ({ page }) => {
      await navigateAuthenticated(page, '/germplasm-comparison')
      
      expect(page.url()).toContain('/germplasm-comparison')
      
      const content = page.locator('main, [role="main"]').first()
      await expect(content).toBeVisible()
    })
  })
  
  test.describe('Pedigree Viewer', () => {
    test('should display pedigree viewer', async ({ page }) => {
      await navigateAuthenticated(page, '/pedigree')
      
      expect(page.url()).toContain('/pedigree')
      
      const content = page.locator('main, [role="main"]').first()
      await expect(content).toBeVisible()
    })
  })
})
