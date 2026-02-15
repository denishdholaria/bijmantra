import { test, expect } from '@playwright/test';
import fs from 'fs';
import path from 'path';

// Load routes
const routesPath = path.join(__dirname, '../all_routes.json');
const routes = JSON.parse(fs.readFileSync(routesPath, 'utf-8'));

test.describe('🪸 Great Barrier Reef - Full UI Audit', () => {

  // Login once before all tests (reuse verify global setup usually, but doing explicit here for safety)
  test.beforeEach(async ({ page }) => {
    // Modify this if you rely on storageState in config
    // If using storageState from global setup, you can skip this.
    // Assuming 'storageState: "playwright/.auth/user.json"' is active in config.
  });

  for (const route of routes) {
    test(`Check Route: ${route}`, async ({ page }) => {
      console.log(`🌊 Visiting: ${route}`);

      // 1. Navigate
      // Handle base URL in config usually, ensure route starts with /
      await page.goto(route);

      // 2. Wait for Load
      // Wait for network to settle or specific element
      try {
        await page.waitForLoadState('networkidle', { timeout: 10000 });
      } catch (e) {
        console.warn(`⚠️ Network still busy on ${route}, proceeding to check UI...`);
      }

      // 3. Check for White Screen of Death (WSOD)
      // Main content area should be present. Adjust selector to your layout (e.g. 'main', '#root', '.app')
      // Use .first() to avoid strict mode violation if both main and #root are present
      const mainContent = page.locator('main, #root').first();
      await expect(mainContent).toBeVisible();

      // Ensure it's not empty height (common WSOD symptom)
      const box = await mainContent.boundingBox();
      expect(box?.height).toBeGreaterThan(50);

      // Check for common error boundaries
      const errorText = page.getByText(/Something went wrong|Application Error|Minified React error/i);
      await expect(errorText).not.toBeVisible();

      // 4. Evidence: Screenshot
      // Sanitize filename
      const safeName = route.replace(/\//g, '_').replace(/[:?]/g, '-');
      await page.screenshot({
        path: `test-results/great_barrier_reef/screenshot${safeName}.png`,
        fullPage: true
      });
    });
  }
});
