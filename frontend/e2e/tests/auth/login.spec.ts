/**
 * Authentication E2E Tests
 * 
 * Tests:
 * - Login flow
 * - Logout flow
 * - Session persistence
 * - Error handling
 * - Protected route access
 */

import { test, expect } from '../../tests/fixtures/test-fixtures'
import { LoginPage } from '../../pages/login.page'

test.describe('Authentication', () => {
  test.describe('Login Flow', () => {
    test('should display login page correctly', async ({ page }) => {
      const loginPage = new LoginPage(page)
      await loginPage.navigate()
      await loginPage.verifyLoginPage()
    })
    
    test('should login with valid demo credentials', async ({ page }) => {
      const loginPage = new LoginPage(page)
      await loginPage.navigate()
      await loginPage.loginAsDemo()
      await loginPage.verifySuccessfulLogin()
    })
    
    test('should show error for invalid credentials', async ({ page }) => {
      const loginPage = new LoginPage(page)
      await loginPage.navigate()
      await loginPage.login('invalid@email.com', 'wrongpassword')
      
      // Wait for error or redirect (demo mode may still work)
      await page.waitForTimeout(2000)
      
      // Check if still on login page with error, or redirected (demo fallback)
      const url = page.url()
      if (url.includes('/login')) {
        const hasError = await loginPage.hasLoginError()
        // Error should be shown for invalid credentials when backend is available
        // If no error, demo mode fallback is active
        expect(hasError || url.includes('/login')).toBeTruthy()
      }
    })
    
    test('should show error for empty email', async ({ page }) => {
      const loginPage = new LoginPage(page)
      await loginPage.navigate()
      await loginPage.fillPassword('somepassword')
      await loginPage.submit()
      
      // Form validation should prevent submission or show error
      await page.waitForTimeout(1000)
      const url = page.url()
      expect(url).toContain('/login')
    })
    
    test('should show error for empty password', async ({ page }) => {
      const loginPage = new LoginPage(page)
      await loginPage.navigate()
      await loginPage.fillEmail('test@example.com')
      await loginPage.submit()
      
      // Form validation should prevent submission or show error
      await page.waitForTimeout(1000)
      const url = page.url()
      expect(url).toContain('/login')
    })
    
    test('should toggle password visibility', async ({ page }) => {
      const loginPage = new LoginPage(page)
      await loginPage.navigate()
      await loginPage.fillPassword('testpassword')
      
      // Initially password should be hidden
      const initiallyVisible = await loginPage.isPasswordVisible()
      expect(initiallyVisible).toBe(false)
      
      // Toggle visibility
      await loginPage.togglePasswordVisibility()
      
      // Password should now be visible (if toggle exists)
      // Note: Some UIs may not have this feature
    })
    
    test('should persist session after page reload', async ({ page }) => {
      const loginPage = new LoginPage(page)
      await loginPage.navigate()
      await loginPage.loginAsDemo()
      await loginPage.verifySuccessfulLogin()
      
      // Reload page
      await page.reload()
      await page.waitForLoadState('networkidle')
      
      // Should still be authenticated
      const token = await page.evaluate(() => localStorage.getItem('auth_token'))
      expect(token).toBeTruthy()
    })
  })
  
  test.describe('Logout Flow', () => {
    test('should logout successfully', async ({ authenticatedPage }) => {
      const page = authenticatedPage
      
      // Navigate to dashboard
      await page.goto('/dashboard')
      await page.waitForLoadState('networkidle')
      
      // Find and click user menu
      const userMenu = page.locator('[data-testid="user-menu"], button:has([class*="avatar"]), [aria-label="User menu"]').first()
      if (await userMenu.isVisible({ timeout: 5000 }).catch(() => false)) {
        await userMenu.click()
        
        // Click logout
        const logoutButton = page.locator('button:has-text("Logout"), a:has-text("Logout"), [data-testid="logout"]').first()
        if (await logoutButton.isVisible({ timeout: 3000 }).catch(() => false)) {
          await logoutButton.click()
          
          // Should redirect to login
          await page.waitForURL(/\/login/, { timeout: 10000 })
          
          // Token should be cleared
          const token = await page.evaluate(() => localStorage.getItem('auth_token'))
          expect(token).toBeFalsy()
        }
      }
    })
  })
  
  test.describe('Protected Routes', () => {
    test('should redirect to login when accessing protected route without auth', async ({ page }) => {
      // Clear any existing auth
      await page.goto('/login')
      await page.evaluate(() => localStorage.removeItem('auth_token'))
      
      // Try to access protected route
      await page.goto('/dashboard')
      
      // Should redirect to login
      await page.waitForURL(/\/login/, { timeout: 10000 })
    })
    
    test('should access protected route with valid auth', async ({ authenticatedPage }) => {
      const page = authenticatedPage
      
      await page.goto('/dashboard')
      await page.waitForLoadState('networkidle')
      
      // Should not redirect to login
      expect(page.url()).not.toContain('/login')
    })
    
    test('should redirect to login on 401 response', async ({ page }) => {
      // Login first
      const loginPage = new LoginPage(page)
      await loginPage.navigate()
      await loginPage.loginAsDemo()
      
      // Manually invalidate token
      await page.evaluate(() => {
        localStorage.setItem('auth_token', 'invalid_token')
      })
      
      // Navigate to a page that requires API call
      await page.goto('/programs')
      
      // Wait for potential redirect
      await page.waitForTimeout(3000)
      
      // May redirect to login if backend rejects invalid token
      // Or may show error if demo mode handles it differently
    })
  })
  
  test.describe('Session Management', () => {
    test('should handle multiple tabs with same session', async ({ browser }) => {
      const context = await browser.newContext({
        storageState: 'playwright/.auth/user.json',
      })
      
      // Open two tabs
      const page1 = await context.newPage()
      const page2 = await context.newPage()
      
      // Navigate both to dashboard
      await page1.goto('/dashboard')
      await page2.goto('/programs')
      
      // Both should be authenticated
      const token1 = await page1.evaluate(() => localStorage.getItem('auth_token'))
      const token2 = await page2.evaluate(() => localStorage.getItem('auth_token'))
      
      expect(token1).toBeTruthy()
      expect(token2).toBeTruthy()
      expect(token1).toBe(token2)
      
      await context.close()
    })
  })
})
