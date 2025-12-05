---
inclusion: always
---

# Bijmantra Development Steering Guide

## Project Overview

**Bijmantra** is a comprehensive platform for agricultural science, plant breeding, and future space-based research, built on the **Parashakti Framework**.

> **Full Technical Specification:** See `docs/framework/PARASHAKTI_SPECIFICATION.md`

### Core Vision

- **100% Open Source** — No proprietary dependencies
- **PWA-First** — Offline-capable, installable, field-ready
- **Modular Architecture** — 9 divisions that can evolve independently
- **Integration-First** — Connect to external systems, don't rebuild them
- **Multi-Engine Compute** — Python, Rust/WASM, Fortran for different workloads
- **Secure** — JWT auth, RBAC, multi-tenant isolation

### Guiding Principle

> **"Build tools that solve real problems, not encyclopedias that document everything."**

Every module must pass this test:
1. Does a breeder/researcher need this in their daily work?
2. Does it help make better decisions or save time?
3. Can we integrate with existing systems instead of rebuilding?

---

## Division Structure

| # | Division | Status | Description |
|---|----------|--------|-------------|
| 1 | Plant Sciences | Active | Breeding, genomics, crop sciences |
| 2 | Seed Bank | Active | Genetic resources, conservation |
| 3 | Earth Systems | Active | Climate, weather, GIS |
| 4 | Sun-Earth Systems | Visionary | Solar radiation, magnetic field |
| 5 | Sensor Networks | Conceptual | IoT, environmental monitoring |
| 6 | Commercial | Planned | Traceability, licensing, ERP integration |
| 7 | Space Research | Visionary | Interplanetary agriculture |
| 8 | Integration Hub | Active | Third-party API connections |
| 9 | Knowledge | Partial | Documentation, training |

Each division is lazy-loaded and can be enabled/disabled via feature flags.


---

## Technology Stack

### Frontend (React PWA)
- React 18+ with TypeScript 5+
- Vite 5+ (build tool)
- Tailwind CSS + shadcn/ui
- TanStack Query (server state)
- Zustand (client state)
- Dexie.js (IndexedDB for offline)
- Workbox (service worker)

### Backend (FastAPI)
- Python 3.11+
- FastAPI (REST framework)
- SQLAlchemy 2.0+ (ORM)
- Pydantic 2+ (validation)

### Compute Engines
- Python — API, ML inference
- Rust/WASM — Genomics, matrices
- Fortran — BLUP, REML, statistics

### Database
- PostgreSQL 15+ with PostGIS (spatial) and pgvector (AI embeddings)
- Redis (caching)
- MinIO (object storage)

### Infrastructure
- Podman (containers)
- Caddy (reverse proxy, auto HTTPS)

---

## Project Structure

```
bijmantra/
├── frontend/src/
│   ├── framework/           # Parashakti core (shell, registry, auth, sync)
│   ├── divisions/           # Division modules (lazy loaded)
│   │   ├── plant-sciences/
│   │   ├── seed-bank/
│   │   └── ...
│   └── shared/              # Shared components
├── backend/app/
│   ├── core/                # Framework core (auth, events, compute)
│   ├── modules/             # Division backends
│   │   ├── plant_sciences/
│   │   └── ...
│   └── integrations/        # External adapters (NCBI, ERPNext, etc.)
├── compute/
│   ├── rust/                # Rust/WASM modules
│   └── fortran/             # Fortran libraries
└── docs/framework/          # Parashakti specification
```

---

## Development Workflow

### Setup
```bash
git clone <repo> bijmantra && cd bijmantra
make install
make dev              # Start infrastructure
make dev-backend      # http://localhost:8000
make dev-frontend     # http://localhost:5173
```

### Common Commands
```bash
make dev              # Start infrastructure
make dev-backend      # Start FastAPI server
make dev-frontend     # Start React dev server
make test             # Run all tests
make db-migrate       # Run migrations
make db-revision      # Create new migration
```

---

## Code Standards

### Python (Backend)
- Linter/Formatter: Ruff
- Type hints required
- Google-style docstrings
- Async for I/O operations

### TypeScript (Frontend)
- ESLint + Prettier
- Strict TypeScript
- Functional components with hooks
- TanStack Query for server state

---

## Key Architectural Decisions

### BrAPI Compatibility
BrAPI v2.1 endpoints are exposed for interoperability with other breeding platforms. This is a compatibility feature, not the platform identity.

### Integration over Rebuilding
- ERP: Integrate with ERPNext, don't build one
- Bioinformatics: Link to NCBI/EMBL, don't rebuild
- Agrochemicals: Log applications, link to external DBs

### Multi-Engine Compute
| Task | Engine |
|------|--------|
| API, ML | Python |
| Genomics, matrices | Rust/WASM |
| BLUP, REML, stats | Fortran |

### Offline-First
- IndexedDB for local storage
- Sync queue for pending changes
- Service worker caching
- Conflict resolution (server wins default)

---

## Security

- JWT tokens (24h access, 7d refresh)
- RBAC with division-level permissions
- Multi-tenant isolation via organization_id
- Row-level security in PostgreSQL
- HTTPS only (Caddy auto-TLS)

---

## Git Workflow

### Commit Messages (Conventional)
```
feat: add program creation endpoint
fix: resolve offline sync race condition
docs: update API documentation
```

### Branch Naming
```
feature/seed-bank-division
fix/offline-sync-bug
docs/parashakti-spec
```

---

## Resources

- [Parashakti Specification](docs/framework/PARASHAKTI_SPECIFICATION.md)
- [FastAPI Documentation](https://fastapi.tiangolo.com)
- [React Documentation](https://react.dev)
- [PostgreSQL Documentation](https://www.postgresql.org/docs)
