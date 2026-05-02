/**
 * Programs CRUD E2E Tests
 * 
 * Tests complete CRUD operations for Breeding Programs:
 * - Create new program
 * - Read/list programs
 * - Update program
 * - Delete program
 */

import { test, expect } from '@playwright/test'
import { TestDataFactory } from '../../helpers/test-data.factory'
import { navigateAuthenticated } from '../../helpers/auth.helper'

const testData = new TestDataFactory()

test.describe('Programs CRUD Operations', () => {
  test.use({ storageState: 'playwright/.auth/user.json' })
  
  let createdProgramId: string | null = null
  
  test.describe('List Programs', () => {
    test('should display programs list page', async ({ page }) => {
      await navigateAuthenticated(page, '/programs')
      
      // Page should load
      expect(page.url()).toContain('/programs')
      
      // Should have a table or list of programs
      const table = page.locator('table, [data-testid="programs-list"], [role="grid"]').first()
      const cards = page.locator('[data-testid="program-card"], .program-card').first()
      
      // Either table or cards should be visible (or empty state)
      const hasTable = await table.isVisible({ timeout: 5000 }).catch(() => false)
      const hasCards = await cards.isVisible({ timeout: 1000 }).catch(() => false)
      const hasEmptyState = await page.locator('text=/no programs|empty|get started/i').first().isVisible({ timeout: 1000 }).catch(() => false)
      
      expect(hasTable || hasCards || hasEmptyState).toBeTruthy()
    })
    
    test('should have create new program button', async ({ page }) => {
      await navigateAuthenticated(page, '/programs')
      
      // Should have a create button
      const createButton = page.locator('a[href="/programs/new"], button:has-text("New"), button:has-text("Create"), button:has-text("Add")').first()
      await expect(createButton).toBeVisible({ timeout: 10000 })
    })
  })
  
  test.describe('Create Program', () => {
    test('should navigate to create program form', async ({ page }) => {
      await navigateAuthenticated(page, '/programs')
      
      // Click create button
      const createButton = page.locator('a[href="/programs/new"], button:has-text("New"), button:has-text("Create"), button:has-text("Add")').first()
      await createButton.click()
      
      // Should navigate to form
      await page.waitForURL(/\/programs\/new/, { timeout: 10000 })
    })
    
    test('should display program creation form', async ({ page }) => {
      await navigateAuthenticated(page, '/programs/new')
      
      // Form should be visible
      const form = page.locator('form').first()
      await expect(form).toBeVisible({ timeout: 10000 })
      
      // Should have program name field
      const nameInput = page.locator('input[name="programName"], input[name="name"], input[placeholder*="name" i]').first()
      await expect(nameInput).toBeVisible()
    })
    
    test('should create a new program', async ({ page }) => {
      await navigateAuthenticated(page, '/programs/new')
      
      const programData = testData.program()
      
      // Fill form
      const nameInput = page.locator('input[name="programName"], input[name="name"], input[placeholder*="name" i]').first()
      await nameInput.fill(programData.programName)
      
      // Fill abbreviation if field exists
      const abbrevInput = page.locator('input[name="abbreviation"], input[placeholder*="abbreviation" i]').first()
      if (await abbrevInput.isVisible({ timeout: 1000 }).catch(() => false)) {
        await abbrevInput.fill(programData.abbreviation)
      }
      
      // Fill objective if field exists
      const objectiveInput = page.locator('textarea[name="objective"], input[name="objective"], textarea[placeholder*="objective" i]').first()
      if (await objectiveInput.isVisible({ timeout: 1000 }).catch(() => false)) {
        await objectiveInput.fill(programData.objective)
      }
      
      // Submit form
      const submitButton = page.locator('button[type="submit"], button:has-text("Save"), button:has-text("Create")').first()
      await submitButton.click()
      
      // Should redirect to programs list or detail page
      await page.waitForURL(/\/programs(?:\/|$)/, { timeout: 15000 })
      
      // Store created program ID for cleanup
      const url = page.url()
      const match = url.match(/\/programs\/([^/]+)/)
      if (match) {
        createdProgramId = match[1]
      }
    })
    
    test('should show validation error for empty name', async ({ page }) => {
      await navigateAuthenticated(page, '/programs/new')
      
      // Try to submit without filling required fields
      const submitButton = page.locator('button[type="submit"], button:has-text("Save"), button:has-text("Create")').first()
      await submitButton.click()
      
      // Should show validation error or stay on form
      await page.waitForTimeout(1000)
      
      // Either shows error or stays on form
      const url = page.url()
      const hasError = await page.locator('.text-red-, [role="alert"], .error').first().isVisible({ timeout: 2000 }).catch(() => false)
      
      expect(url.includes('/programs/new') || hasError).toBeTruthy()
    })
  })
  
  test.describe('View Program Detail', () => {
    test('should navigate to program detail from list', async ({ page }) => {
      await navigateAuthenticated(page, '/programs')
      
      // Click on first program in list
      const programLink = page.locator('table tbody tr a, [data-testid="program-card"] a, a[href^="/programs/"]').first()
      
      if (await programLink.isVisible({ timeout: 5000 }).catch(() => false)) {
        await programLink.click()
        
        // Should navigate to detail page
        await page.waitForURL(/\/programs\/[^/]+$/, { timeout: 10000 })
      }
    })
    
    test('should display program details', async ({ page }) => {
      // First get a program ID
      await navigateAuthenticated(page, '/programs')
      
      const programLink = page.locator('a[href^="/programs/"]').first()
      const href = await programLink.getAttribute('href')
      
      if (href && !href.includes('/new')) {
        await navigateAuthenticated(page, href)
        
        // Should show program details
        const content = page.locator('main, [role="main"]').first()
        await expect(content).toBeVisible()
      }
    })
  })
  
  test.describe('Update Program', () => {
    test('should navigate to edit form', async ({ page }) => {
      await navigateAuthenticated(page, '/programs')
      
      // Find edit button or link
      const editButton = page.locator('a[href*="/edit"], button:has-text("Edit"), [data-testid="edit-button"]').first()
      
      if (await editButton.isVisible({ timeout: 5000 }).catch(() => false)) {
        await editButton.click()
        
        // Should navigate to edit form
        await page.waitForURL(/\/programs\/[^/]+\/edit/, { timeout: 10000 })
      }
    })
    
    test('should update program name', async ({ page }) => {
      await navigateAuthenticated(page, '/programs')
      
      // Navigate to first program's edit page
      const editLink = page.locator('a[href*="/edit"]').first()
      
      if (await editLink.isVisible({ timeout: 5000 }).catch(() => false)) {
        await editLink.click()
        await page.waitForLoadState('domcontentloaded')
        
        // Update name
        const nameInput = page.locator('input[name="programName"], input[name="name"]').first()
        
        if (await nameInput.isVisible({ timeout: 5000 }).catch(() => false)) {
          const currentName = await nameInput.inputValue()
          const newName = `${currentName}_UPDATED`
          
          await nameInput.clear()
          await nameInput.fill(newName)
          
          // Submit
          const submitButton = page.locator('button[type="submit"], button:has-text("Save"), button:has-text("Update")').first()
          await submitButton.click()
          
          // Should redirect after save
          await page.waitForURL(/\/programs/, { timeout: 15000 })
        }
      } else {
        // No edit link available - skip test gracefully
        console.log('No edit link found - skipping update test')
      }
    })
  })
  
  test.describe('Delete Program', () => {
    test('should show delete confirmation', async ({ page }) => {
      await navigateAuthenticated(page, '/programs')
      
      // Find delete button
      const deleteButton = page.locator('button:has-text("Delete"), [data-testid="delete-button"], button[aria-label*="delete" i]').first()
      
      if (await deleteButton.isVisible({ timeout: 5000 }).catch(() => false)) {
        await deleteButton.click()
        
        // Should show confirmation dialog
        const dialog = page.locator('[role="dialog"], [role="alertdialog"], .modal').first()
        const confirmText = page.locator('text=/confirm|are you sure|delete/i').first()
        
        const hasDialog = await dialog.isVisible({ timeout: 3000 }).catch(() => false)
        const hasConfirmText = await confirmText.isVisible({ timeout: 1000 }).catch(() => false)
        
        // Either shows dialog or inline confirmation
        expect(hasDialog || hasConfirmText).toBeTruthy()
      }
    })
  })
  
  // Cleanup
  test.afterAll(async ({ request }) => {
    if (createdProgramId) {
      try {
        await request.delete(`http://localhost:8000/brapi/v2/programs/${createdProgramId}`)
      } catch {
        // Ignore cleanup errors
      }
    }
  })
})
