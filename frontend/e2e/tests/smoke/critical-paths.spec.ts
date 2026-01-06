/**
 * Smoke Tests - Critical Paths
 * 
 * Quick validation that core functionality works:
 * - Application loads
 * - Authentication works
 * - Main navigation works
 * - Key pages render
 */

import { test, expect } from '@playwright/test'
import { navigateAuthenticated } from '../../helpers/auth.helper'

test.describe('Smoke Tests - Critical Paths', () => {
  test.describe('Application Health', () => {
    test('should load login page', async ({ page }) => {
      await page.goto('/login')
      await expect(page).toHaveTitle(/BijMantra|Login/i)
      
      // Login form should be visible
      const emailInput = page.locator('input[type="email"], input[name="email"]').first()
      await expect(emailInput).toBeVisible({ timeout: 10000 })
    })
    
    test('should have no console errors on login page', async ({ page }) => {
      const errors: string[] = []
      page.on('console', msg => {
        if (msg.type() === 'error') {
          errors.push(msg.text())
        }
      })
      
      await page.goto('/login')
      await page.waitForLoadState('networkidle')
      
      // Filter out known acceptable errors
      const criticalErrors = errors.filter(e => 
        !e.includes('favicon') && 
        !e.includes('404') &&
        !e.includes('Failed to load resource')
      )
      
      expect(criticalErrors).toHaveLength(0)
    })
  })
  
  test.describe('Authentication Flow', () => {
    test('should complete login flow', async ({ page }) => {
      await page.goto('/login')
      
      // Fill credentials
      await page.locator('input[type="email"], input[name="email"]').first().fill('demo@bijmantra.com')
      await page.locator('input[type="password"]').first().fill('demo123')
      
      // Submit
      await page.locator('button[type="submit"]').first().click()
      
      // Should redirect away from login
      await page.waitForURL(/\/(dashboard|gateway)/, { timeout: 15000 })
      
      // Should have auth token
      const token = await page.evaluate(() => localStorage.getItem('auth_token'))
      expect(token).toBeTruthy()
    })
  })
  
  test.describe('Core Navigation', () => {
    test.use({ storageState: 'playwright/.auth/user.json' })
    
    test('should load dashboard', async ({ page }) => {
      await navigateAuthenticated(page, '/dashboard')
      
      // Main content should be visible
      const main = page.locator('main, .min-h-screen').first()
      await expect(main).toBeVisible({ timeout: 15000 })
    })
    
    test('should navigate to programs page', async ({ page }) => {
      await navigateAuthenticated(page, '/programs')
      expect(page.url()).toContain('/programs')
    })
    
    test('should navigate to trials page', async ({ page }) => {
      await navigateAuthenticated(page, '/trials')
      expect(page.url()).toContain('/trials')
    })
    
    test('should navigate to germplasm page', async ({ page }) => {
      await navigateAuthenticated(page, '/germplasm')
      expect(page.url()).toContain('/germplasm')
    })
    
    test('should navigate to locations page', async ({ page }) => {
      await navigateAuthenticated(page, '/locations')
      expect(page.url()).toContain('/locations')
    })
    
    test('should navigate to traits page', async ({ page }) => {
      await navigateAuthenticated(page, '/traits')
      expect(page.url()).toContain('/traits')
    })
  })
  
  test.describe('Division Navigation', () => {
    test.use({ storageState: 'playwright/.auth/user.json' })
    
    test('should load seed bank dashboard', async ({ page }) => {
      await navigateAuthenticated(page, '/seed-bank')
      expect(page.url()).toContain('/seed-bank')
    })
    
    test('should load seed operations dashboard', async ({ page }) => {
      await navigateAuthenticated(page, '/seed-operations')
      expect(page.url()).toContain('/seed-operations')
    })
    
    test('should load earth systems dashboard', async ({ page }) => {
      await navigateAuthenticated(page, '/earth-systems')
      expect(page.url()).toContain('/earth-systems')
    })
    
    test('should load commercial dashboard', async ({ page }) => {
      await navigateAuthenticated(page, '/commercial')
      expect(page.url()).toContain('/commercial')
    })
  })
  
  test.describe('Error Handling', () => {
    test.use({ storageState: 'playwright/.auth/user.json' })
    
    test('should show 404 page for invalid route', async ({ page }) => {
      await navigateAuthenticated(page, '/this-route-does-not-exist-12345')
      
      // Should show 404 or redirect
      const content = await page.content()
      const is404 = content.includes('404') || 
                    content.includes('Not Found') || 
                    content.includes('not found')
      
      // Either shows 404 or redirects to a valid page
      expect(is404 || !page.url().includes('this-route-does-not-exist')).toBeTruthy()
    })
  })
  
  test.describe('Responsive Design', () => {
    test.use({ storageState: 'playwright/.auth/user.json' })
    
    test('should be responsive on mobile viewport', async ({ page }) => {
      await page.setViewportSize({ width: 375, height: 667 })
      await navigateAuthenticated(page, '/dashboard')
      
      // Page should still be functional
      const main = page.locator('main, [role="main"], .min-h-screen').first()
      await expect(main).toBeVisible({ timeout: 10000 })
    })
    
    test('should be responsive on tablet viewport', async ({ page }) => {
      await page.setViewportSize({ width: 768, height: 1024 })
      await navigateAuthenticated(page, '/dashboard')
      
      const main = page.locator('main, [role="main"], .min-h-screen').first()
      await expect(main).toBeVisible({ timeout: 10000 })
    })
  })
})
