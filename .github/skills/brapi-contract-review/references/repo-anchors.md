# BrAPI Contract Review Repo Anchors

Use these repo surfaces for BrAPI contract review.

- `backend/app/main.py`
  - BrAPI router mounting and `/brapi/v2/serverinfo`
- `backend/app/api/v2/core/router.py`
  - core BrAPI router composition
- `backend/app/api/brapi/router.py`
  - germplasm and phenotyping router composition
- `backend/app/api/brapi/genotyping_router.py`
  - genotyping router composition
- `backend/app/schemas/brapi/__init__.py`
  - canonical BrAPI `metadata` and `result` envelope types
- `backend/app/api/v2/core/trials.py`
  - representative typed BrAPI endpoint pattern
- `backend/app/api/v2/core/serverinfo.py`
  - declared BrAPI call inventory
- `backend/tests/integration/test_brapi_live.py`
  - end-to-end BrAPI behavior checks
- `backend/tests/test_smoke_api_v2.py`
  - route-level smoke coverage
- `.ai/decisions/ADR-005-api-contract-discipline.md`
  - accepted contract-discipline direction

Primary checks:

- `metadata` and `result` envelope consistency
- pagination keys: `currentPage`, `pageSize`, `totalCount`, `totalPages`
- BrAPI-style `*DbId` naming and aliasing
- clear distinction between official BrAPI endpoints and BijMantra extensions
- focused tests covering any changed contract behavior
