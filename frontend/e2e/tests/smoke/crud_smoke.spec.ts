/**
 * CRUD Operations Smoke Test
 * 
 * Automated detection of broken form submissions.
 * Run from frontend/e2e: npx playwright test tests/smoke/crud_smoke.spec.ts --project=chromium
 */

import { test, expect } from '@playwright/test';

test.describe('Plant Sciences - CRUD Operations Smoke Test', () => {
  
  // Use ADMIN auth state (not user.json which is demo user with no permissions)
  test.use({ storageState: 'playwright/.auth/admin.json' });

  test('should create a new Program successfully', async ({ page }) => {
    await page.goto('/programs');
    
    // The "New Program" button is actually an <a> tag styled as button
    await page.getByRole('link', { name: /New Program/i }).click();
    
    // Wait for form to appear
    await page.waitForURL('**/programs/new');
    
    // Fill Form using correct field IDs
    const programName = 'Auto Test Program ' + Date.now();
    await page.fill('#programName', programName);
    await page.fill('#abbreviation', 'ATP');
    await page.fill('#objective', 'Automated testing objective');
    
    // Submit - this IS a button
    await page.getByRole('button', { name: 'Create Program' }).click();
    
    // On success, the form navigates back to /programs list
    // Wait for navigation OR error message
    await Promise.race([
      page.waitForURL('**/programs', { timeout: 15000 }),
      page.waitForSelector('[role="alert"]', { timeout: 15000 }).then(() => {
        throw new Error('Form submission failed - error alert shown');
      }),
    ]);
    
    // Verify we're on the programs list page
    expect(page.url()).toContain('/programs');
    expect(page.url()).not.toContain('/new');
  });

  test('should create a new Trial successfully', async ({ page }) => {
    // First, ensure we have at least one program
    await page.goto('/programs');
    
    // Check if there are any programs
    const programLinks = page.locator('a[href^="/programs/"]').first();
    const hasPrograms = await programLinks.isVisible({ timeout: 5000 }).catch(() => false);
    
    if (!hasPrograms) {
      // Create a program first
      await page.getByRole('link', { name: /New Program/i }).click();
      await page.waitForURL('**/programs/new');
      await page.fill('#programName', 'Test Program for Trial ' + Date.now());
      await page.fill('#abbreviation', 'TPT');
      await page.getByRole('button', { name: 'Create Program' }).click();
      await page.waitForURL('**/programs', { timeout: 15000 });
    }
    
    // Now create the trial
    await page.goto('/trials');
    await page.getByRole('link', { name: /New Trial/i }).click();
    await page.waitForURL('**/trials/new');
    
    await page.fill('#trialName', 'Auto Test Trial ' + Date.now());
    
    // Trial requires a program - wait for programs to load and select the first one
    const programSelect = page.locator('#programDbId');
    await programSelect.waitFor({ state: 'visible' });
    await page.waitForTimeout(2000); // Wait for programs to load from API
    
    // Select the first non-empty option
    const options = await programSelect.locator('option').all();
    if (options.length > 1) {
      await programSelect.selectOption({ index: 1 });
    }
    
    await page.getByRole('button', { name: 'Create Trial' }).click();
    
    // Wait for navigation away from /new page or error
    await page.waitForFunction(
      () => !window.location.pathname.endsWith('/new'),
      { timeout: 15000 }
    ).catch(async () => {
      // Check if there's an error message
      const errorVisible = await page.locator('.bg-red-50, .bg-red-900\\/30').isVisible();
      if (errorVisible) {
        throw new Error('Trial creation failed - error message shown');
      }
      throw new Error('Trial creation timed out');
    });
    
    expect(page.url()).not.toContain('/new');
  });

  test('should create a new Location successfully', async ({ page }) => {
    await page.goto('/locations');
    await page.getByRole('link', { name: /New Location/i }).click();
    await page.waitForURL('**/locations/new');
    
    await page.fill('#locationName', 'Auto Test Loc ' + Date.now());
    
    // Optional: fill locationType if available
    const locationTypeSelect = page.locator('#locationType');
    if (await locationTypeSelect.isVisible()) {
      const options = await locationTypeSelect.locator('option').all();
      if (options.length > 1) {
        await locationTypeSelect.selectOption({ index: 1 });
      }
    }
    
    await page.getByRole('button', { name: 'Create Location' }).click();
    
    // Wait for navigation away from /new page or error
    await page.waitForFunction(
      () => !window.location.pathname.endsWith('/new'),
      { timeout: 15000 }
    ).catch(async () => {
      // Check if there's an error message
      const errorVisible = await page.locator('.bg-red-50, .bg-red-900\\/30').isVisible();
      if (errorVisible) {
        throw new Error('Location creation failed - error message shown');
      }
      throw new Error('Location creation timed out');
    });
    
    expect(page.url()).not.toContain('/new');
  });

});
