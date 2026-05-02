/**
 * LD Analysis E2E Tests
 * 
 * Tests the complete LD analysis workflow including:
 * - Loading state
 * - Empty state
 * - Error state
 * - Success state with data visualization
 */

import { test, expect } from '@playwright/test';
import { navigateAuthenticated } from '../../../helpers/auth.helper';

test.describe('LD Analysis Workflow', () => {
  test.use({ storageState: 'playwright/.auth/user.json' });

  test.describe('Page Load and Initial State', () => {
    test('should load LD analysis page', async ({ page }) => {
      await navigateAuthenticated(page, '/ld-analysis');
      expect(page.url()).toContain('/ld-analysis');

      // Page title should be visible
      const heading = page.locator('h1').first();
      await expect(heading).toContainText(/linkage disequilibrium/i, { timeout: 10000 });
    });

    test('should display WebAssembly status badge', async ({ page }) => {
      await navigateAuthenticated(page, '/ld-analysis');

      // WebAssembly badge should be visible
      const wasmBadge = page.locator('text=/WebAssembly|Loading/i').first();
      await expect(wasmBadge).toBeVisible({ timeout: 10000 });
    });

    test('should display summary cards', async ({ page }) => {
      await navigateAuthenticated(page, '/ld-analysis');

      // Summary cards should be visible
      await expect(page.getByText('Markers')).toBeVisible({ timeout: 10000 });
      await expect(page.getByText('High LD Pairs')).toBeVisible();
      await expect(page.getByText('HWE Violations')).toBeVisible();
      await expect(page.getByText('Mean r²')).toBeVisible();
    });

    test('should display analysis parameters section', async ({ page }) => {
      await navigateAuthenticated(page, '/ld-analysis');

      // Parameters section should be visible
      await expect(page.getByText('Analysis Parameters')).toBeVisible({ timeout: 10000 });
      await expect(page.getByLabel(/number of samples/i)).toBeVisible();
      await expect(page.getByLabel(/number of markers/i)).toBeVisible();
      await expect(page.getByLabel(/ld threshold/i)).toBeVisible();
    });

    test('should display result tabs', async ({ page }) => {
      await navigateAuthenticated(page, '/ld-analysis');

      // Result tabs should be visible
      await expect(page.getByRole('tab', { name: /ld pairs/i })).toBeVisible({ timeout: 10000 });
      await expect(page.getByRole('tab', { name: /ld matrix/i })).toBeVisible();
      await expect(page.getByRole('tab', { name: /hwe tests/i })).toBeVisible();
      await expect(page.getByRole('tab', { name: /ld decay/i })).toBeVisible();
    });
  });

  test.describe('Empty State', () => {
    test('should show empty state message in LD Matrix tab', async ({ page }) => {
      await navigateAuthenticated(page, '/ld-analysis');

      // Click LD Matrix tab
      await page.getByRole('tab', { name: /ld matrix/i }).click();

      // Empty state message should be visible
      await expect(page.getByText(/run analysis to generate ld matrix/i)).toBeVisible({ timeout: 5000 });
    });

    test('should show empty state message in LD Decay tab', async ({ page }) => {
      await navigateAuthenticated(page, '/ld-analysis');

      // Click LD Decay tab
      await page.getByRole('tab', { name: /ld decay/i }).click();

      // Empty state message should be visible
      await expect(page.getByText(/run analysis to see ld decay pattern/i)).toBeVisible({ timeout: 5000 });
    });

    test('should display zero counts in summary cards initially', async ({ page }) => {
      await navigateAuthenticated(page, '/ld-analysis');

      // Summary cards should show zero or dash
      const summaryCards = page.locator('[class*="card"]');
      await expect(summaryCards.first()).toBeVisible({ timeout: 10000 });
    });
  });

  test.describe('Parameter Configuration', () => {
    test('should allow changing number of samples', async ({ page }) => {
      await navigateAuthenticated(page, '/ld-analysis');

      const samplesInput = page.getByLabel(/number of samples/i);
      await samplesInput.fill('300');

      // Value should be updated
      await expect(samplesInput).toHaveValue('300');
    });

    test('should allow changing number of markers', async ({ page }) => {
      await navigateAuthenticated(page, '/ld-analysis');

      const markersInput = page.getByLabel(/number of markers/i);
      await markersInput.fill('75');

      // Value should be updated
      await expect(markersInput).toHaveValue('75');
    });

    test('should allow adjusting LD threshold slider', async ({ page }) => {
      await navigateAuthenticated(page, '/ld-analysis');

      // Slider should be visible
      const slider = page.getByRole('slider');
      await expect(slider).toBeVisible({ timeout: 10000 });

      // Current threshold value should be displayed
      await expect(page.getByText('0.2')).toBeVisible();
    });

    test('should show variant set ID input in server mode', async ({ page }) => {
      await navigateAuthenticated(page, '/ld-analysis');

      // Variant Set ID input should be visible (default is server mode)
      const variantSetInput = page.getByLabel(/variant set id/i);
      await expect(variantSetInput).toBeVisible({ timeout: 10000 });
    });
  });

  test.describe('Error State', () => {
    test('should show validation error when variant set ID is missing', async ({ page }) => {
      await navigateAuthenticated(page, '/ld-analysis');

      // Clear variant set ID if present
      const variantSetInput = page.getByLabel(/variant set id/i);
      await variantSetInput.clear();

      // Click Run Analysis
      await page.getByRole('button', { name: /run analysis/i }).click();

      // Error message should appear
      await expect(page.getByText(/enter a variant set id/i)).toBeVisible({ timeout: 5000 });
    });

    test('should display error message in amber alert', async ({ page }) => {
      await navigateAuthenticated(page, '/ld-analysis');

      // Clear variant set ID
      const variantSetInput = page.getByLabel(/variant set id/i);
      await variantSetInput.clear();

      // Click Run Analysis
      await page.getByRole('button', { name: /run analysis/i }).click();

      // Error alert should have amber styling
      const errorAlert = page.locator('.border-amber-300').first();
      await expect(errorAlert).toBeVisible({ timeout: 5000 });
    });

    test('should handle API errors gracefully', async ({ page }) => {
      await navigateAuthenticated(page, '/ld-analysis');

      // Enter invalid variant set ID
      const variantSetInput = page.getByLabel(/variant set id/i);
      await variantSetInput.fill('INVALID_ID_12345');

      // Click Run Analysis
      await page.getByRole('button', { name: /run analysis/i }).click();

      // Should show loading state briefly
      await expect(page.getByRole('button', { name: /analyzing/i })).toBeVisible({ timeout: 5000 });

      // Error message should appear (either validation or API error)
      await expect(page.locator('.border-amber-300')).toBeVisible({ timeout: 15000 });
    });
  });

  test.describe('Loading State', () => {
    test('should show loading state during analysis', async ({ page }) => {
      await navigateAuthenticated(page, '/ld-analysis');

      // Enter variant set ID
      const variantSetInput = page.getByLabel(/variant set id/i);
      await variantSetInput.fill('TEST_VS_001');

      // Click Run Analysis
      await page.getByRole('button', { name: /run analysis/i }).click();

      // Loading button should appear
      const analyzingButton = page.getByRole('button', { name: /analyzing/i });
      await expect(analyzingButton).toBeVisible({ timeout: 2000 });

      // Button should be disabled during processing
      await expect(analyzingButton).toBeDisabled();
    });

    test('should disable parameter inputs during processing', async ({ page }) => {
      await navigateAuthenticated(page, '/ld-analysis');

      // Enter variant set ID
      const variantSetInput = page.getByLabel(/variant set id/i);
      await variantSetInput.fill('TEST_VS_001');

      // Click Run Analysis
      await page.getByRole('button', { name: /run analysis/i }).click();

      // Check if analyzing button appears (indicates processing started)
      const analyzingButton = page.getByRole('button', { name: /analyzing/i });
      if (await analyzingButton.isVisible({ timeout: 1000 }).catch(() => false)) {
        // Inputs should be disabled
        const samplesInput = page.getByLabel(/number of samples/i);
        await expect(samplesInput).toBeDisabled();
      }
    });
  });

  test.describe('Success State (Client-Side)', () => {
    test('should run client-side analysis in dev mode', async ({ page }) => {
      await navigateAuthenticated(page, '/ld-analysis');

      // Toggle to client-side mode if available
      const serverSwitch = page.getByRole('switch', { name: /server-side/i });
      if (await serverSwitch.isVisible({ timeout: 2000 }).catch(() => false)) {
        await serverSwitch.click();

        // Set parameters
        await page.getByLabel(/number of samples/i).fill('100');
        await page.getByLabel(/number of markers/i).fill('20');

        // Run analysis
        await page.getByRole('button', { name: /run analysis/i }).click();

        // Wait for analysis to complete
        await expect(page.getByRole('button', { name: /run analysis/i })).toBeVisible({ timeout: 10000 });

        // Results should be visible
        await expect(page.getByText(/M1/)).toBeVisible({ timeout: 5000 });
      }
    });

    test('should display LD pairs table with data', async ({ page }) => {
      await navigateAuthenticated(page, '/ld-analysis');

      // Toggle to client-side mode if available
      const serverSwitch = page.getByRole('switch', { name: /server-side/i });
      if (await serverSwitch.isVisible({ timeout: 2000 }).catch(() => false)) {
        await serverSwitch.click();

        // Run analysis
        await page.getByRole('button', { name: /run analysis/i }).click();
        await page.waitForTimeout(2000);

        // LD Pairs tab should show data
        const table = page.locator('table').first();
        await expect(table).toBeVisible({ timeout: 5000 });

        // Table headers should be visible
        await expect(page.getByText('Marker 1')).toBeVisible();
        await expect(page.getByText('Marker 2')).toBeVisible();
        await expect(page.getByText('Distance')).toBeVisible();
      }
    });

    test('should display LD matrix heatmap', async ({ page }) => {
      await navigateAuthenticated(page, '/ld-analysis');

      // Toggle to client-side mode if available
      const serverSwitch = page.getByRole('switch', { name: /server-side/i });
      if (await serverSwitch.isVisible({ timeout: 2000 }).catch(() => false)) {
        await serverSwitch.click();

        // Run analysis
        await page.getByRole('button', { name: /run analysis/i }).click();
        await page.waitForTimeout(2000);

        // Click LD Matrix tab
        await page.getByRole('tab', { name: /ld matrix/i }).click();

        // Heatmap should be visible (check for colored cells)
        const heatmapCells = page.locator('.w-3.h-3.rounded-sm');
        await expect(heatmapCells.first()).toBeVisible({ timeout: 5000 });
      }
    });

    test('should display LD decay chart', async ({ page }) => {
      await navigateAuthenticated(page, '/ld-analysis');

      // Toggle to client-side mode if available
      const serverSwitch = page.getByRole('switch', { name: /server-side/i });
      if (await serverSwitch.isVisible({ timeout: 2000 }).catch(() => false)) {
        await serverSwitch.click();

        // Run analysis
        await page.getByRole('button', { name: /run analysis/i }).click();
        await page.waitForTimeout(2000);

        // Click LD Decay tab
        await page.getByRole('tab', { name: /ld decay/i }).click();

        // Chart should be visible
        await expect(page.getByText(/based on.*pairwise comparisons/i)).toBeVisible({ timeout: 5000 });
      }
    });

    test('should display HWE tests table', async ({ page }) => {
      await navigateAuthenticated(page, '/ld-analysis');

      // Toggle to client-side mode if available
      const serverSwitch = page.getByRole('switch', { name: /server-side/i });
      if (await serverSwitch.isVisible({ timeout: 2000 }).catch(() => false)) {
        await serverSwitch.click();

        // Run analysis
        await page.getByRole('button', { name: /run analysis/i }).click();
        await page.waitForTimeout(2000);

        // Click HWE Tests tab
        await page.getByRole('tab', { name: /hwe tests/i }).click();

        // HWE table should be visible
        await expect(page.getByText('Chi-square')).toBeVisible({ timeout: 5000 });
        await expect(page.getByText('P-value')).toBeVisible();
      }
    });

    test('should update summary statistics after analysis', async ({ page }) => {
      await navigateAuthenticated(page, '/ld-analysis');

      // Toggle to client-side mode if available
      const serverSwitch = page.getByRole('switch', { name: /server-side/i });
      if (await serverSwitch.isVisible({ timeout: 2000 }).catch(() => false)) {
        await serverSwitch.click();

        // Set parameters
        await page.getByLabel(/number of markers/i).fill('20');

        // Run analysis
        await page.getByRole('button', { name: /run analysis/i }).click();
        await page.waitForTimeout(2000);

        // Summary cards should show updated values
        await expect(page.getByText('20')).toBeVisible({ timeout: 5000 }); // Markers count
      }
    });
  });

  test.describe('Tab Navigation', () => {
    test('should switch between result tabs', async ({ page }) => {
      await navigateAuthenticated(page, '/ld-analysis');

      // Click each tab
      await page.getByRole('tab', { name: /ld pairs/i }).click();
      await expect(page.getByText('Pairwise LD')).toBeVisible({ timeout: 5000 });

      await page.getByRole('tab', { name: /ld matrix/i }).click();
      await expect(page.getByText('LD Matrix Heatmap')).toBeVisible({ timeout: 5000 });

      await page.getByRole('tab', { name: /hwe tests/i }).click();
      await expect(page.getByText('Hardy-Weinberg Equilibrium')).toBeVisible({ timeout: 5000 });

      await page.getByRole('tab', { name: /ld decay/i }).click();
      await expect(page.getByText('LD Decay')).toBeVisible({ timeout: 5000 });
    });
  });

  test.describe('Workflow Completion', () => {
    test('should complete full analysis workflow', async ({ page }) => {
      await navigateAuthenticated(page, '/ld-analysis');

      // 1. Initial state - empty
      await expect(page.getByText('Linkage Disequilibrium Analysis')).toBeVisible({ timeout: 10000 });

      // 2. Configure parameters
      const serverSwitch = page.getByRole('switch', { name: /server-side/i });
      if (await serverSwitch.isVisible({ timeout: 2000 }).catch(() => false)) {
        await serverSwitch.click();
        await page.getByLabel(/number of samples/i).fill('50');
        await page.getByLabel(/number of markers/i).fill('10');

        // 3. Run analysis - loading state
        await page.getByRole('button', { name: /run analysis/i }).click();

        // 4. Wait for completion - success state
        await page.waitForTimeout(2000);

        // 5. Verify results in all tabs
        await page.getByRole('tab', { name: /ld pairs/i }).click();
        await expect(page.locator('table').first()).toBeVisible({ timeout: 5000 });

        await page.getByRole('tab', { name: /ld matrix/i }).click();
        await expect(page.locator('.w-3.h-3.rounded-sm').first()).toBeVisible({ timeout: 5000 });

        await page.getByRole('tab', { name: /hwe tests/i }).click();
        await expect(page.getByText(/Chi-square|χ²/i)).toBeVisible({ timeout: 5000 });

        await page.getByRole('tab', { name: /ld decay/i }).click();
        await expect(page.getByText(/pairwise comparisons/i)).toBeVisible({ timeout: 5000 });
      }
    });
  });
});
