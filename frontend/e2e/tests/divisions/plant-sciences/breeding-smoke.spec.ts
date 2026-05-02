import { test, expect } from "../../../tests/fixtures/test-fixtures";

/**
 * Plant Sciences - Breeding Operations Smoke Tests
 *
 * Verifies that key pages load and primary action buttons are functional.
 * This answers the requirement: "details of all buttons in app working/not working".
 */

test.describe("Plant Sciences - Breeding Operations", () => {
  const pages = [
    {
      name: "Programs",
      path: "/plant-sciences/programs",
      buttonText: "New Program",
      buttonId: "new-program-btn",
    },
    {
      name: "Trials",
      path: "/plant-sciences/trials",
      buttonText: "New Trial",
      buttonId: "new-trial-btn",
    },
    {
      name: "Studies",
      path: "/plant-sciences/studies",
      buttonText: "New Study",
      buttonId: "new-study-btn",
    },
    {
      name: "Locations",
      path: "/plant-sciences/locations",
      buttonText: "New Location",
      buttonId: "new-location-btn",
    },
    {
      name: "Seasons",
      path: "/plant-sciences/seasons",
      buttonText: "New Season",
      buttonId: "new-season-btn",
    },
    {
      name: "Germplasm",
      path: "/plant-sciences/germplasm",
      buttonText: "Add Germplasm",
      buttonId: "add-germplasm-btn",
    },
  ];

  for (const pageInfo of pages) {
    test(`should load ${pageInfo.name} page and show create button`, async ({
      authenticatedPage,
    }) => {
      const page = authenticatedPage;

      // Navigate
      await page.goto(pageInfo.path);
      await page.waitForLoadState("networkidle");

      // Check URL
      expect(page.url()).toContain(pageInfo.path);

      // Check Page Title (approximate selector)
      await expect(page.locator("h1, h2, .page-title").first()).toBeVisible();

      // Check Primary Button
      // We search by text first as IDs might not be consistent yet
      const button = page.locator(
        `button:has-text("${pageInfo.buttonText}"), a:has-text("${pageInfo.buttonText}")`
      );

      const isVisible = await button.isVisible();

      // Report Status
      console.log(`[${pageInfo.name}] Page Load: COMPLETED`);
      console.log(
        `[${pageInfo.name}] Button "${pageInfo.buttonText}": ${isVisible ? "VISIBLE" : "MISSING"}`
      );

      if (isVisible) {
        const isEnabled = await button.isEnabled();
        console.log(
          `[${pageInfo.name}] Button State: ${isEnabled ? "ENABLED" : "DISABLED"}`
        );
        expect(isEnabled).toBe(true);
      } else {
        // Soft assertion failure to keep testing other pages?
        // Playwright fails the test, which is fine.
        // We'll catch this in the global report.
        throw new Error(
          `Button "${pageInfo.buttonText}" is missing on ${pageInfo.name} page`
        );
      }
    });
  }
});
