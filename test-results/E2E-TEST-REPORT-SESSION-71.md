# E2E Test Report — Session 71

**Date**: January 8, 2026  
**Session**: 71 - MAHAKALI SAHASRABHUJA  
**Test Framework**: Playwright  

---

## Summary

| Suite | Passed | Failed | Skipped | Total |
|-------|--------|--------|---------|-------|
| Smoke Tests (critical-paths) | 16 | 0 | 0 | 16 |
| CRUD Smoke Tests | 3 | 0 | 0 | 3 |
| Auth Tests | 12 | 0 | 0 | 12 |
| API Tests | 28 | 8 | 1 | 37 |
| **Total** | **59** | **8** | **1** | **68** |

**Pass Rate**: 86.8% (59/68)

---

## Fixes Applied This Session

### 1. Test User Password Update
**Issue**: Login credentials `Demo123!` and `Admin123!` were not matching database passwords.

**Root Cause**: Users were created with old passwords before Session 70 password policy changes. The seeder only creates users if they don't exist, so password updates weren't applied.

**Fix**: Created `backend/scripts/update_test_passwords.py` to update passwords directly in database.

### 2. CRUD Test Navigation Assertions
**Issue**: Tests expected toast messages that don't exist in the forms.

**Root Cause**: Forms navigate to detail pages on success, not back to list pages, and don't show toast messages.

**Fix**: Updated `frontend/e2e/tests/smoke/crud_smoke.spec.ts` to:
- Check for navigation away from `/new` page instead of toast messages
- Create prerequisite data (Program) before creating Trial
- Use `waitForFunction` for more reliable navigation detection

---

## Test Results by Suite

### ✅ Smoke Tests - Critical Paths (16/16 passed)

| Test | Status | Duration |
|------|--------|----------|
| should load login page | ✅ | 4.8s |
| should have no console errors on login page | ✅ | 5.0s |
| should complete login flow | ✅ | 5.1s |
| should load dashboard | ✅ | 7.6s |
| should navigate to programs page | ✅ | 8.1s |
| should navigate to trials page | ✅ | 7.9s |
| should navigate to germplasm page | ✅ | 7.8s |
| should navigate to locations page | ✅ | 7.7s |
| should navigate to traits page | ✅ | 5.4s |
| should load seed bank dashboard | ✅ | 5.0s |
| should load seed operations dashboard | ✅ | 6.4s |
| should load earth systems dashboard | ✅ | 6.9s |
| should load commercial dashboard | ✅ | 6.8s |
| should show 404 page for invalid route | ✅ | 6.7s |
| should be responsive on mobile viewport | ✅ | 6.1s |
| should be responsive on tablet viewport | ✅ | 4.7s |

### ✅ CRUD Smoke Tests (3/3 passed)

| Test | Status | Duration |
|------|--------|----------|
| should create a new Program successfully | ✅ | 3.9s |
| should create a new Trial successfully | ✅ | 6.4s |
| should create a new Location successfully | ✅ | 3.9s |

### ✅ Auth Tests (12/12 passed)

All authentication flow tests passing.

### ⚠️ API Tests (28/37 - 8 failed)

**Passing Tests**: Server info, common crop names, germplasm endpoints, observation variables, samples, variants, maps, seedlots, breeding methods, and most error handling.

**Failing Tests** (Known Issues):

| Test | Issue | Root Cause |
|------|-------|------------|
| should login with valid credentials | 429 Too Many Requests | Rate limiter triggered by previous test runs |
| should list programs | 401 Unauthorized | Auth token not properly set after rate limit |
| should support pagination | 401 Unauthorized | Same as above |
| should list trials | 401 Unauthorized | Same as above |
| should list studies | 401 Unauthorized | Same as above |
| should list locations | 401 Unauthorized | Same as above |
| should return 404 for non-existent resource | Returns 401 instead of 404 | Auth required before 404 check |
| should handle multiple rapid requests | All requests fail | Rate limiter blocks all requests |

**Recommendation**: API tests need rate limit reset between test runs. The `reset-rate-limit` endpoint is called in global setup but the API tests run in a different context.

---

## Files Modified

| File | Change |
|------|--------|
| `backend/scripts/update_test_passwords.py` | Created - Updates test user passwords |
| `frontend/e2e/tests/smoke/crud_smoke.spec.ts` | Fixed navigation assertions, added prerequisite creation |

---

## Known Issues (Not Fixed This Session)

1. **API Test Rate Limiting**: Tests that make authenticated requests fail due to rate limiting. Need to add rate limit reset within API test suite.

2. **BrAPI Endpoint Auth**: Some BrAPI endpoints return 401 when accessed without valid token, even for public data.

---

## Recommendations

1. **Add rate limit reset to API test beforeAll**: Each API test file should reset rate limits before running.

2. **Consider test isolation**: Run API tests with a dedicated test user to avoid rate limit conflicts.

3. **Update API tests for auth flow**: Ensure token is properly obtained and used across all API tests.

---

## Verification Commands

```bash
# Run smoke tests
cd frontend/e2e && npx playwright test tests/smoke/ --project=chromium

# Run all tests
cd frontend/e2e && npx playwright test --project=chromium

# View test report
cd frontend/e2e && npx playwright show-report
```

---

*Report generated: January 8, 2026*
