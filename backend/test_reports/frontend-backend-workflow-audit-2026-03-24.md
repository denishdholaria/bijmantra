# Frontend, Backend, and Workflow Audit — 2026-03-24

## Scope

This audit exercised the repository's existing frontend, backend, and workflow validation surfaces to identify broken or missing pieces that block production readiness for the app's modules, submodules, and pages.

The audit was automated-first rather than manual page-by-page browsing:

- frontend unit/integration suite
- frontend production build
- frontend lint workflow bootstrap
- backend lint/bootstrap and pytest collection
- backend smoke tests for core and plant-sciences module routes
- GitHub Actions workflow inspection for recent CI state

## Commands Run

### Frontend

- `cd frontend && npm run test:run`
- `cd frontend && npm run build`
- `cd frontend && npm run lint`

### Backend

- `cd backend && . venv/bin/activate && pytest --collect-only`
- `cd backend && . venv/bin/activate && pytest tests/api/v2/test_core_router.py tests/modules/plant_sciences/test_router.py`
- `cd backend && . venv/bin/activate && ruff check .`

### CI / Workflow

- inspected recent workflow runs in `denishdholaria/bijmantraorg`
- reviewed `.github/workflows/api-registry-update.yml`
- reviewed `.github/workflows/sync-to-public.yml`

## What Passed

- Frontend test suite: `79` files, `392` tests passed
- Frontend production build now completes successfully
- Backend pytest collection succeeded: `3315` tests collected
- Focused backend smoke tests for core routes and the plant-sciences overview now pass

## Broken or Missing Pieces Found

### Fixed in this change

1. **Frontend lint workflow bootstrap was broken**
   - `npm run lint` failed before linting any files because ESLint 10 could not find a flat config file.
   - Fix: added `frontend/eslint.config.mjs` so the lint workflow boots correctly and reports real findings.

2. **Frontend production build failed when the optional genomics WASM bundle was absent**
   - The loader referenced `./pkg/bijmantra_genomics` in a way that Vite tried to resolve at build time.
   - Fix: moved the optional import behind a Vite-ignored runtime loader and added focused tests for available/missing bundle paths.

3. **Frontend production build exhausted Node's default heap**
   - After the WASM import issue was fixed, `npm run build` still died with a JavaScript heap OOM in this repository's current bundle size.
   - Fix: updated the frontend build scripts to run Vite with `--max-old-space-size=4096`.

4. **Backend core-router async tests were broken by httpx API drift**
   - `AsyncClient(app=app, ...)` no longer works on the installed httpx version.
   - Fix: updated the core-router tests to use `ASGITransport`.

5. **Backend core rate-limit status endpoint had stale enum and response wiring**
   - The route referenced `RateLimitType.API` and `rate_check.limit`, neither of which exists in the current rate limiter contract.
   - Fix: mapped `"api"` to `RateLimitType.API_GENERAL`, mapped `"export"` to `RateLimitType.API_WRITE`, and sourced the returned limit from `RATE_LIMITS`.

6. **Plant Sciences overview route was defined but not mounted**
   - The router existed at `backend/app/modules/plant_sciences/router.py`, but `app.main` did not include it, causing `/plant-sciences/` to return `404`.
   - Fix: mounted the plant-sciences router in `app.main`.

### Still present after this change

1. **Frontend lint debt remains high**
   - The lint command now runs, but it reports a large pre-existing backlog (`337` errors, `1925` warnings during this audit run).
   - This is repository debt, not a lint bootstrap issue anymore.

2. **Frontend bundle size remains heavy**
   - The build completes, but several chunks are still very large, including `blueprint-graph-react` at over `2 MB`.
   - This is a production-readiness concern for performance and caching, though not a build blocker after this change.

3. **Frontend dependency security debt remains**
   - `npm install` reported `12` vulnerabilities (`3 moderate`, `9 high`) in the current dependency tree.
   - These were not introduced by this change and should be addressed in a dependency-hardening follow-up.

4. **Backend lint debt remains**
   - `ruff check .` still fails immediately on pre-existing import ordering debt in untouched backend files.

5. **Backend test collection still emits warnings**
   - Notably:
     - a `datetime.utcnow()` deprecation warning in `app/modules/phenotyping/services/vision/model_service.py`
     - a pytest collection warning in `tests/units/isolated/test_parquet_schema_validator_isolated.py`

## CI / Workflow Notes

- Recent GitHub Actions history includes an `action_required` run for `Update API Registry`.
- Based on `.github/workflows/api-registry-update.yml`, that workflow comments on PRs when backend API files change without regenerating `docs/api/API_REGISTRY.md` and `docs/api/API_REGISTRY.json`.
- That workflow state is informational for API-surface changes and was not caused by this audit's frontend/build fixes.

## Production-Readiness Follow-Ups

1. Burn down the newly visible frontend lint backlog in prioritized slices.
2. Reduce the largest frontend chunks with additional route/component code splitting.
3. Audit and remediate the current npm vulnerability set.
4. Clean the existing backend Ruff violations.
5. Resolve backend warning debt (`datetime.utcnow()` and test-collection warnings).
