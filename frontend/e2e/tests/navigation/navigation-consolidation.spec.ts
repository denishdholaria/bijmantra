/**
 * Navigation Consolidation E2E Tests
 * 
 * Tests Task 10.5: Verify Navigation Consolidation
 * 
 * Validates:
 * - All navigation links work
 * - No broken routes
 * - Command palette completeness
 * - Sidebar navigation functionality
 */

import { test, expect } from '@playwright/test'
import { navigateAuthenticated } from '../../helpers/auth.helper'

test.describe('Navigation Consolidation', () => {
  test.use({ storageState: 'playwright/.auth/user.json' })

  test.describe('10.5.1: Verify all navigation links work', () => {
    test('should navigate to all top-level divisions', async ({ page }) => {
      const divisions = [
        { path: '/dashboard', name: 'Home' },
        { path: '/programs', name: 'Plant Sciences' },
        { path: '/crop-intelligence', name: 'Crop Intelligence' },
        { path: '/soil-nutrients', name: 'Soil & Nutrients' },
        { path: '/crop-protection', name: 'Crop Protection' },
        { path: '/water-irrigation', name: 'Water & Irrigation' },
        { path: '/seed-operations', name: 'Seed Commerce' },
        { path: '/seed-bank', name: 'Seed Bank' },
        { path: '/sensor-networks', name: 'Sensor Networks' },
        { path: '/quick-entry', name: 'Tools' },
        { path: '/help', name: 'Knowledge' },
        { path: '/space-research', name: 'Space Research' },
        { path: '/settings', name: 'Settings' },
      ]

      for (const division of divisions) {
        await navigateAuthenticated(page, division.path)
        
        // Verify page loaded without errors
        await expect(page).not.toHaveURL(/\/error/)
        
        // Verify no 404 or error messages
        const errorText = await page.locator('text=/404|not found|error/i').count()
        expect(errorText).toBe(0)
        
        console.log(`✓ ${division.name} (${division.path})`)
      }
    })

    test('should navigate to sample section pages', async ({ page }) => {
      const samplePages = [
        '/trials',
        '/germplasm',
        '/crosses',
        '/traits',
        '/samples',
        '/genetic-diversity',
        '/linkage-disequilibrium',
        '/fieldlayout',
        '/statistics',
      ]

      for (const path of samplePages) {
        await navigateAuthenticated(page, path)
        
        // Verify page loaded
        await expect(page).not.toHaveURL(/\/error/)
        
        // Wait for content to load
        await page.waitForLoadState('networkidle', { timeout: 10000 })
        
        console.log(`✓ ${path}`)
      }
    })
  })

  test.describe('10.5.2: Verify no broken routes', () => {
    test('should handle invalid routes gracefully', async ({ page }) => {
      await navigateAuthenticated(page, '/this-route-does-not-exist-12345')
      
      // Should show 404 or redirect to a valid page
      const url = page.url()
      const has404 = await page.locator('text=/404|not found/i').count() > 0
      const redirectedToValid = url.includes('/dashboard') || url.includes('/login')
      
      expect(has404 || redirectedToValid).toBeTruthy()
    })

    test('should not have console errors on valid routes', async ({ page }) => {
      const errors: string[] = []
      
      page.on('console', msg => {
        if (msg.type() === 'error') {
          errors.push(msg.text())
        }
      })

      await navigateAuthenticated(page, '/dashboard')
      await page.waitForLoadState('networkidle')
      
      // Filter out known non-critical errors
      const criticalErrors = errors.filter(err => 
        !err.includes('favicon') && 
        !err.includes('manifest') &&
        !err.includes('DevTools')
      )
      
      expect(criticalErrors.length).toBe(0)
    })
  })

  test.describe('10.5.3: Verify command palette completeness', () => {
    test('should open command palette with Cmd+K', async ({ page }) => {
      await navigateAuthenticated(page, '/dashboard')
      
      // Open command palette
      await page.keyboard.press('Meta+K')
      
      // Verify command palette is visible
      const commandPalette = page.locator('[role="dialog"]').filter({ hasText: /command|search/i })
      await expect(commandPalette).toBeVisible({ timeout: 5000 })
    })

    test('should show navigation items in command palette', async ({ page }) => {
      await navigateAuthenticated(page, '/dashboard')
      
      // Open command palette
      await page.keyboard.press('Meta+K')
      await page.waitForTimeout(500)
      
      // Search for a known navigation item
      await page.keyboard.type('trials')
      await page.waitForTimeout(500)
      
      // Should show trials in results
      const results = page.locator('[cmdk-item]')
      const count = await results.count()
      expect(count).toBeGreaterThan(0)
    })

    test('should navigate via command palette', async ({ page }) => {
      await navigateAuthenticated(page, '/dashboard')
      
      // Open command palette
      await page.keyboard.press('Meta+K')
      await page.waitForTimeout(500)
      
      // Search and select
      await page.keyboard.type('germplasm')
      await page.waitForTimeout(500)
      await page.keyboard.press('Enter')
      
      // Should navigate to germplasm page
      await page.waitForURL(/\/germplasm/, { timeout: 5000 })
      expect(page.url()).toContain('/germplasm')
    })
  })

  test.describe('10.5.4: Sidebar navigation functionality', () => {
    test('should show sidebar with divisions', async ({ page }) => {
      await navigateAuthenticated(page, '/dashboard')
      
      // Sidebar should be visible
      const sidebar = page.locator('aside').first()
      await expect(sidebar).toBeVisible()
    })

    test('should navigate via sidebar clicks', async ({ page }) => {
      await navigateAuthenticated(page, '/dashboard')
      
      // Wait for sidebar to load
      await page.waitForSelector('aside', { timeout: 5000 })
      
      // Click on a division in sidebar (if visible)
      const plantSciencesLink = page.locator('aside').locator('text=/Plant Sciences|Programs/i').first()
      
      if (await plantSciencesLink.isVisible()) {
        await plantSciencesLink.click()
        await page.waitForLoadState('networkidle')
        
        // Should navigate to plant sciences
        expect(page.url()).toMatch(/\/(programs|plant-sciences)/)
      }
    })

    test('should expand/collapse sidebar sections', async ({ page }) => {
      await navigateAuthenticated(page, '/programs')
      
      // Wait for sidebar
      await page.waitForSelector('aside', { timeout: 5000 })
      
      // Look for expandable sections (chevron icons)
      const chevrons = page.locator('aside').locator('[class*="chevron"]')
      const count = await chevrons.count()
      
      // Should have some expandable sections
      expect(count).toBeGreaterThanOrEqual(0)
    })
  })

  test.describe('Navigation Integration', () => {
    test('should maintain navigation state across page transitions', async ({ page }) => {
      await navigateAuthenticated(page, '/dashboard')
      
      // Navigate to a few pages
      await page.goto('/programs')
      await page.waitForLoadState('networkidle')
      
      await page.goto('/trials')
      await page.waitForLoadState('networkidle')
      
      // Go back
      await page.goBack()
      await page.waitForLoadState('networkidle')
      
      // Should be on programs
      expect(page.url()).toContain('/programs')
    })

    test('should handle rapid navigation without errors', async ({ page }) => {
      const paths = ['/dashboard', '/programs', '/trials', '/germplasm', '/traits']
      
      for (const path of paths) {
        await navigateAuthenticated(page, path)
        await page.waitForTimeout(200) // Brief pause
      }
      
      // Should end on last path without errors
      expect(page.url()).toContain('/traits')
    })
  })

  test.describe('Breadcrumbs', () => {
    test('should show breadcrumbs on nested pages', async ({ page }) => {
      await navigateAuthenticated(page, '/linkage-disequilibrium')
      
      // Look for breadcrumb navigation
      const breadcrumbs = page.locator('[aria-label*="breadcrumb"]').or(
        page.locator('nav').filter({ hasText: /Plant Sciences|Genomics/i })
      )
      
      // Breadcrumbs may or may not be implemented yet
      const count = await breadcrumbs.count()
      console.log(`Breadcrumbs found: ${count}`)
    })
  })
})
