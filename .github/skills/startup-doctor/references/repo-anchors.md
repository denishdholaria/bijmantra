# Startup Doctor Repo Anchors

Use these repo surfaces when diagnosing local startup failures.

- `Makefile`
  - `dev`, `dev-backend`, `dev-frontend`, `db-migrate`, `startup-doctor`, `migration-doctor`
- `start-bijmantra-app.sh`
  - main local startup sequence
- `start.sh`
  - compatibility wrapper for the main startup script
- `setup.sh`
  - first-time prerequisite and dependency setup
- `backend/start_dev.sh`
  - backend development server entrypoint
- `backend/app/main.py`
  - `/health` endpoint used for runtime health checks
- `compose.yaml`
  - health checks and core infra service definitions

Typical failure buckets:

- missing container runtime or wrong runtime expectations
- missing backend virtualenv or frontend dependencies
- infrastructure services not running
- backend health unavailable on port `8000`
- frontend dev server unavailable on port `5173`
- migration issues hidden behind generic startup failures
