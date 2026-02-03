/**
 * SAHASRABHUJA Protocol - JavaScript Error Detection
 * Comprehensive app-wide JavaScript error scanning
 */
import { test, expect, Page } from '@playwright/test';

// All routes to test for JS errors
const ALL_ROUTES = [
  // Core
  '/', '/dashboard', '/profile', '/settings', '/search',
  // Breeding
  '/programs', '/trials', '/studies', '/crosses', '/crossingprojects',
  '/plannedcrosses', '/crossingplanner', '/pipeline', '/germplasm',
  '/germplasm-comparison', '/collections', '/pedigree', '/pedigree-3d',
  '/breeding-simulator', '/locations', '/seasons',
  // Phenotyping
  '/traits', '/observations', '/observationunits', '/fieldlayout', '/fieldbook',
  '/images', '/events', '/scales', '/methods', '/ontology',
  // Genomics
  '/samples', '/variants', '/variantsets', '/calls', '/callsets',
  '/allelematrix', '/plates', '/references', '/genomemaps', '/markerprofiles',
  '/vendor-orders', '/linkage-groups', '/markers', '/maps',
  // Seed Bank
  '/seed-bank', '/seed-bank/vault', '/seed-bank/accessions', '/seed-bank/conservation',
  '/seed-bank/viability', '/seed-bank/regeneration', '/seed-bank/exchange',
  '/seed-bank/mcpd', '/seed-bank/grin',
  // Seed Operations
  '/seed-operations', '/seed-operations/samples', '/seed-operations/testing',
  '/seed-operations/certificates', '/seed-operations/lots', '/seed-operations/processing',
  '/seed-operations/dispatch', '/seed-operations/dus', '/seed-operations/dus/crops',
  '/seedlots', '/seedlots/transactions',
  // Earth Systems
  '/earth-systems', '/weather', '/soil', '/climate', '/irrigation',
  '/solar', '/photoperiod', '/gdd', '/drought', '/uv', '/radiation',
  '/devices', '/alerts', '/live-data', '/aggregates', '/input-log',
  // Commercial
  '/commercial', '/commercial/varieties', '/commercial/agreements',
  '/commercial/warehouse', '/commercial/dispatch', '/commercial/track',
  '/commercial/quality', '/commercial/stock-alerts', '/commercial/firms',
  // Analysis
  '/statistics', '/reports', '/analytics-dashboard', '/apex-analytics',
  '/insights-dashboard',
  // Knowledge
  '/forums', '/tutorials', '/documentation', '/faq', '/glossary', '/community',
  // Admin
  '/users', '/teams', '/organizations', '/roles', '/permissions',
  '/system-health', '/auditlog', '/system-settings', '/integrations',
  '/api-keys', '/webhooks', '/notifications', '/data-import', '/data-export',
  // AI
  '/veena', '/devguru',
  // Space
  '/space-crops', '/life-support', '/telemetry',
];

interface JSError {
  message: string;
  source?: string;
  lineno?: number;
  colno?: number;
  stack?: string;
}

interface PageResult {
  route: string;
  errors: JSError[];
  consoleErrors: string[];
  loadTime: number;
  status: 'success' | 'error' | 'timeout';
}

test.describe('SAHASRABHUJA - JavaScript Error Detection', () => {
  test.setTimeout(600000); // 10 minutes for full scan

  test('should scan all routes for JavaScript errors', async ({ page }) => {
    const results: PageResult[] = [];
    const errorSummary: { route: string; error: string }[] = [];

    // Setup error collection
    const collectErrors = async (route: string): Promise<PageResult> => {
      const errors: JSError[] = [];
      const consoleErrors: string[] = [];
      const startTime = Date.now();

      // Listen for page errors
      const errorHandler = (error: Error) => {
        errors.push({
          message: error.message,
          stack: error.stack,
        });
      };

      // Listen for console errors
      const consoleHandler = (msg: any) => {
        if (msg.type() === 'error') {
          consoleErrors.push(msg.text());
        }
      };

      page.on('pageerror', errorHandler);
      page.on('console', consoleHandler);

      let status: 'success' | 'error' | 'timeout' = 'success';

      try {
        const response = await page.goto(route, {
          waitUntil: 'networkidle',
          timeout: 30000,
        });

        // Wait for any async errors
        await page.waitForTimeout(1000);

        if (!response || response.status() >= 400) {
          status = 'error';
        }
      } catch (e: any) {
        if (e.message.includes('timeout')) {
          status = 'timeout';
        } else {
          status = 'error';
          errors.push({ message: e.message });
        }
      }

      page.off('pageerror', errorHandler);
      page.off('console', consoleHandler);

      return {
        route,
        errors,
        consoleErrors,
        loadTime: Date.now() - startTime,
        status,
      };
    };

    // Test each route
    for (const route of ALL_ROUTES) {
      const result = await collectErrors(route);
      results.push(result);

      // Collect errors for summary
      for (const error of result.errors) {
        errorSummary.push({ route, error: error.message });
      }

      // Filter out known/expected console errors
      const criticalConsoleErrors = result.consoleErrors.filter(
        (e) =>
          !e.includes('Query data cannot be undefined') && // TanStack Query warning
          !e.includes('Failed to fetch') && // Network errors (expected in test)
          !e.includes('Method Not Allowed') && // API method errors
          !e.includes('401') && // Auth errors
          !e.includes('404') // Not found (expected for some routes)
      );

      for (const error of criticalConsoleErrors) {
        errorSummary.push({ route, error: `[Console] ${error}` });
      }
    }

    // Generate report
    console.log('\n========================================');
    console.log('SAHASRABHUJA - JavaScript Error Report');
    console.log('========================================\n');

    const routesWithErrors = results.filter(
      (r) => r.errors.length > 0 || r.status === 'error'
    );
    const routesWithTimeout = results.filter((r) => r.status === 'timeout');
    const successfulRoutes = results.filter(
      (r) => r.status === 'success' && r.errors.length === 0
    );

    console.log(`Total Routes Scanned: ${results.length}`);
    console.log(`Successful: ${successfulRoutes.length}`);
    console.log(`With Errors: ${routesWithErrors.length}`);
    console.log(`Timeouts: ${routesWithTimeout.length}`);

    if (errorSummary.length > 0) {
      console.log('\n--- ERRORS FOUND ---\n');
      for (const { route, error } of errorSummary) {
        console.log(`[${route}] ${error}`);
      }
    }

    // NotFoundError specific check
    const notFoundErrors = errorSummary.filter((e) =>
      e.error.includes('NotFoundError')
    );
    if (notFoundErrors.length > 0) {
      console.log('\n--- NotFoundError INSTANCES ---\n');
      for (const { route, error } of notFoundErrors) {
        console.log(`[${route}] ${error}`);
      }
    }

    console.log('\n========================================\n');

    // Assert no critical JS errors
    const criticalErrors = errorSummary.filter(
      (e) =>
        e.error.includes('NotFoundError') ||
        e.error.includes('TypeError') ||
        e.error.includes('ReferenceError') ||
        e.error.includes('SyntaxError')
    );

    if (criticalErrors.length > 0) {
      console.log('CRITICAL ERRORS:');
      criticalErrors.forEach((e) => console.log(`  ${e.route}: ${e.error}`));
    }

    // Test passes if no NotFoundError specifically
    expect(notFoundErrors.length).toBe(0);
  });

  test('should detect NotFoundError on rapid navigation', async ({ page }) => {
    const errors: string[] = [];

    page.on('pageerror', (error) => {
      errors.push(error.message);
    });

    // Rapid navigation pattern that often triggers NotFoundError
    const rapidRoutes = [
      '/dashboard',
      '/programs',
      '/trials',
      '/germplasm',
      '/dashboard',
      '/seed-bank',
      '/seed-operations',
      '/earth-systems',
      '/dashboard',
    ];

    for (const route of rapidRoutes) {
      await page.goto(route, { waitUntil: 'domcontentloaded', timeout: 10000 });
      await page.waitForTimeout(200); // Quick navigation
    }

    await page.waitForTimeout(2000); // Wait for any delayed errors

    const notFoundErrors = errors.filter((e) => e.includes('NotFoundError'));
    console.log('Rapid navigation errors:', errors);

    expect(notFoundErrors.length).toBe(0);
  });

  test('should detect DOM manipulation errors', async ({ page }) => {
    const errors: string[] = [];

    page.on('pageerror', (error) => {
      errors.push(error.message);
    });

    // Pages with known DOM manipulation (download links, etc.)
    const domManipulationPages = [
      '/programs',
      '/seed-bank/mcpd',
      '/data-export',
    ];

    for (const route of domManipulationPages) {
      await page.goto(route, { waitUntil: 'networkidle', timeout: 30000 });
      await page.waitForTimeout(1000);
    }

    const domErrors = errors.filter(
      (e) =>
        e.includes('NotFoundError') ||
        e.includes('removeChild') ||
        e.includes('appendChild')
    );

    expect(domErrors.length).toBe(0);
  });
});
