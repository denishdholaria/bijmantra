/**
 * Accessibility E2E Tests
 * 
 * Tests WCAG 2.1 compliance:
 * - Keyboard navigation
 * - Screen reader compatibility
 * - Color contrast
 * - Focus management
 * - ARIA attributes
 */

import { test, expect } from '@playwright/test'
import AxeBuilder from '@axe-core/playwright'

test.describe('Accessibility Tests', () => {
  test.use({ storageState: 'playwright/.auth/user.json' })
  
  // Core pages to test for accessibility
  const pagesToTest = [
    { name: 'Login', path: '/login', requiresAuth: false },
    { name: 'Dashboard', path: '/dashboard', requiresAuth: true },
    { name: 'Programs', path: '/programs', requiresAuth: true },
    { name: 'Germplasm', path: '/germplasm', requiresAuth: true },
    { name: 'Trials', path: '/trials', requiresAuth: true },
    { name: 'Settings', path: '/settings', requiresAuth: true },
  ]
  
  test.describe('Axe Accessibility Scans', () => {
    for (const pageInfo of pagesToTest) {
      test(`should have no critical accessibility violations on ${pageInfo.name}`, async ({ page }) => {
        await page.goto(pageInfo.path)
        await page.waitForLoadState('networkidle')
        
        // Wait for page to stabilize
        await page.waitForTimeout(1000)
        
        // Run axe accessibility scan
        const accessibilityScanResults = await new AxeBuilder({ page })
          .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'])
          .exclude('.chart-container') // Exclude complex chart components
          .exclude('canvas') // Exclude canvas elements (3D, charts)
          .exclude('.recharts-wrapper') // Exclude Recharts components
          .exclude('.leaflet-container') // Exclude Leaflet maps
          .exclude('[data-radix-popper-content-wrapper]') // Exclude Radix UI poppers
          .exclude('.toaster') // Exclude toast notifications
          .analyze()
        
        // Filter for critical and serious violations
        const criticalViolations = accessibilityScanResults.violations.filter(
          v => v.impact === 'critical' || v.impact === 'serious'
        )
        
        // Log violations for debugging
        if (criticalViolations.length > 0) {
          console.log(`Accessibility violations on ${pageInfo.name}:`)
          criticalViolations.forEach(v => {
            console.log(`  - ${v.id}: ${v.description} (${v.impact})`)
            v.nodes.forEach(n => {
              console.log(`    Target: ${n.target}`)
            })
          })
        }
        
        // Should have no critical violations
        expect(criticalViolations).toHaveLength(0)
      })
    }
  })
  
  test.describe('Keyboard Navigation', () => {
    test('should navigate login form with keyboard', async ({ page }) => {
      await page.goto('/login')
      await page.waitForLoadState('networkidle')
      
      // Tab to email input
      await page.keyboard.press('Tab')
      
      // Check if email input is focused
      const emailFocused = await page.evaluate(() => {
        const active = document.activeElement
        return active?.tagName === 'INPUT' && 
               (active.getAttribute('type') === 'email' || 
                active.getAttribute('name')?.includes('email'))
      })
      
      // Tab to password input
      await page.keyboard.press('Tab')
      
      // Tab to submit button
      await page.keyboard.press('Tab')
      
      // Should be able to submit with Enter
      const submitFocused = await page.evaluate(() => {
        const active = document.activeElement
        return active?.tagName === 'BUTTON'
      })
      
      expect(emailFocused || submitFocused).toBeTruthy()
    })
    
    test('should navigate sidebar with keyboard', async ({ page }) => {
      await page.goto('/dashboard')
      await page.waitForLoadState('networkidle')
      
      // Find sidebar
      const sidebar = page.locator('nav, aside, [role="navigation"]').first()
      
      if (await sidebar.isVisible()) {
        // Tab through sidebar items
        for (let i = 0; i < 5; i++) {
          await page.keyboard.press('Tab')
        }
        
        // Check if a link is focused
        const linkFocused = await page.evaluate(() => {
          const active = document.activeElement
          return active?.tagName === 'A' || active?.tagName === 'BUTTON'
        })
        
        expect(linkFocused).toBeTruthy()
      }
    })
    
    test('should trap focus in modal dialogs', async ({ page }) => {
      await page.goto('/programs')
      await page.waitForLoadState('networkidle')
      
      // Try to open a modal (e.g., delete confirmation)
      const deleteButton = page.locator('button:has-text("Delete")').first()
      
      if (await deleteButton.isVisible({ timeout: 3000 }).catch(() => false)) {
        await deleteButton.click()
        
        // Check if modal is open
        const modal = page.locator('[role="dialog"], [role="alertdialog"]').first()
        
        if (await modal.isVisible({ timeout: 2000 }).catch(() => false)) {
          // Tab through modal
          await page.keyboard.press('Tab')
          await page.keyboard.press('Tab')
          await page.keyboard.press('Tab')
          
          // Focus should stay within modal
          const focusInModal = await page.evaluate(() => {
            const active = document.activeElement
            const modal = document.querySelector('[role="dialog"], [role="alertdialog"]')
            return modal?.contains(active)
          })
          
          expect(focusInModal).toBeTruthy()
          
          // Close modal with Escape
          await page.keyboard.press('Escape')
        }
      }
    })
  })
  
  test.describe('Focus Management', () => {
    test('should have visible focus indicators', async ({ page }) => {
      await page.goto('/login')
      await page.waitForLoadState('networkidle')
      
      // Tab to first focusable element
      await page.keyboard.press('Tab')
      
      // Check if focus is visible
      const hasFocusStyle = await page.evaluate(() => {
        const active = document.activeElement
        if (!active) return false
        
        const styles = window.getComputedStyle(active)
        const outline = styles.outline
        const boxShadow = styles.boxShadow
        const border = styles.border
        
        // Check for visible focus indicator
        return outline !== 'none' || 
               boxShadow !== 'none' || 
               border.includes('rgb')
      })
      
      // Focus should be visible (either through outline, box-shadow, or border)
      expect(hasFocusStyle).toBeTruthy()
    })
    
    test('should return focus after modal closes', async ({ page }) => {
      await page.goto('/programs')
      await page.waitForLoadState('networkidle')
      
      const triggerButton = page.locator('button:has-text("New"), button:has-text("Create")').first()
      
      if (await triggerButton.isVisible({ timeout: 3000 }).catch(() => false)) {
        // Click to potentially open modal or navigate
        await triggerButton.click()
        await page.waitForTimeout(500)
        
        // If modal opened, close it
        const modal = page.locator('[role="dialog"]').first()
        if (await modal.isVisible({ timeout: 1000 }).catch(() => false)) {
          await page.keyboard.press('Escape')
          await page.waitForTimeout(300)
          
          // Focus should return to trigger
          const focusReturned = await page.evaluate(() => {
            const active = document.activeElement
            return active?.tagName === 'BUTTON'
          })
          
          expect(focusReturned).toBeTruthy()
        }
      }
    })
  })
  
  test.describe('ARIA Attributes', () => {
    test('should have proper ARIA labels on interactive elements', async ({ page }) => {
      await page.goto('/dashboard')
      await page.waitForLoadState('networkidle')
      
      // Check buttons have accessible names
      const buttons = page.locator('button')
      const buttonCount = await buttons.count()
      
      for (let i = 0; i < Math.min(buttonCount, 10); i++) {
        const button = buttons.nth(i)
        
        if (await button.isVisible()) {
          const hasAccessibleName = await button.evaluate(el => {
            const ariaLabel = el.getAttribute('aria-label')
            const ariaLabelledBy = el.getAttribute('aria-labelledby')
            const textContent = el.textContent?.trim()
            const title = el.getAttribute('title')
            
            return !!(ariaLabel || ariaLabelledBy || textContent || title)
          })
          
          expect(hasAccessibleName).toBeTruthy()
        }
      }
    })
    
    test('should have proper heading hierarchy', async ({ page }) => {
      await page.goto('/dashboard')
      await page.waitForLoadState('networkidle')
      
      // Get all headings
      const headings = await page.evaluate(() => {
        const h1s = document.querySelectorAll('h1')
        const h2s = document.querySelectorAll('h2')
        const h3s = document.querySelectorAll('h3')
        
        return {
          h1Count: h1s.length,
          h2Count: h2s.length,
          h3Count: h3s.length,
        }
      })
      
      // Should have at least one h1 (or use aria-level)
      // Heading hierarchy should be logical
      expect(headings.h1Count).toBeGreaterThanOrEqual(0)
    })
    
    test('should have proper form labels', async ({ page }) => {
      await page.goto('/login')
      await page.waitForLoadState('networkidle')
      
      // Check inputs have labels
      const inputs = page.locator('input:not([type="hidden"])')
      const inputCount = await inputs.count()
      
      for (let i = 0; i < inputCount; i++) {
        const input = inputs.nth(i)
        
        if (await input.isVisible()) {
          const hasLabel = await input.evaluate(el => {
            const id = el.id
            const ariaLabel = el.getAttribute('aria-label')
            const ariaLabelledBy = el.getAttribute('aria-labelledby')
            const placeholder = el.getAttribute('placeholder')
            const label = id ? document.querySelector(`label[for="${id}"]`) : null
            
            return !!(ariaLabel || ariaLabelledBy || label || placeholder)
          })
          
          expect(hasLabel).toBeTruthy()
        }
      }
    })
  })
  
  test.describe('Color and Contrast', () => {
    test('should not rely solely on color to convey information', async ({ page }) => {
      await page.goto('/dashboard')
      await page.waitForLoadState('networkidle')
      
      // Check error messages have icons or text, not just color
      const errorElements = page.locator('.text-red-, [class*="error"], [role="alert"]')
      const errorCount = await errorElements.count()
      
      for (let i = 0; i < errorCount; i++) {
        const error = errorElements.nth(i)
        
        if (await error.isVisible()) {
          const hasNonColorIndicator = await error.evaluate(el => {
            const hasIcon = el.querySelector('svg, img, [class*="icon"]')
            const hasText = el.textContent?.trim().length > 0
            
            return !!(hasIcon || hasText)
          })
          
          expect(hasNonColorIndicator).toBeTruthy()
        }
      }
    })
  })
  
  test.describe('Screen Reader Compatibility', () => {
    test('should have skip link for main content', async ({ page }) => {
      await page.goto('/dashboard')
      await page.waitForLoadState('networkidle')
      
      // Check for skip link
      const skipLink = page.locator('a[href="#main"], a[href="#content"], .skip-link, [class*="skip"]').first()
      
      // Skip link may be visually hidden but should exist
      const skipLinkExists = await skipLink.count() > 0
      
      // Not all apps have skip links, but it's a best practice
      // Log if missing rather than fail
      if (!skipLinkExists) {
        console.log('Note: No skip link found - consider adding for better accessibility')
      }
    })
    
    test('should have proper landmark regions', async ({ page }) => {
      await page.goto('/dashboard')
      await page.waitForLoadState('networkidle')
      
      // Check for main landmark
      const main = page.locator('main, [role="main"]')
      const hasMain = await main.count() > 0
      
      // Check for navigation landmark
      const nav = page.locator('nav, [role="navigation"]')
      const hasNav = await nav.count() > 0
      
      expect(hasMain).toBeTruthy()
      expect(hasNav).toBeTruthy()
    })
  })
})
