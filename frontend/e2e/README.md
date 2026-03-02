# BijMantra E2E Testing

Comprehensive End-to-End testing infrastructure using Playwright.

## Overview

This E2E test suite covers:
- **221 pages** - All application pages render correctly
- **Authentication** - Login, logout, session management
- **CRUD Operations** - Create, Read, Update, Delete for all entities
- **Accessibility** - WCAG 2.1 AA compliance
- **Visual Regression** - Screenshot comparisons
- **Performance** - Core Web Vitals, load times
- **API Testing** - Direct API endpoint validation

## Quick Start

```bash
# Install dependencies
npm install

# Install Playwright browsers
npx playwright install

# Run all tests
npm test

# Run specific test suites
npm run test:smoke        # Quick smoke tests
npm run test:auth         # Authentication tests
npm run test:crud         # CRUD operation tests
npm run test:pages        # Page render tests
npm run test:accessibility # Accessibility tests
npm run test:visual       # Visual regression tests
npm run test:performance  # Performance tests
npm run test:api          # API tests
```

## Test Structure

```
e2e/
├── playwright.config.ts    # Playwright configuration
├── package.json            # E2E dependencies
├── pages/                  # Page Object Models
│   ├── base.page.ts        # Base page class
│   ├── login.page.ts       # Login page
│   └── dashboard.page.ts   # Dashboard page
├── helpers/                # Test utilities
│   ├── navigation.helper.ts # Route definitions
│   ├── api.helper.ts       # API interactions
│   └── test-data.factory.ts # Test data generation
├── tests/
│   ├── fixtures/           # Custom test fixtures
│   ├── auth/               # Authentication tests
│   ├── smoke/              # Smoke tests
│   ├── pages/              # Page render tests
│   ├── crud/               # CRUD operation tests
│   ├── accessibility/      # Accessibility tests
│   ├── visual/             # Visual regression tests
│   ├── performance/        # Performance tests
│   └── api/                # API tests
└── playwright/
    └── .auth/              # Stored auth states
```

## Running Tests

### Interactive Mode
```bash
npm run test:ui           # Open Playwright UI
npm run test:headed       # Run with browser visible
npm run test:debug        # Debug mode
```

### By Browser
```bash
npm run test:chromium     # Chrome only
npm run test:firefox      # Firefox only
npm run test:webkit       # Safari only
npm run test:mobile       # Mobile browsers
```

### CI Mode
```bash
npm run test:ci           # CI-optimized run
```

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `E2E_BASE_URL` | `http://localhost:5173` | Frontend URL |
| `E2E_API_URL` | `http://localhost:8000` | Backend API URL |
| `E2E_TEST_EMAIL` | `demo@bijmantra.org` | Test user email |
| `E2E_TEST_PASSWORD` | `Demo123!` | Test user password |
| `E2E_ADMIN_EMAIL` | `admin@bijmantra.org` | Admin user email |
| `E2E_ADMIN_PASSWORD` | `Admin123!` | Admin user password |

### Test Timeouts

- Global timeout: 60 seconds
- Action timeout: 15 seconds
- Navigation timeout: 30 seconds
- Expect timeout: 10 seconds

## Writing Tests

### Using Page Objects

```typescript
import { test, expect } from '../fixtures/test-fixtures'
import { LoginPage } from '../pages/login.page'

test('should login successfully', async ({ page }) => {
  const loginPage = new LoginPage(page)
  await loginPage.navigate()
  await loginPage.loginAsDemo()
  await loginPage.verifySuccessfulLogin()
})
```

### Using Test Data Factory

```typescript
import { TestDataFactory } from '../helpers/test-data.factory'

const testData = new TestDataFactory()

test('should create program', async ({ page }) => {
  const programData = testData.program({
    programName: 'Custom Name',
  })
  // Use programData in test
})
```

### Using API Helper

```typescript
import { ApiHelper } from '../helpers/api.helper'

test('should create via API', async ({ request }) => {
  const api = new ApiHelper(request)
  await api.authenticate('demo@bijmantra.org', 'Demo123!')
  const program = await api.createProgram({ programName: 'Test' })
})
```

## Visual Regression

### Update Snapshots
```bash
npm run update-snapshots
```

### Compare Snapshots
Visual tests automatically compare against baseline screenshots stored in `__snapshots__/`.

## Accessibility Testing

Uses `@axe-core/playwright` for WCAG compliance testing:
- WCAG 2.0 Level A
- WCAG 2.0 Level AA
- WCAG 2.1 Level A
- WCAG 2.1 Level AA

## Performance Thresholds

| Metric | Threshold |
|--------|-----------|
| Page Load | < 5s |
| First Paint | < 2s |
| LCP | < 4s |
| FID | < 100ms |
| CLS | < 0.25 |

## Reports

After running tests:
```bash
npm run report            # Open HTML report
```

Reports are generated in:
- `playwright-report/` - HTML report
- `test-results/` - JSON and JUnit reports

## CI/CD Integration

Tests run automatically on:
- Push to `main` or `develop`
- Pull requests

See `.github/workflows/e2e-tests.yml` for configuration.

## Troubleshooting

### Tests failing to authenticate
1. Ensure backend is running on port 8000
2. Check test credentials are valid
3. Clear auth state: `rm -rf playwright/.auth/`

### Visual tests failing
1. Update snapshots if changes are intentional
2. Check viewport size consistency
3. Ensure fonts are loaded before screenshot

### Slow tests
1. Use `test.slow()` for known slow tests
2. Increase timeouts for specific tests
3. Check network conditions

## Best Practices

1. **Use Page Objects** - Encapsulate page interactions
2. **Use Test Data Factory** - Generate consistent test data
3. **Clean up test data** - Use `afterAll` hooks
4. **Avoid flaky selectors** - Use data-testid attributes
5. **Wait properly** - Use Playwright's auto-waiting
6. **Isolate tests** - Each test should be independent
