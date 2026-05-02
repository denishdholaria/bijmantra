import { test, expect } from "./fixtures/test-fixtures";

test.describe("Calculators", () => {

  test.describe("Trait Calculator", () => {
    test.beforeEach(async ({ authenticatedPage }) => {
      // Mock Formulas
      await authenticatedPage.route('**/api/v2/ontology/formulas', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            formulas: [
              {
                id: '1',
                name: 'Test Formula',
                category: 'Test Category',
                formula: 'A + B',
                inputs: [
                  { name: 'Input A', unit: 'kg' },
                  { name: 'Input B', unit: 'kg' }
                ],
                output: { name: 'Result', unit: 'kg' }
              }
            ]
          })
        });
      });

      // Mock Calculate
      await authenticatedPage.route('**/api/v2/ontology/formulas/calculate', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            result: 100,
            unit: 'kg'
          })
        });
      });
    });

    test("should calculate result using formula", async ({ authenticatedPage }) => {
      const page = authenticatedPage;
      await page.goto('/calculator');

      // Wait for formula to load
      await expect(page.getByRole('button', { name: 'Test Formula' })).toBeVisible();

      // Click on formula
      await page.getByRole('button', { name: 'Test Formula' }).click();

      // Enter inputs
      await page.locator('input[type="number"]').first().fill('50');
      await page.locator('input[type="number"]').nth(1).fill('50');

      // Click Calculate
      await page.getByRole('button', { name: 'Calculate' }).click();

      // Verify Result
      await expect(page.locator('.text-3xl').getByText('100.00')).toBeVisible();
      await expect(page.getByText('Result')).toBeVisible();

      // Verify History
      await expect(page.getByText('Test Formula').last()).toBeVisible();
      await expect(page.getByText('= 100.00')).toBeVisible();
    });
  });

  test.describe("Selection Index Calculator", () => {
    test.beforeEach(async ({ authenticatedPage }) => {
      // Mock Methods
      await authenticatedPage.route('**/api/v2/selection/methods', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(['Smith-Hazel', 'Desired Gains'])
        });
      });

      // Mock Default Weights
      await authenticatedPage.route('**/api/v2/selection/default-weights', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({})
        });
      });

      // Mock Smith-Hazel Calculation
      await authenticatedPage.route('**/api/v2/selection/smith-hazel', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            index_coefficients: { 'Yield': 0.5, 'Protein': 0.5 },
            expected_response: { 'Yield': 10, 'Protein': 5 },
            accuracy: 0.8,
            message: 'Calculation success'
          })
        });
      });
    });

    test("should calculate selection index", async ({ authenticatedPage }) => {
      const page = authenticatedPage;
      await page.goto('/selection-index-calculator');

      // Verify Title
      await expect(page.getByText('Selection Index Calculator')).toBeVisible();

      // Check for default traits (Yield, Protein)
      await expect(page.locator('input[value="Yield"]')).toBeVisible();
      await expect(page.locator('input[value="Protein"]')).toBeVisible();

      // Click Calculate
      await page.getByRole('button', { name: 'Calculate Index' }).click();

      // Verify Results
      // Use first() because "Smith-Hazel" appears in Tab, Table, and Result Badge
      await expect(page.getByText('Smith-Hazel', { exact: true }).last()).toBeVisible();
      await expect(page.getByText('80.0%')).toBeVisible(); // Accuracy 0.8 * 100
      await expect(page.getByText('Index Coefficients (b)')).toBeVisible();
    });
  });

  test.describe("Genetic Gain Calculator", () => {
    test("should update genetic gain calculation", async ({ authenticatedPage }) => {
      const page = authenticatedPage;
      await page.goto('/genetic-gain-calculator');

      // Initial check (Default values: i=1.76, h2=0.35, sp=12.5, L=4)
      // Gain = (1.76 * 0.35 * 12.5) / 4 = 1.925 => 1.93
      await expect(page.getByText('1.93').first()).toBeVisible();

      // Change Selection Intensity (Top 5% -> i=2.06)
      await page.getByText('Top 5% selected').click();

      // New Gain = (2.06 * 0.35 * 12.5) / 4 = 2.253 => 2.25
      await page.waitForTimeout(200); // Wait for calculation to update
      await expect(page.getByText('2.25').first()).toBeVisible();
    });
  });

  test.describe("Breeding Value Calculator", () => {
    test.beforeEach(async ({ authenticatedPage }) => {
      const mockIndividuals = [
        { id: 'IND001', name: 'Plant 1', ebv: 10.5, accuracy: 0.6 },
        { id: 'IND002', name: 'Plant 2', ebv: 8.2, accuracy: 0.5 },
        { id: 'IND003', name: 'Plant 3', ebv: 12.1, accuracy: 0.7 }
      ];

      // Mock Individuals
      await authenticatedPage.route('**/api/v2/breeding-value/individuals*', async (route) => {
         await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ data: mockIndividuals })
        });
      });

      // Mock BLUP
      await authenticatedPage.route('**/api/v2/breeding-value/blup', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            individuals: mockIndividuals,
            heritability: 0.45,
            genetic_variance: 20.5,
            residual_variance: 15.2
          })
        });
      });

      // Mock Cross Prediction
      await authenticatedPage.route('**/api/v2/breeding-value/predict-cross', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            parent1: 'IND001',
            parent2: 'IND003',
            predicted_mean: 11.3,
            predicted_variance: 5.2,
            probability_superior: 0.75
          })
        });
      });
    });

    test("should run BLUP and predict cross", async ({ authenticatedPage }) => {
      const page = authenticatedPage;
      await page.goto('/breeding-value-calculator');

      // Verify Table Loaded
      await expect(page.getByText('Plant 1')).toBeVisible();
      await expect(page.getByText('Plant 3')).toBeVisible();

      // Run BLUP
      await page.getByRole('button', { name: 'Run BLUP' }).click();
      await expect(page.getByText('0.450')).toBeVisible(); // Heritability

      // Predict Cross
      await page.getByRole('tab', { name: 'Predict Cross' }).click();

      // Select Parents (using generic locators as IDs might not be present on SelectTrigger)
      // Parent 1
      await page.locator('button[role="combobox"]').first().click();
      await page.getByRole('option', { name: 'Plant 1' }).click();

      // Parent 2
      await page.locator('button[role="combobox"]').nth(1).click();
      await page.getByRole('option', { name: 'Plant 3' }).click();

      await page.getByRole('button', { name: 'Predict Cross' }).click();

      // Verify Prediction
      await expect(page.getByText('11.30').first()).toBeVisible();
      await expect(page.getByText('75%').first()).toBeVisible();
    });
  });

});
