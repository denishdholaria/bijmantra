/**
 * Visual Regression Tests
 * 
 * Captures and compares screenshots to detect unintended visual changes:
 * - Layout consistency
 * - Component rendering
 * - Responsive design
 * - Theme consistency
 */

import { test, expect } from '@playwright/test'

test.describe('Visual Regression Tests', () => {
  test.use({ storageState: 'playwright/.auth/user.json' })
  
  // Pages to capture for visual regression
  const visualTestPages = [
    { name: 'login', path: '/login', requiresAuth: false },
    { name: 'dashboard', path: '/dashboard', requiresAuth: true },
    { name: 'programs', path: '/programs', requiresAuth: true },
    { name: 'germplasm', path: '/germplasm', requiresAuth: true },
    { name: 'trials', path: '/trials', requiresAuth: true },
    { name: 'locations', path: '/locations', requiresAuth: true },
    { name: 'traits', path: '/traits', requiresAuth: true },
    { name: 'seed-bank', path: '/seed-bank', requiresAuth: true },
    { name: 'seed-operations', path: '/seed-operations', requiresAuth: true },
    { name: 'settings', path: '/settings', requiresAuth: true },
  ]
  
  test.describe('Full Page Screenshots', () => {
    for (const pageInfo of visualTestPages) {
      test(`should match visual snapshot for ${pageInfo.name}`, async ({ page }) => {
        await page.goto(pageInfo.path)
        await page.waitForLoadState('networkidle')
        
        // Wait for animations to complete
        await page.waitForTimeout(1000)
        
        // Hide dynamic content that changes between runs
        await page.evaluate(() => {
          // Hide timestamps
          document.querySelectorAll('[data-testid="timestamp"], .timestamp, time').forEach(el => {
            (el as HTMLElement).style.visibility = 'hidden'
          })
          
          // Hide avatars (may have random colors)
          document.querySelectorAll('[data-testid="avatar"], .avatar').forEach(el => {
            (el as HTMLElement).style.visibility = 'hidden'
          })
          
          // Hide loading spinners
          document.querySelectorAll('.animate-spin, [data-testid="loading"]').forEach(el => {
            (el as HTMLElement).style.display = 'none'
          })
        })
        
        // Take screenshot - dashboard has dynamic content so allow more diff
        const maxDiff = pageInfo.name === 'dashboard' ? 5000 : 500
        await expect(page).toHaveScreenshot(`${pageInfo.name}.png`, {
          fullPage: true,
          maxDiffPixels: maxDiff,
          threshold: 0.3,
        })
      })
    }
  })
  
  test.describe('Component Screenshots', () => {
    test('should match sidebar visual snapshot', async ({ page }) => {
      await page.goto('/dashboard')
      await page.waitForLoadState('networkidle')
      
      const sidebar = page.locator('nav, aside, [data-testid="sidebar"]').first()
      
      if (await sidebar.isVisible()) {
        await expect(sidebar).toHaveScreenshot('sidebar.png', {
          maxDiffPixels: 200,
        })
      }
    })
    
    test('should match header visual snapshot', async ({ page }) => {
      await page.goto('/dashboard')
      await page.waitForLoadState('networkidle')
      
      const header = page.locator('header, [data-testid="header"]').first()
      
      if (await header.isVisible()) {
        await expect(header).toHaveScreenshot('header.png', {
          maxDiffPixels: 200,
        })
      }
    })
    
    test('should match data table visual snapshot', async ({ page }) => {
      await page.goto('/programs')
      await page.waitForLoadState('networkidle')
      
      const table = page.locator('table, [role="grid"]').first()
      
      if (await table.isVisible({ timeout: 5000 }).catch(() => false)) {
        await expect(table).toHaveScreenshot('data-table.png', {
          maxDiffPixels: 300,
        })
      }
    })
    
    test('should match form visual snapshot', async ({ page }) => {
      await page.goto('/programs/new')
      await page.waitForLoadState('networkidle')
      
      const form = page.locator('form').first()
      
      if (await form.isVisible()) {
        await expect(form).toHaveScreenshot('form.png', {
          maxDiffPixels: 200,
        })
      }
    })
  })
  
  test.describe('Responsive Visual Tests', () => {
    const viewports = [
      { name: 'mobile', width: 375, height: 667 },
      { name: 'tablet', width: 768, height: 1024 },
      { name: 'desktop', width: 1280, height: 720 },
      { name: 'wide', width: 1920, height: 1080 },
    ]
    
    for (const viewport of viewports) {
      test(`should match dashboard at ${viewport.name} viewport`, async ({ page }) => {
        await page.setViewportSize({ width: viewport.width, height: viewport.height })
        await page.goto('/dashboard')
        await page.waitForLoadState('networkidle')
        await page.waitForTimeout(500)
        
        await expect(page).toHaveScreenshot(`dashboard-${viewport.name}.png`, {
          fullPage: false, // Just viewport
          maxDiffPixels: 5000, // Dashboard has dynamic content (timestamps, stats)
        })
      })
    }
  })
  
  test.describe('Theme Visual Tests', () => {
    test('should match light theme', async ({ page }) => {
      await page.goto('/dashboard')
      await page.waitForLoadState('networkidle')
      
      // Ensure light theme
      await page.evaluate(() => {
        document.documentElement.classList.remove('dark')
        document.documentElement.classList.add('light')
        localStorage.setItem('theme', 'light')
      })
      
      await page.waitForTimeout(500)
      
      await expect(page).toHaveScreenshot('dashboard-light.png', {
        maxDiffPixels: 300,
      })
    })
    
    test('should match dark theme', async ({ page }) => {
      await page.goto('/dashboard')
      await page.waitForLoadState('networkidle')
      
      // Switch to dark theme
      await page.evaluate(() => {
        document.documentElement.classList.remove('light')
        document.documentElement.classList.add('dark')
        localStorage.setItem('theme', 'dark')
      })
      
      await page.waitForTimeout(500)
      
      await expect(page).toHaveScreenshot('dashboard-dark.png', {
        maxDiffPixels: 300,
      })
    })
  })
  
  test.describe('State Visual Tests', () => {
    test('should match empty state', async ({ page }) => {
      await page.goto('/programs')
      await page.waitForLoadState('networkidle')
      
      // Check for empty state
      const emptyState = page.locator('[data-testid="empty-state"], .empty-state, text=/no.*found|empty|get started/i').first()
      
      if (await emptyState.isVisible({ timeout: 3000 }).catch(() => false)) {
        await expect(emptyState).toHaveScreenshot('empty-state.png', {
          maxDiffPixels: 200,
        })
      }
    })
    
    test('should match loading state', async ({ page }) => {
      // Intercept API to delay response
      await page.route('**/brapi/v2/**', async route => {
        await new Promise(resolve => setTimeout(resolve, 2000))
        await route.continue()
      })
      
      await page.goto('/programs')
      
      // Capture loading state
      const loadingIndicator = page.locator('.animate-spin, [data-testid="loading"], .skeleton').first()
      
      if (await loadingIndicator.isVisible({ timeout: 1000 }).catch(() => false)) {
        await expect(loadingIndicator).toHaveScreenshot('loading-state.png', {
          maxDiffPixels: 300,
        })
      }
    })
    
    test('should match error state', async ({ page }) => {
      // Force error by blocking API
      await page.route('**/brapi/v2/**', route => {
        route.fulfill({
          status: 500,
          body: JSON.stringify({ detail: 'Internal Server Error' }),
        })
      })
      
      await page.goto('/programs')
      await page.waitForTimeout(2000)
      
      // Check for error state
      const errorState = page.locator('[data-testid="error"], .error, [role="alert"]').first()
      
      if (await errorState.isVisible({ timeout: 3000 }).catch(() => false)) {
        await expect(errorState).toHaveScreenshot('error-state.png', {
          maxDiffPixels: 200,
        })
      }
    })
  })
})
