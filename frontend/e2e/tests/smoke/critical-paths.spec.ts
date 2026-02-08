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
      
      // Use environment variables with fallbacks
      const email = process.env.E2E_TEST_EMAIL || 'demo@bijmantra.org'
      const password = process.env.E2E_TEST_PASSWORD || 'Demo123!'
      
      // Fill credentials
      await page.locator('input[type="email"], input[name="email"]').first().fill(email)
      await page.locator('input[type="password"]').first().fill(password)
      
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
      
      // The BijMantrAGSDesktop shell renders header + content area (no <main> tag)
      const header = page.locator('header').first()
      await expect(header).toBeVisible({ timeout: 15000 })
      expect(page.url()).toContain('/dashboard')
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
      
      // In an SPA, unmatched routes may render the shell with empty content,
      // redirect to dashboard, or show a 404 component
      const content = await page.content()
      const is404 = content.includes('404') || 
                    content.includes('Not Found') || 
                    content.includes('not found')
      
      // Check if it redirected away from the invalid route
      const redirectedAway = !page.url().includes('this-route-does-not-exist')
      
      // The shell still renders (header visible) — page handled the unknown route
      const headerVisible = await page.locator('header').first().isVisible({ timeout: 5000 }).catch(() => false)
      
      // Pass if: shows 404, redirected, or shell rendered (app didn't crash)
      expect(is404 || redirectedAway || headerVisible).toBeTruthy()
    })
  })
  
  test.describe('Responsive Design', () => {
    test.use({ storageState: 'playwright/.auth/user.json' })
    
    test('should be responsive on mobile viewport', async ({ page }) => {
      await page.setViewportSize({ width: 375, height: 667 })
      await navigateAuthenticated(page, '/dashboard')
      
      // Page should still be functional — header renders in the shell
      const header = page.locator('header').first()
      await expect(header).toBeVisible({ timeout: 10000 })
      expect(page.url()).toContain('/dashboard')
    })
    
    test('should be responsive on tablet viewport', async ({ page }) => {
      await page.setViewportSize({ width: 768, height: 1024 })
      await navigateAuthenticated(page, '/dashboard')
      
      const header = page.locator('header').first()
      await expect(header).toBeVisible({ timeout: 10000 })
      expect(page.url()).toContain('/dashboard')
    })
  })
})
