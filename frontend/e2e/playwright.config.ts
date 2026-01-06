/**
 * Playwright E2E Test Configuration
 * BijMantra Comprehensive Testing Infrastructure
 * 
 * Coverage: 221 pages, authentication flows, CRUD operations,
 * accessibility, visual regression, and performance testing
 */

import { defineConfig, devices } from '@playwright/test'

/**
 * Environment configuration
 */
const BASE_URL = process.env.E2E_BASE_URL || 'http://localhost:5173'
const API_URL = process.env.E2E_API_URL || 'http://localhost:8000'
const CI = !!process.env.CI

export default defineConfig({
  // Test directory
  testDir: './tests',
  
  // Test file patterns
  testMatch: '**/*.spec.ts',
  
  // Parallel execution
  fullyParallel: true,
  
  // Fail fast in CI
  forbidOnly: CI,
  
  // Retry configuration
  retries: CI ? 2 : 0,
  
  // Worker configuration
  workers: CI ? 4 : undefined,
  
  // Reporter configuration
  reporter: [
    ['html', { outputFolder: 'playwright-report', open: CI ? 'never' : 'on-failure' }],
    ['json', { outputFile: 'test-results/results.json' }],
    ['junit', { outputFile: 'test-results/junit.xml' }],
    CI ? ['github'] : ['list'],
  ],
  
  // Global timeout
  timeout: 60000,
  
  // Expect timeout
  expect: {
    timeout: 10000,
    toHaveScreenshot: {
      maxDiffPixels: 100,
      threshold: 0.2,
    },
  },
  
  // Shared settings for all projects
  use: {
    // Base URL
    baseURL: BASE_URL,
    
    // Tracing
    trace: CI ? 'on-first-retry' : 'retain-on-failure',
    
    // Screenshots
    screenshot: 'only-on-failure',
    
    // Video
    video: CI ? 'on-first-retry' : 'retain-on-failure',
    
    // Viewport
    viewport: { width: 1280, height: 720 },
    
    // Action timeout
    actionTimeout: 15000,
    
    // Navigation timeout
    navigationTimeout: 30000,
    
    // Ignore HTTPS errors (for local dev)
    ignoreHTTPSErrors: true,
    
    // Extra HTTP headers
    extraHTTPHeaders: {
      'Accept-Language': 'en-US,en;q=0.9',
    },
  },
  
  // Project configurations
  projects: [
    // Setup project - runs first to authenticate
    {
      name: 'setup',
      testMatch: /global\.setup\.ts/,
      teardown: 'teardown',
    },
    
    // Teardown project - runs last to cleanup
    {
      name: 'teardown',
      testMatch: /global\.teardown\.ts/,
    },
    
    // Desktop Chrome - Primary browser
    {
      name: 'chromium',
      use: {
        ...devices['Desktop Chrome'],
        storageState: 'playwright/.auth/user.json',
      },
      dependencies: ['setup'],
    },
    
    // Desktop Firefox
    {
      name: 'firefox',
      use: {
        ...devices['Desktop Firefox'],
        storageState: 'playwright/.auth/user.json',
      },
      dependencies: ['setup'],
    },
    
    // Desktop Safari
    {
      name: 'webkit',
      use: {
        ...devices['Desktop Safari'],
        storageState: 'playwright/.auth/user.json',
      },
      dependencies: ['setup'],
    },
    
    // Mobile Chrome
    {
      name: 'mobile-chrome',
      use: {
        ...devices['Pixel 5'],
        storageState: 'playwright/.auth/user.json',
      },
      dependencies: ['setup'],
    },
    
    // Mobile Safari
    {
      name: 'mobile-safari',
      use: {
        ...devices['iPhone 13'],
        storageState: 'playwright/.auth/user.json',
      },
      dependencies: ['setup'],
    },
    
    // Accessibility tests (separate project)
    {
      name: 'accessibility',
      testMatch: /accessibility\.spec\.ts/,
      use: {
        ...devices['Desktop Chrome'],
        storageState: 'playwright/.auth/user.json',
      },
      dependencies: ['setup'],
    },
    
    // Visual regression tests
    {
      name: 'visual',
      testMatch: /visual\.spec\.ts/,
      use: {
        ...devices['Desktop Chrome'],
        storageState: 'playwright/.auth/user.json',
      },
      dependencies: ['setup'],
    },
    
    // Performance tests
    {
      name: 'performance',
      testMatch: /performance\.spec\.ts/,
      use: {
        ...devices['Desktop Chrome'],
        storageState: 'playwright/.auth/user.json',
      },
      dependencies: ['setup'],
    },
    
    // API tests (no browser needed)
    {
      name: 'api',
      testMatch: /api\.spec\.ts/,
      use: {
        baseURL: API_URL,
      },
    },
  ],
  
  // Web server configuration
  webServer: [
    {
      command: 'npm run dev',
      url: BASE_URL,
      reuseExistingServer: !CI,
      timeout: 120000,
      cwd: '..',
    },
  ],
  
  // Output directory
  outputDir: 'test-results',
  
  // Preserve output on failure
  preserveOutput: 'failures-only',
  
  // Global setup/teardown
  globalSetup: require.resolve('./tests/global.setup.ts'),
  globalTeardown: require.resolve('./tests/global.teardown.ts'),
})
