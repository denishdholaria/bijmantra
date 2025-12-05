# 🌱 Bijmantra - Agricultural Science Platform

A comprehensive Progressive Web Application for agricultural science, plant breeding, and future space-based research. Built on the **Parashakti Framework** — a modular, offline-first architecture designed to scale from individual researchers to global institutions.

**9 Divisions** | **Offline-First PWA** | **Multi-Engine Compute** | **BrAPI v2.1 Compatible**

![Bijmantra Dashboard](docs/images/Screenshot-2025-12-04.png)

---

## 🏗️ Architecture: Parashakti Framework

Bijmantra is built on the Parashakti Framework — a modular architecture where each division operates independently while sharing core infrastructure.

### Division Structure

| # | Division | Status | Description |
|---|----------|--------|-------------|
| 1 | **Plant Sciences** | Active | Breeding, genomics, crop sciences |
| 2 | **Seed Bank** | Active | Genetic resources, conservation |
| 3 | **Earth Systems** | Beta | Climate, weather, GIS |
| 4 | **Sun-Earth Systems** | Visionary | Solar radiation, magnetic field |
| 5 | **Sensor Networks** | Conceptual | IoT, environmental monitoring |
| 6 | **Commercial** | Planned | Traceability, licensing, ERP integration |
| 7 | **Space Research** | Visionary | Interplanetary agriculture |
| 8 | **Integration Hub** | Active | Third-party API connections |
| 9 | **Knowledge** | Partial | Documentation, training |

### Core Principles

- **100% Open Source** — No proprietary dependencies
- **PWA-First** — Offline-capable, installable, field-ready
- **Modular Architecture** — Divisions evolve independently
- **Integration-First** — Connect to external systems, don't rebuild them
- **Multi-Engine Compute** — Python, Rust/WASM, Fortran for different workloads

> **Full Technical Specification:** See [`docs/framework/PARASHAKTI_SPECIFICATION.md`](docs/framework/PARASHAKTI_SPECIFICATION.md)

---

## 🚧 Development Status

> **Active Development** — Many modules are functional but require testing. We welcome contributors!

**How to Contribute:**
- Test modules and report issues via [GitHub Issues](https://github.com/denishdholaria/bijmantra/issues)
- Share feedback and suggestions
- Submit pull requests

📧 **Contact:** [DenishDholaria@gmail.com](mailto:DenishDholaria@gmail.com)

---

## 🚫 Ethical Use Notice

> **IMPORTANT:** This software is PROHIBITED for use in developing Terminator seeds, GURTs, or any technology that restricts farmers' rights to save and replant seeds.

See [ETHICAL_USE_POLICY.md](ETHICAL_USE_POLICY.md) for complete terms.

---

## 🚀 Key Features

### Plant Sciences Division
- **Breeding Programs** — Multi-environment trials, studies, germplasm management
- **Genomics** — Genetic diversity, GBLUP, QTL mapping, genomic selection
- **Phenotyping** — Trait definitions, observations, data collection
- **Genotyping** — Sample management, variant analysis, allele matrices
- **Field Operations** — Trial design, field layout, harvest planning

### Seed Bank Division
- **Vault Management** — Base, active, and cryo storage monitoring
- **Accessions** — Germplasm registration with full passport data
- **Conservation** — Diversity analysis, safety duplication tracking
- **Viability Testing** — Germination test scheduling and tracking
- **Regeneration Planning** — Priority-based regeneration queue
- **Germplasm Exchange** — SMTA-compliant material transfer

### Compute Engines
| Task | Engine |
|------|--------|
| API, ML inference | Python |
| Genomics, matrices | Rust/WASM |
| BLUP, REML, statistics | Fortran |

### BrAPI v2.1 Compatibility
Full implementation for interoperability with other breeding platforms:
- Core Module (Programs, Trials, Studies, Locations)
- Germplasm Module (Germplasm, Pedigree, Crosses)
- Phenotyping Module (Observations, Traits, Events)
- Genotyping Module (Samples, Variants, Calls)

---

## 🔧 Tech Stack

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

### Database & Infrastructure
- PostgreSQL 15+ with PostGIS and pgvector
- Redis (caching)
- MinIO (object storage)
- Podman (containers)
- Caddy (reverse proxy, auto HTTPS)

---

## 🚀 Getting Started

### Prerequisites
- Docker/Podman
- Node.js 18+
- Python 3.11+

### Quick Start

```bash
# Clone the repository
git clone https://github.com/denishdholaria/bijmantra.git
cd bijmantra

# Start infrastructure
make dev

# Start backend (new terminal)
make dev-backend    # http://localhost:8000

# Start frontend (new terminal)
make dev-frontend   # http://localhost:5173
```

### Access Points
- **Frontend**: http://localhost:5173
- **API Docs**: http://localhost:8000/docs
- **BrAPI**: http://localhost:8000/brapi/v2

---

## 📁 Project Structure

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
│   │   ├── seed_bank/
│   │   └── ...
│   └── integrations/        # External adapters (NCBI, ERPNext, etc.)
├── rust/                    # Rust/WASM modules
├── fortran/                 # Fortran libraries
└── docs/framework/          # Parashakti specification
```

---

## 📜 License

**Bijmantra Open Source License with Attribution (BOSLA)**

This software is open source with mandatory attribution requirements.

**Required Attribution:**
```
Powered by Bijmantra - Created by Denish Dholaria / R.E.E.V.A.i
```

See [LICENSE](LICENSE) for full details.

---

## 👨‍💻 Developer

**R.E.E.V.A.i** — Rural Empowerment through Emerging Value-driven Agro-Intelligence

---

**ॐ श्री गणेशाय नमः** 🙏

*May Lord Ganesha remove all obstacles in the path of agricultural innovation*
