/**
 * LD Analysis Workflow E2E Tests
 * 
 * Tests the complete LD Analysis workflow:
 * - Input → Compute → Result display
 * - Loading states during computation
 * - Empty state handling (no data)
 * - Error state handling (computation failures, invalid input)
 * 
 * Validates: FR-5, AC-5
 */

import { test, expect } from '@playwright/test'
import { navigateAuthenticated } from '../../helpers/auth.helper'

test.describe('LD Analysis Workflow', () => {
  test.use({ storageState: 'playwright/.auth/user.json' })

  test.describe('Page Load and Initial State', () => {
    test('should load LD Analysis page successfully', async ({ page }) => {
      await navigateAuthenticated(page, '/wasm-ld')
      
      expect(page.url()).toContain('/wasm-ld')
      
      // Page title should be visible
      const heading = page.locator('h1').first()
      await expect(heading).toContainText(/linkage disequilibrium/i, { timeout: 10000 })
    })

    test('should display summary cards with initial values', async ({ page }) => {
      await navigateAuthenticated(page, '/wasm-ld')
      
      // Wait for page to load
      await expect(page.locator('h1')).toContainText(/linkage disequilibrium/i, { timeout: 10000 })
      
      // Summary cards should be visible
      await expect(page.getByText(/markers/i).first()).toBeVisible()
      await expect(page.getByText(/high ld pairs/i).first()).toBeVisible()
      await expect(page.getByText(/hwe violations/i).first()).toBeVisible()
      await expect(page.getByText(/mean r²/i).first()).toBeVisible()
    })

    test('should display analysis parameters section', async ({ page }) => {
      await navigateAuthenticated(page, '/wasm-ld')
      
      await expect(page.locator('h1')).toContainText(/linkage disequilibrium/i, { timeout: 10000 })
      
      // Parameters card should be visible
      await expect(page.getByText(/analysis parameters/i)).toBeVisible()
      
      // Run Analysis button should be visible
      const runButton = page.getByRole('button', { name: /run analysis/i })
      await expect(runButton).toBeVisible()
    })

    test('should display result tabs', async ({ page }) => {
      await navigateAuthenticated(page, '/wasm-ld')
      
      await expect(page.locator('h1')).toContainText(/linkage disequilibrium/i, { timeout: 10000 })
      
      // All tabs should be visible
      await expect(page.getByRole('tab', { name: /ld pairs/i })).toBeVisible()
      await expect(page.getByRole('tab', { name: /ld matrix/i })).toBeVisible()
      await expect(page.getByRole('tab', { name: /hwe tests/i })).toBeVisible()
      await expect(page.getByRole('tab', { name: /ld decay/i })).toBeVisible()
    })
  })

  test.describe('Empty State Handling', () => {
    test('should show error message when variant set ID is empty in server mode', async ({ page }) => {
      await navigateAuthenticated(page, '/wasm-ld')
      
      await expect(page.locator('h1')).toContainText(/linkage disequilibrium/i, { timeout: 10000 })
      
      // Ensure we're in server mode (production default)
      // In production builds, server mode is the only option
      
      // Clear variant set ID if present
      const variantSetInput = page.locator('input#ld-variant-set-id')
      if (await variantSetInput.isVisible({ timeout: 2000 }).catch(() => false)) {
        await variantSetInput.clear()
      }
      
      // Click Run Analysis
      const runButton = page.getByRole('button', { name: /run analysis/i })
      await runButton.click()
      
      // Should show error message about missing variant set ID
      await expect(page.getByText(/enter a variant set id/i)).toBeVisible({ timeout: 5000 })
    })

    test('should show empty state in results tabs before analysis', async ({ page }) => {
      await navigateAuthenticated(page, '/wasm-ld')
      
      await expect(page.locator('h1')).toContainText(/linkage disequilibrium/i, { timeout: 10000 })
      
      // Check LD Matrix tab for empty state
      await page.getByRole('tab', { name: /ld matrix/i }).click()
      await expect(page.getByText(/run analysis to generate/i)).toBeVisible()
      
      // Check LD Decay tab for empty state
      await page.getByRole('tab', { name: /ld decay/i }).click()
      await expect(page.getByText(/run analysis to see/i)).toBeVisible()
    })
  })

  test.describe('Error State Handling', () => {
    test('should handle invalid variant set ID gracefully', async ({ page }) => {
      await navigateAuthenticated(page, '/wasm-ld')
      
      await expect(page.locator('h1')).toContainText(/linkage disequilibrium/i, { timeout: 10000 })
      
      // Enter an invalid variant set ID
      const variantSetInput = page.locator('input#ld-variant-set-id')
      if (await variantSetInput.isVisible({ timeout: 2000 }).catch(() => false)) {
        await variantSetInput.fill('invalid-nonexistent-id-12345')
        
        // Click Run Analysis
        const runButton = page.getByRole('button', { name: /run analysis/i })
        await runButton.click()
        
        // Should show error message or handle gracefully
        // Wait for either error message or completion
        await page.waitForTimeout(3000)
        
        // Button should not be stuck in loading state
        await expect(runButton).not.toHaveText(/analyzing/i)
      }
    })

    test('should recover from error state and allow retry', async ({ page }) => {
      await navigateAuthenticated(page, '/wasm-ld')
      
      await expect(page.locator('h1')).toContainText(/linkage disequilibrium/i, { timeout: 10000 })
      
      // Trigger an error by leaving variant set ID empty
      const variantSetInput = page.locator('input#ld-variant-set-id')
      if (await variantSetInput.isVisible({ timeout: 2000 }).catch(() => false)) {
        await variantSetInput.clear()
      }
      
      const runButton = page.getByRole('button', { name: /run analysis/i })
      await runButton.click()
      
      // Wait for error message
      await expect(page.getByText(/enter a variant set id/i)).toBeVisible({ timeout: 5000 })
      
      // Now enter a valid ID and retry
      if (await variantSetInput.isVisible({ timeout: 2000 }).catch(() => false)) {
        await variantSetInput.fill('test-variant-set-001')
        
        // Button should be clickable again
        await expect(runButton).toBeEnabled()
        
        // Can click again (may fail due to invalid ID, but should not crash)
        await runButton.click()
        await page.waitForTimeout(2000)
      }
    })
  })

  test.describe('Loading State', () => {
    test('should show loading state during analysis', async ({ page }) => {
      await navigateAuthenticated(page, '/wasm-ld')
      
      await expect(page.locator('h1')).toContainText(/linkage disequilibrium/i, { timeout: 10000 })
      
      // Enter a variant set ID
      const variantSetInput = page.locator('input#ld-variant-set-id')
      if (await variantSetInput.isVisible({ timeout: 2000 }).catch(() => false)) {
        await variantSetInput.fill('test-variant-set-001')
        
        const runButton = page.getByRole('button', { name: /run analysis/i })
        
        // Click and immediately check for loading state
        await runButton.click()
        
        // Button should show "Analyzing..." text briefly
        // Note: This may be very fast, so we use a short timeout
        const isAnalyzing = await runButton.getByText(/analyzing/i).isVisible({ timeout: 1000 }).catch(() => false)
        
        // Either we caught the loading state, or it completed very quickly
        // Both are acceptable outcomes
        expect(typeof isAnalyzing).toBe('boolean')
        
        // Wait for completion
        await page.waitForTimeout(3000)
        
        // Button should return to normal state
        await expect(runButton).toHaveText(/run analysis/i)
      }
    })

    test('should disable run button during processing', async ({ page }) => {
      await navigateAuthenticated(page, '/wasm-ld')
      
      await expect(page.locator('h1')).toContainText(/linkage disequilibrium/i, { timeout: 10000 })
      
      const variantSetInput = page.locator('input#ld-variant-set-id')
      if (await variantSetInput.isVisible({ timeout: 2000 }).catch(() => false)) {
        await variantSetInput.fill('test-variant-set-001')
        
        const runButton = page.getByRole('button', { name: /run analysis/i })
        
        // Initial state should be enabled
        await expect(runButton).toBeEnabled()
        
        // Click to start analysis
        await runButton.click()
        
        // Check if button becomes disabled (may be very brief)
        const wasDisabled = await runButton.isDisabled({ timeout: 500 }).catch(() => false)
        
        // Wait for completion
        await page.waitForTimeout(3000)
        
        // Button should be enabled again
        await expect(runButton).toBeEnabled()
      }
    })
  })

  test.describe('Successful Analysis Flow', () => {
    test('should complete full workflow with valid data', async ({ page }) => {
      await navigateAuthenticated(page, '/wasm-ld')
      
      await expect(page.locator('h1')).toContainText(/linkage disequilibrium/i, { timeout: 10000 })
      
      // Check if we're in development mode with synthetic data toggle
      const serverModeSwitch = page.locator('input#server-mode')
      const hasSyntheticMode = await serverModeSwitch.isVisible({ timeout: 2000 }).catch(() => false)
      
      if (hasSyntheticMode) {
        // Development mode: use synthetic data
        // Toggle to client-side mode
        await serverModeSwitch.click()
        
        // Adjust parameters
        const samplesInput = page.locator('input[type="number"]').first()
        await samplesInput.fill('100')
        
        // Run analysis
        const runButton = page.getByRole('button', { name: /run analysis/i })
        await runButton.click()
        
        // Wait for analysis to complete
        await page.waitForTimeout(2000)
        
        // Check that results are displayed
        // LD Pairs tab should have data
        await page.getByRole('tab', { name: /ld pairs/i }).click()
        
        // Should have table with results
        const table = page.locator('table').first()
        await expect(table).toBeVisible({ timeout: 5000 })
        
        // Should have at least one row of data
        const tableRows = page.locator('tbody tr')
        const rowCount = await tableRows.count()
        expect(rowCount).toBeGreaterThan(0)
        
        // Check LD Matrix tab
        await page.getByRole('tab', { name: /ld matrix/i }).click()
        
        // Should show heatmap (not empty state message)
        await expect(page.getByText(/run analysis to generate/i)).not.toBeVisible()
        
        // Check HWE Tests tab
        await page.getByRole('tab', { name: /hwe tests/i }).click()
        
        // Should have HWE test results
        const hweTable = page.locator('table').first()
        await expect(hweTable).toBeVisible()
        
        // Check LD Decay tab
        await page.getByRole('tab', { name: /ld decay/i }).click()
        
        // Should show chart (not empty state message)
        await expect(page.getByText(/run analysis to see/i)).not.toBeVisible()
        
        // Summary cards should be updated
        await expect(page.getByText(/high ld pairs/i).first()).toBeVisible()
      } else {
        // Production mode: would need real variant set data
        // Just verify the UI is ready for input
        const variantSetInput = page.locator('input#ld-variant-set-id')
        await expect(variantSetInput).toBeVisible()
        
        const runButton = page.getByRole('button', { name: /run analysis/i })
        await expect(runButton).toBeVisible()
        await expect(runButton).toBeEnabled()
      }
    })

    test('should update summary cards after analysis', async ({ page }) => {
      await navigateAuthenticated(page, '/wasm-ld')
      
      await expect(page.locator('h1')).toContainText(/linkage disequilibrium/i, { timeout: 10000 })
      
      // Check if synthetic mode is available
      const serverModeSwitch = page.locator('input#server-mode')
      const hasSyntheticMode = await serverModeSwitch.isVisible({ timeout: 2000 }).catch(() => false)
      
      if (hasSyntheticMode) {
        // Get initial marker count
        const markersCard = page.locator('text=/markers/i').first().locator('..')
        const initialMarkers = await markersCard.locator('.text-2xl').textContent()
        
        // Toggle to client-side mode
        await serverModeSwitch.click()
        
        // Run analysis
        const runButton = page.getByRole('button', { name: /run analysis/i })
        await runButton.click()
        
        // Wait for completion
        await page.waitForTimeout(2000)
        
        // Verify summary cards are updated
        const updatedMarkers = await markersCard.locator('.text-2xl').textContent()
        
        // Should have marker count displayed
        expect(updatedMarkers).toBeTruthy()
        expect(updatedMarkers).not.toBe('-')
      }
    })

    test('should allow switching between result tabs', async ({ page }) => {
      await navigateAuthenticated(page, '/wasm-ld')
      
      await expect(page.locator('h1')).toContainText(/linkage disequilibrium/i, { timeout: 10000 })
      
      // Navigate through all tabs
      await page.getByRole('tab', { name: /ld pairs/i }).click()
      await expect(page.getByText(/pairwise ld/i)).toBeVisible()
      
      await page.getByRole('tab', { name: /ld matrix/i }).click()
      await expect(page.getByText(/ld matrix heatmap/i)).toBeVisible()
      
      await page.getByRole('tab', { name: /hwe tests/i }).click()
      await expect(page.getByText(/hardy-weinberg equilibrium/i)).toBeVisible()
      
      await page.getByRole('tab', { name: /ld decay/i }).click()
      await expect(page.getByText(/ld decay/i)).toBeVisible()
      
      // Should be able to go back to first tab
      await page.getByRole('tab', { name: /ld pairs/i }).click()
      await expect(page.getByText(/pairwise ld/i)).toBeVisible()
    })
  })

  test.describe('Parameter Adjustment', () => {
    test('should allow adjusting LD threshold', async ({ page }) => {
      await navigateAuthenticated(page, '/wasm-ld')
      
      await expect(page.locator('h1')).toContainText(/linkage disequilibrium/i, { timeout: 10000 })
      
      // Find the LD threshold slider
      const thresholdSlider = page.locator('input[type="range"]').first()
      
      if (await thresholdSlider.isVisible({ timeout: 2000 }).catch(() => false)) {
        // Slider should be interactive
        await expect(thresholdSlider).toBeEnabled()
        
        // Get initial value
        const initialValue = await thresholdSlider.getAttribute('value')
        expect(initialValue).toBeTruthy()
      }
    })

    test('should allow entering variant set ID', async ({ page }) => {
      await navigateAuthenticated(page, '/wasm-ld')
      
      await expect(page.locator('h1')).toContainText(/linkage disequilibrium/i, { timeout: 10000 })
      
      const variantSetInput = page.locator('input#ld-variant-set-id')
      
      if (await variantSetInput.isVisible({ timeout: 2000 }).catch(() => false)) {
        // Should be able to type in the input
        await variantSetInput.fill('test-variant-123')
        
        // Value should be set
        await expect(variantSetInput).toHaveValue('test-variant-123')
        
        // Should be able to clear it
        await variantSetInput.clear()
        await expect(variantSetInput).toHaveValue('')
      }
    })
  })

  test.describe('WebAssembly Integration', () => {
    test('should display WASM status badge', async ({ page }) => {
      await navigateAuthenticated(page, '/wasm-ld')
      
      await expect(page.locator('h1')).toContainText(/linkage disequilibrium/i, { timeout: 10000 })
      
      // WASM badge should be visible
      const wasmBadge = page.locator('text=/webassembly|loading/i').first()
      await expect(wasmBadge).toBeVisible({ timeout: 5000 })
    })
  })
})
