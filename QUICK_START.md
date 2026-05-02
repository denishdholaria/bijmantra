# Bijmantra Quick Start Guide

Get up and running with Bijmantra in 5 minutes.

🌐 **Website:** [bijmantra.org](https://bijmantra.org)  
📦 **Version:** Preview

---

## 🚀 One-Command Setup

> **Docker users**: BijMantra uses **Podman** instead of Docker. Commands are identical — just use `podman` instead of `docker`. [Why Podman?](docs/ARCHITECTURE.md#container-runtime-podman)

```bash
./setup.sh
```

This will:
- Start PostgreSQL by default (via Podman)
- Leave Redis, MinIO, and Meilisearch available as opt-in services for features that need them
- Install backend dependencies via uv
- Run database migrations
- Seed demo data
- Install frontend dependencies
- Build HPC compute modules (if prerequisites available)

---

## 🏃 Start Development

### Option 1: Using Make (Recommended)

```bash
# Terminal 1: Start infrastructure
make dev

# Optional only when needed
make dev-redis
make dev-minio
make dev-meilisearch
# or: make dev-all

# Terminal 2: Start backend
make dev-backend

# Terminal 3: Start frontend
make dev-frontend
```

`make dev-backend` now prints the active local database authority before REEVU starts so you can confirm it is not silently binding to the wrong PostgreSQL database.

### Optional: Being Bijmantra Sidecar

The main BijMantra app does not require the Being Bijmantra project-brain sidecar.

Start it only when you are working on the developer-facing `beingbijmantra` memory and bootstrap flows:

```bash
make dev-beingbijmantra

cd backend
uv run python scripts/bootstrap_project_brain_surreal_schema.py
uv run python scripts/bootstrap_project_brain_surreal.py
```

The dedicated sidecar listens on `http://127.0.0.1:8083` by default and remains separate from the core app stack.

### Optional: Mem0 Platform And CLI

If you want BijMantra and your local Mem0 CLI to share the same API key, use the repo-local `.env` flow.

1. Create `.env` from the root template if you do not already have one.
2. Set `MEM0_ENABLED=true` and `MEM0_API_KEY=<your key>`.
3. If you use Mem0 project scoping, set both `MEM0_ORG_ID` and `MEM0_PROJECT_ID`. Leave both blank otherwise.
4. Restart the backend after changing `.env` so BijMantra reloads the Mem0 settings.

Example:

```bash
cp .env.example .env

# Edit .env and set:
# MEM0_ENABLED=true
# MEM0_API_KEY=m0-...
```

Install the repo-local Mem0 CLI once from the repository root:

```bash
bun add -d @mem0/cli
```

The repo wrapper reads `.env` and forwards the connection settings to the repo-local `mem0` CLI:

```bash
./scripts/mem0-cli.sh status
./scripts/mem0-cli.sh add "Testing BijMantra memory" --user-id bijmantra-dev
./scripts/mem0-cli.sh search "What am I testing?" --user-id bijmantra-dev -o json
```

You can also use the Makefile shortcut for connectivity checks:

```bash
make mem0-status
```

If you prefer Mem0's interactive wizard, you can still run:

```bash
./scripts/mem0-cli.sh init
```

### Option 2: Single main-app launcher

```bash
bash ./start-bijmantra-app.sh
```

This starts the main BijMantra app stack only. The private OpenClaw runtime is separate and should be started with `ops-private/claw-runtime/scripts/bjm-start.sh` when needed.

### Option 3: Manual

```bash
# Terminal 1: Start infrastructure
/opt/podman/bin/podman compose up -d postgres

# Terminal 2: Backend
cd backend
bash ./start_dev.sh

# Terminal 3: Frontend
cd frontend
bun run dev
```

To verify REEVU's active database authority after startup as a superuser:

```bash
curl -H "Authorization: Bearer <token>" http://localhost:8000/api/v2/chat/diagnostics | jq '.database_authority'
```

---

## 🌐 Access Points

| Service | URL | Description |
|---------|-----|-------------|
| Frontend | http://localhost:5173 | React PWA (253 pages in current metrics) |
| Backend API | http://localhost:8000 | FastAPI server (1,965 endpoints in current metrics) |
| API Docs | http://localhost:8000/docs | Swagger UI |
| ReDoc | http://localhost:8000/redoc | Alternative docs |
| BrAPI | http://localhost:8000/brapi/v2 | 201 official BrAPI v2.1 operations, 248 currently exposed locally |
| PostgreSQL | localhost:5432 | Database (TimescaleDB + PostGIS + pgvector + 5 more extensions) |
| Redis | localhost:6379 | Optional cache service |
| MinIO Console | http://localhost:9001 | Optional object storage |
| Meilisearch | http://localhost:7700 | Optional search service |

---

## 🔑 Default Credentials

### Application
Create your first user account after setup:
```bash
# Run the user creation script
make create-user
# Or manually via API after starting the server
```

### MinIO (Development Only)
- **Username**: Set via `MINIO_ROOT_USER` environment variable
- **Password**: Set via `MINIO_ROOT_PASSWORD` environment variable

### pgcrypto (Integration Credentials Encryption)
- **Variable**: `INTEGRATION_ENCRYPTION_KEY`
- Set this in `.env` to enable database-level encryption for integration API keys.
- If not set, the integration hub service will warn but continue to function.

⚠️ **All credentials must be set via environment variables in production!**

---

## 🧪 Test the API

```bash
cd backend
uv run python test_api.py
```

This will test:
- Root endpoint
- Health check
- BrAPI serverinfo
- Authentication
- Program CRUD operations

---

## 📚 Common Commands

### Backend

```bash
# Install / sync dependencies (uv manages .venv automatically)
cd backend && uv sync --extra dev --extra analytics --extra geo

# Run migrations
uv run alembic upgrade head

# Create new migration
uv run alembic revision --autogenerate -m "description"

# Seed database
uv run python -m app.db.seed --env=dev

# Clear seeded data
uv run python -m app.db.seed --clear

# List available seeders
uv run python -m app.db.seed --list

# Run tests
uv run pytest

# Lint code
uv run ruff check .

# Format code
uv run ruff format .
```

### Frontend

```bash
cd frontend

# Install dependencies
bun install

# Start dev server
bun run dev

# Build for production
bun run build

# Run tests
bun run test

# Lint code
bun run lint
```

### Infrastructure (Podman)

```bash
# Start infrastructure services
make dev

# Start optional services only when needed
make dev-redis
make dev-minio
make dev-meilisearch
make dev-beingbijmantra

# Stop the optional Being Bijmantra sidecar
make dev-beingbijmantra-down

# Stop all services
make stop

# View logs
make logs

# Show running containers
make ps

# Reset database (⚠️ destroys data)
make db-reset

# Show service URLs
make info

# Start Podman machine (macOS)
make machine-start
```

---

## 🗂️ Project Structure

```
bijmantra/
├── backend/              # FastAPI backend
│   ├── app/
│   │   ├── api/         # API endpoints (v2, brapi)
│   │   ├── modules/     # Domain modules (breeding, genomics, etc.)
│   │   ├── core/        # Config, database, security
│   │   ├── models/      # SQLAlchemy models (110)
│   │   ├── services/    # Business logic
│   │   ├── control_plane/ # Developer control plane
│   │   ├── startup/     # App initialization
│   │   ├── db/seeders/  # Database seeders (15)
│   │   └── main.py      # FastAPI app
│   ├── alembic/         # Database migrations (31)
│   └── pyproject.toml   # uv/PEP 621 dependencies
│
├── frontend/            # React 19 PWA
│   ├── src/
│   │   ├── components/  # React components
│   │   ├── divisions/   # Domain module pages
│   │   ├── features/    # Feature modules (ai-chat, auth)
│   │   ├── framework/   # Shell, registry, routing
│   │   ├── pages/       # Global pages
│   │   ├── hooks/       # Custom hooks
│   │   ├── store/       # Zustand stores
│   │   └── App.tsx
│   └── package.json
│
├── fortran/             # HPC compute kernels (BLUP, GBLUP)
├── rust/                # Rust FFI + WASM genomics
├── docker/              # Container configs
├── compose.yaml         # Podman Compose config
├── compose.dev.yaml     # Development overrides
├── compose.prod.yaml    # Production config
├── Caddyfile            # Reverse proxy config
├── Makefile             # Development commands
├── setup.sh             # Setup script
└── metrics.json         # Project metrics (single source of truth)
```

---

## 🔧 Troubleshooting

### Podman machine not running (macOS)

```bash
# Start Podman machine
make machine-start
# or: /opt/podman/bin/podman machine start

# Check status
make machine-status
```

### Backend won't start

```bash
# Check if PostgreSQL is running
make ps

# Check logs
/opt/podman/bin/podman logs bijmantra-postgres

# Restart containers
/opt/podman/bin/podman start bijmantra-postgres bijmantra-redis bijmantra-minio
```

### Port already in use

```bash
# Find process using port 8000
lsof -i :8000

# Kill process
kill -9 <PID>
```

### Database connection error

```bash
# Restart PostgreSQL
/opt/podman/bin/podman restart bijmantra-postgres

# Check connection
/opt/podman/bin/podman exec -it bijmantra-postgres psql -U bijmantra_user -d bijmantra_db
```

### Module not found errors

```bash
# Backend — uv manages the venv automatically
cd backend
uv sync --extra dev --extra analytics --extra geo

# Frontend
cd frontend
rm -rf node_modules
bun install
```

---

## 📖 Next Steps

1. **Explore the API**: Visit http://localhost:8000/docs
2. **Read the docs**: Check `docs/` folder
3. **Review contributor workflow**: See `AGENTS.md`, `.github/docs/ai/2026-03-30-ai-operator-quickstart.md`, and `CONTRIBUTING.md`
4. **Check metrics**: See `metrics.json` for current stats
5. **Start coding**: Follow the active repo workflow in `.github/copilot-instructions.md` and the nearest `.github/instructions/` file
6. **If startup or migrations block**: Run `make startup-doctor` or `make migration-doctor`

---

## 🆘 Getting Help

- **Documentation**: See `docs/` folder
- **Issues**: GitHub Issues
- **Discussions**: GitHub Discussions
- **Code of Conduct**: See `CODE_OF_CONDUCT.md`

---

## 🎯 What's Implemented (preview-1)

### Backend ✅ (1,965 API Endpoints In Current Metrics)

| Module | Endpoints | Description |
|--------|-----------|-------------|
| BrAPI v2.1 | 201 published, 248 exposed locally | Official published operations plus BijMantra-local `/brapi/v2` exposure |
| Breeding | 120 | Programs, trials, crossing, selection, pedigree |
| Phenotyping | 85 | Observations, traits, field operations |
| Genomics | 107 | Genotyping, GWAS, QTL, molecular breeding |
| Seed Bank | 59 | Vaults, accessions, conservation, MTA |
| Environment | 97 | Weather, climate, soil, sensors |
| Seed Operations | 96 | Quality, processing, DUS testing |
| Knowledge | 35 | Forums, training |
| Settings & Admin | 95 | Users, teams, integrations |

### Frontend ✅ (253 Pages, 236 Functional)

| Module | Pages | Status |
|--------|-------|--------|
| Breeding | 35 | ✅ Functional |
| Phenotyping | 25 | ✅ Functional |
| Genomics | 35 | ✅ Functional |
| Seed Bank | 15 | ✅ Functional |
| Environment | 20 | ✅ Functional |
| Seed Operations | 22 | ✅ Functional |
| Knowledge | 5 | ✅ Functional |
| Settings & Admin | 35 | ✅ Functional |

> **Note:** 2 pages (ApexAnalytics, InsightsDashboard) are classified as Experimental — APIs exist but return demo data.

### Key Features
- 🔐 JWT Authentication with RBAC
- 🌐 All 201 official BrAPI v2.1 operations published
- 📱 PWA with low-connectivity field capture
- 🤖 Veena AI Assistant (RAG + Voice)
- 🧬 WASM Genomics (browser-side)
- 🔬 HPC Compute (Fortran BLUP/GBLUP)
- 🗄️ Multi-tenant architecture
- 🎨 Prakruti Design System

---

## 📝 Example API Calls

### Login

```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=YOUR_EMAIL&password=YOUR_PASSWORD"
```

### List Programs

```bash
curl -X GET http://localhost:8000/brapi/v2/programs \
  -H "Authorization: Bearer <your-token>"
```

### Create Program

```bash
curl -X POST http://localhost:8000/brapi/v2/programs \
  -H "Authorization: Bearer <your-token>" \
  -H "Content-Type: application/json" \
  -d '{
    "programName": "My Breeding Program",
    "abbreviation": "MBP",
    "objective": "Improve crop yield"
  }'
```

### Check Metrics

```bash
curl http://localhost:8000/api/v2/metrics/summary
```

---

## 🏗️ Tech Stack

| Layer | Technologies |
|-------|--------------|
| Frontend | React 19, TypeScript 6, Vite 8, Tailwind CSS 4, TanStack Query 5 |
| Backend | Python 3.13, FastAPI, SQLAlchemy 2.0, Pydantic 2 |
| Package Managers | uv (backend, Rust-based), Bun (frontend) |
| Database | PostgreSQL 16 (TimescaleDB HA) + PostGIS + pgvector + pgcrypto + pgaudit + ltree, Redis 8 |
| Compute | Rust/WASM, Fortran |
| Container | Podman (rootless, daemonless) |

---

**Happy Coding!** 🌱
