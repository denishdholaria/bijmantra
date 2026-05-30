# TOOLS.md - BijMantra Dev Environment

## Container Runtime

- **Runtime:** Podman at `/opt/homebrew/bin/podman`
- **Compose:** `podman compose` (via podman-compose)
- **Machine IP:** `192.168.127.2` (Podman VM on macOS)
- **Start everything:** `bash dev.sh --chloe`
- **Stop everything:** `bash dev.sh --stop`

## Services

| Service | Container | Port | Notes |
|---------|-----------|------|-------|
| PostgreSQL 16 | bijmantra-postgres | 5432 | TimescaleDB HA image, PostGIS + pgvector + 8 extensions |
| Redis 8 | bijmantra-redis | 6379 | Cache, optional via `--profile infra` |
| MinIO | bijmantra-minio | 9000/9001 | Object storage, optional |
| Meilisearch | bijmantra-meilisearch | 7700 | Search, optional |
| SurrealDB | beingbijmantra-surrealdb | 8083 | Project brain sidecar |
| Chloe Gateway | bijmantra-chloe-gateway | 18789 | OpenClaw agent runtime |
| Chloe Sandbox | bijmantra-chloe-sandbox | — | Tool sandbox |

## Database

- **Host:** localhost:5432
- **User:** bijmantra_user
- **Password:** (see `.env` — `POSTGRES_PASSWORD`)
- **Database:** bijmantra_db
- **Extensions:** timescaledb, vector, postgis, pg_trgm, uuid-ossp, pgcrypto, pgaudit, ltree
- **Connect from host:** `psql -h localhost -p 5432 -U bijmantra_user -d bijmantra_db`
- **Connect inside container:** `/opt/homebrew/bin/podman exec bijmantra-postgres psql -U bijmantra_user -d bijmantra_db`
- **Note:** Local homebrew postgres may conflict on port 5432. Stop it with `brew services stop postgresql@17` if needed.

## Package Managers

| Domain | Tool | Never use |
|--------|------|-----------|
| Python (backend) | `uv` | pip, pipx, conda |
| TypeScript (frontend) | `bun` | npm, yarn, pnpm |
| Containers | Podman | Docker-first assumptions |

## Backend

- **Location:** `backend/`
- **Python:** 3.13
- **Framework:** FastAPI
- **ORM:** SQLAlchemy 2.0 (async with asyncpg)
- **Migrations:** Alembic — `uv run alembic upgrade head`
- **Tests:** `uv run pytest` or `make test-backend`
- **Lint:** `uv run ruff check .`
- **Format:** `uv run ruff format .`
- **Install deps:** `uv sync --extra dev --extra analytics --extra geo`

## Frontend

- **Location:** `frontend/`
- **Framework:** React 19, TypeScript 6, Vite 8
- **Styling:** Tailwind CSS 4
- **Data fetching:** TanStack Query 5
- **Tests:** `bun run test` or `make test-frontend`
- **Install deps:** `bun install`
- **Dev server:** `bun run dev` (port 5656)

## Key Paths

| What | Where |
|------|-------|
| API endpoints | `backend/app/api/v2/` |
| SQLAlchemy models | `backend/app/models/` |
| Pydantic schemas | `backend/app/schemas/` |
| Domain modules | `backend/app/modules/` |
| Alembic migrations | `backend/alembic/versions/` |
| Frontend pages | `frontend/src/pages/` |
| Division modules | `frontend/src/divisions/` |
| Shared components | `frontend/src/components/` |
| API client | `frontend/src/lib/api-client.ts` |
| Metrics (source of truth) | `metrics.json` |
| Architecture trail | `.ai/decisions/`, `.ai/tasks/` |
| Agent definitions | `.github/agents/` |
| Path-scoped rules | `.github/instructions/` |
| Specialist workflows | `.github/skills/` |

## Useful Commands

```bash
# Full dev stack
bash dev.sh --chloe

# Backend only
bash dev.sh --minimal
cd backend && uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Run migrations
cd backend && uv run alembic upgrade head

# Create migration
cd backend && uv run alembic revision --autogenerate -m "description"

# Seed database
cd backend && uv run python -m app.db.seed --env=dev

# Check extension health
/opt/homebrew/bin/podman exec bijmantra-postgres psql -U bijmantra_user -d bijmantra_db -c "SELECT extname, extversion FROM pg_extension ORDER BY extname;"

# Verify container status
bash dev.sh --status
```

## Environment Variables

Key env vars are in `.env` at the repo root. Important ones:

- `POSTGRES_*` — database connection
- `SECRET_KEY` — JWT signing
- `INTEGRATION_ENCRYPTION_KEY` — pgcrypto credential encryption
- `MINIO_ROOT_USER` / `MINIO_ROOT_PASSWORD` — object storage
- `OPENCLAW_GATEWAY_TOKEN` — Chloe gateway auth
