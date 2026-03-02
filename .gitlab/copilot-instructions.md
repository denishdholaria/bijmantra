# BijMantra AI Coding Instructions

## Project Overview
BijMantra is a **cross-domain agricultural intelligence platform** implementing **BrAPI v2.1** (201/201 endpoints). The core thesis: *"No agricultural decision exists in a single domain"* — AI bridges genetics, agronomy, soil, climate, and economics.

**Version**: v1.0.0-alpha.1 Prathama | **State**: `.kiro/steering/STATE.md` | **Metrics**: `/metrics.json`

## Architecture

### Stack
- **Backend**: FastAPI (Python 3.11+), async PostgreSQL + PostGIS + pgvector, Redis, Meilisearch
- **Frontend**: React 18 + TypeScript + Vite, Zustand state, shadcn/ui, TanStack Query
- **Compute Engines**: Python (API/ML), Rust/WASM (genomics matrices), Fortran (BLUP/REML)
- **Container Runtime**: **Podman** (not Docker) — use `podman` commands

### Key Directories
```
backend/app/
├── api/v2/          # 100+ BrAPI endpoint modules
├── models/          # SQLAlchemy models (inherit from base.py)
├── schemas/         # Pydantic schemas (BrAPI-compliant responses)
├── core/            # config.py, security.py, database.py, rls.py
└── crud/            # Database operations

frontend/src/
├── pages/           # 248 page components (+ 106 in divisions/)
├── components/ui/   # shadcn/ui primitives
├── lib/api-client.ts # BrAPI HTTP client
├── store/           # Zustand stores (auth.ts, workspaceStore.ts)
└── wasm/            # Rust-compiled genomics modules
```

## Development Commands
```bash
make dev              # Start postgres, redis, minio (Podman)
make dev-backend      # uvicorn on :8000 (activate venv first)
make dev-frontend     # Vite on :5173
make test             # pytest (backend) + vitest (frontend)
make lint && make format  # Ruff (backend), ESLint/Prettier (frontend)
make db-migrate       # alembic upgrade head
```

## Critical Rules

### Zero Mock Data Policy
All data must come from database. Demo data is sandboxed in "Demo Organization" via seeders.
```python
# ✅ CORRECT — query database
result = await db.execute(select(Item))

# ❌ FORBIDDEN — hardcoded mock data
_store = [{"id": "1", "name": "Demo"}]
```

### Git Remote — MANDATORY
```bash
git push bijmantraorg main   # ONLY remote. All work goes here.
```
Never push to other remotes. See `.kiro/steering/operational-guardrails.md`.

### Confidential Files
These paths are filtered from public repo: `docs/gupt/`, `.env` files, credentials.

## Conventions & Patterns

### Backend API Endpoints
- All endpoints under `/brapi/v2/` prefix — follow BrAPI spec
- Response format: `{ metadata: {...}, result: {...} }` (single) or `result.data: [...]` (list)
- Auth: `Depends(get_current_user)` from `app/api/deps.py`
- New endpoints: create module in `backend/app/api/v2/`, register in router

### Frontend Pages
- Pattern: `{Entity}.tsx`, `{Entity}Form.tsx`, `{Entity}Detail.tsx` in `src/pages/`
- API: `apiClient` from `@/lib/api-client` handles auth + BrAPI parsing
- State: `useAuthStore` (auth), `useWorkspaceStore` (workspace context)
- UI: shadcn/ui from `@/components/ui/{component}`

### Database Models
- Inherit `BaseModel` from `app/models/base.py` (provides id, created_at, updated_at)
- Multi-tenant: `organization_id` column + Row-Level Security (RLS)
- Migrations: `alembic revision --autogenerate -m "description"`

### Testing
- Backend: pytest + `TestClient(app)` — see `tests/test_brapi_public.py`
- Frontend: Vitest (unit), Playwright (E2E in `frontend/e2e/`)
- E2E: `npm test` from `frontend/e2e/` or `make e2e` from root

## Domain-Specific

### Cross-Domain Integration
Modules must expose inputs/outputs for AI reasoning across domains. A breeding decision should surface soil constraints, climate risks, economic viability. See `.kiro/steering/cross-domain-philosophy.md`.

### Demo vs Production
- Demo Org: `demo@bijmantra.org` — sandboxed sample data
- Admin Org: `admin@bijmantra.org` — production data
- Check `user.is_demo` flag for conditional behavior

### Genomics WASM
```bash
cd rust && ./build.sh  # Outputs to frontend/src/wasm/
```
Heavy computations (GRM, GBLUP, LD) run client-side via Rust WASM.

### Metrics — Single Source of Truth
After work, update `/metrics.json`. All dashboards, README, API endpoints read from this file.

## AI Agent Protocols

### SWAYAM (Autonomous Mode)
```
SWAYAM              # Pick next priority from STATE.md
SWAYAM <feature>    # Develop specific feature
SWAYAM VERIFY       # Run builds/tests
```
Behavior: Check STATE.md → Execute → Update metrics.json → Verify build

### MAHAKALI (Parallel Deployment)
```
INVOKE MAHAKALI — [mission]   # Multi-stream parallel work
```
Streams: P0 (Critical) → P1 (Quality) → P2 (Docs) → P3 (Security)

## Module Requirements

New modules must include a declaration with:
- `primary_domain` / `secondary_domains` — Scientific scope
- `assumptions` — Explicit assumptions made
- `limitations` — Known constraints
- `uncertainty_handling` — How uncertainty is represented

Modules must expose inputs/outputs in domain-neutral format for AI agent interrogation. See `.kiro/steering/module-acceptance-criteria.md`.

## API Contract Philosophy

> **"Every API is a scientific conversation, not a function call."**

Cross-domain APIs must carry:
- **Context** — Domain scope and capability
- **Assumptions** — What the API assumes
- **Uncertainty** — Confidence bounds on outputs
- **Provenance** — Data source traceability

APIs returning raw values without meaning are invalid. See `.kiro/steering/api-contracts.md`.

## Code Quality
- Backend: Ruff (`pyproject.toml`)
- Frontend: ESLint + Prettier, strict TypeScript
- Import order: stdlib → third-party → local (`app/` or `@/`)
