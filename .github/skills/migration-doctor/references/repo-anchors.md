# Migration Doctor Repo Anchors

Use these repo surfaces when diagnosing Alembic and schema-drift issues.

- `Makefile`
  - `db-migrate`, `db-reset`, `migration-doctor`
- `backend/alembic/versions/`
  - canonical local revision chain
- `backend/run_migrations.py`
  - direct migration runner
- `backend/app/scripts/auto_migration_checker.py`
  - detects model changes without migration updates
- `backend/scripts/system_health_check.py`
  - existing schema-sync check via `alembic check`
- `backend/start_dev.sh`
  - local backend env defaults
- `start-bijmantra-app.sh`
  - startup migration call path

Common issue categories:

- missing local parent revision in `backend/alembic/versions/`
- duplicate or branched local heads
- database points to a revision id that does not exist locally
- database schema is behind head or ahead of current code
