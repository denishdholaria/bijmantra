# Debugging Report: Internal Server Errors (RLS)

## Issue

Users reported an `Internal Server Error` (500) when creating a new Program.

## Root Cause Analysis

The application has Row Level Security (RLS) enabled on core tables (Programs, Trials, etc.) but the API endpoints fail to set the required session context.

- **DB Policy**: Requires `app.current_organization_id` to be set.
- **Code**: `backend/app/api/v2/core/programs.py` was directly calling CRUD methods without initializing this context.
- **Result**: Database rejected the INSERT, causing a crash.

## Fix

Applied a patch to `backend/app/api/v2/core/programs.py` to inject the context:

```python
from app.core.rls import set_tenant_context
# ...
await set_tenant_context(db, current_user.organization_id, current_user.is_superuser)
```

## Status

- **Programs**: Fix applied. Requires Server Restart (process crashed during reload).
- **Other Endpoints**: Likely broken (Trials, Studies, Locations, Seasons).

## Automated Detection Strategy

We have implemented a new E2E test suite `frontend/e2e/tests/smoke/crud_smoke.spec.ts` that:

1.  Logs in as Admin.
2.  Navigates to each creation form.
3.  Fills and Submits data.
4.  Asserts success or flags failure.

Run this test to identify all remaining broken endpoints:

```bash
npx playwright test tests/smoke/crud_smoke.spec.ts
```
