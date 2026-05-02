# Workflow E2E Tests

This directory contains end-to-end tests for the three completed bounded workflows from the Titanium Path.

## Test Files

### 1. LD Analysis (`ld-analysis.spec.ts`)
- **Route**: `/wasm-ld`
- **Test Count**: 17 tests
- **Coverage**:
  - Page load and initial state
  - Empty state handling
  - Error state handling
  - Loading state during analysis
  - Successful analysis flow
  - Parameter adjustment
  - WebAssembly integration

### 2. Phenomic Upload (`phenomic-upload.spec.ts`)
- **Route**: `/phenomic-upload`
- **Test Count**: 17 tests
- **Coverage**:
  - Page load and initial state (4 tests)
  - File selection (3 tests)
  - Error state handling (3 tests)
  - Loading state (2 tests)
  - Success state (3 tests)
  - Tenant safety (2 tests)
  - Platform selection (2 tests)

### 3. Trial Creation (`trial-creation.spec.ts`)
- **Route**: `/trials/new`
- **Test Count**: 28 tests
- **Coverage**:
  - Page load and initial state (5 tests)
  - Form input and validation (8 tests)
  - Form submission and loading state (2 tests)
  - Success state (4 tests)
  - Error state handling (3 tests)
  - Form cancellation (2 tests)
  - Tenant safety (3 tests)
  - Complete workflow (1 test)

## Test Patterns

All workflow tests follow a consistent pattern:

1. **Page Load and Initial State**: Verify the page loads correctly and displays all expected UI elements
2. **Empty State**: Test the initial state before any user interaction
3. **Loading State**: Verify loading indicators during async operations
4. **Success State**: Test successful completion of the workflow
5. **Error State**: Test error handling and recovery
6. **Tenant Safety**: Verify tenant isolation and data security

## Running Tests

```bash
# Run all workflow tests
bun run test tests/workflows/

# Run specific workflow test
bun run test tests/workflows/phenomic-upload.spec.ts
bun run test tests/workflows/trial-creation.spec.ts
bun run test tests/workflows/ld-analysis.spec.ts

# Run with UI
bun run test:ui tests/workflows/

# Run in headed mode
bun run test:headed tests/workflows/
```

## Test Requirements

These tests validate:
- **FR-5**: Add E2E test coverage for the 3 completed bounded workflows (LD Analysis, Phenomic Upload, Trial Creation)
- **AC-5**: E2E tests exist and pass for LD Analysis, Phenomic Upload, and Trial Creation workflows

## Key Features Tested

### Phenomic Upload
- File selection via drag-drop or file picker
- File validation and error handling
- Upload progress tracking
- Upload receipt with job details
- Platform selection (NIRS, Hyperspectral, RGB, Multispectral, Other)
- Optional metadata (dataset name, crop)
- Tenant-safe data handling

### Trial Creation
- Form validation (required vs optional fields)
- Date range selection
- Trial type and crop specification
- Success state with navigation options
- Error recovery
- Form cancellation
- Tenant-safe trial creation

## Authentication

All tests use authenticated sessions via `navigateAuthenticated()` helper, which:
- Injects auth state into localStorage
- Handles Zustand persist hydration timing
- Retries navigation if auth fails to hydrate
- Ensures tenant context is maintained

## Tenant Safety

Both new workflows include tenant safety tests that verify:
- Tenant context is maintained during operations
- Data is scoped to the current tenant
- No data leakage from other tenants
- Proper tenant isolation at the UI level

## Notes

- Tests are designed to be resilient to timing issues
- Loading states may be very brief in development
- Some tests check for success OR error states (both are valid outcomes)
- Tenant safety is enforced at both UI and API levels
