
import { test, expect } from '@playwright/test';

test.describe('Scientific Modules - Feature Toggle Verification', () => {
  // Use authenticated state
  test.use({ storageState: 'playwright/.auth/user.json' });

  test('GxE Interaction - Toggle Database Mode', async ({ page }) => {
    // Navigate to GxE Interaction page
    await page.goto('/gxe-interaction');

    // Wait for the main content to load
    await expect(page.getByRole('heading', { name: /G.E Interaction/i })).toBeVisible();

    // Locate the Data Source toggle (Label is dynamic, so use generic selector)
    const databaseToggle = page.getByRole('switch').first();
    await expect(databaseToggle).toBeVisible();

    // Expect it to be unchecked initially (Demo Mode)
    await expect(databaseToggle).not.toBeChecked();
    
    // Verify Demo Mode elements
    // The "Select Environment" text should NOT be present in Demo Mode
    await expect(page.getByText('Select Environment (Studies)')).not.toBeVisible();

    // Toggle to Database Mode
    await databaseToggle.click();
    await expect(databaseToggle).toBeChecked();

    // Verify Database Mode elements
    // "Environments / Studies" should now be visible
    await expect(page.getByText('Environments / Studies')).toBeVisible();
  });

  test('Breeding Value Calculator - Toggle Database Mode', async ({ page }) => {
    // Navigate to Breeding Value Calculator
    await page.goto('/breeding-value-calculator');

    // Wait for page load
    await expect(page.getByRole('heading', { name: /Breeding Value/i })).toBeVisible();

    // Locate the toggle
    const databaseToggle = page.getByRole('switch', { name: /Use Database Observations/i });
    await expect(databaseToggle).toBeVisible();

    // Ensure we are in Demo Mode
    if (await databaseToggle.isChecked()) {
        await databaseToggle.click();
    }
    await expect(databaseToggle).not.toBeChecked();

    // Verify Demo Mode Trait Selector (Use getByText as Label is not associated)
    await expect(page.getByText('Target Trait (Demo)')).toBeVisible();

    // Toggle to Database Mode
    await databaseToggle.click();

    // Verify Database Mode Elements
    await expect(page.getByText('Select Environment (Studies)')).toBeVisible();
    await expect(page.getByText('Target Trait (Variable)')).toBeVisible();
  });
});
