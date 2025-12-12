# 🌱 Bijmantra - Agricultural Science Platform

A comprehensive Progressive Web Application for agricultural science, plant breeding, and future space-based research. Built on the **Parashakti Framework** — a modular, offline-first architecture designed to scale from individual researchers to global institutions.

**285+ Pages** | **611 API Endpoints** | **11 Modules** | **Offline-First PWA** | **Multi-Engine Compute** | **BrAPI v2.1 Compatible**

![Bijmantra Dashboard](docs/images/Screenshot-2025-12-11.png)


---

## ⚠️ Development Status Notice

**This application is in active development.** While the UI is extensive, not all pages are fully functional:

| Status | Count | Description |
|--------|-------|-------------|
| ✅ Functional | 99 pages | Connected to real backend APIs |
| 🟡 Demo Data | 70 pages | UI works with mock/demo data |
| 🔴 UI Only | 8 pages | Visual mockups, no backend |

**See [FUNCTIONALITY_AUDIT.md](docs/FUNCTIONALITY_AUDIT.md) for detailed page-by-page status.**

---

## ✅ Current Status (December 12, 2025)

| Metric | Status |
|--------|--------|
| Pages | 295+ (177 audited) |
| API Endpoints | 611 |
| BrAPI v2.1 Coverage | 74/135 (55%) |
| Components | 174+ |
| TypeScript | 0 errors |
| Tests | 48 passing |
| Build | ✅ Verified (5.4MB) |

> **Note:** BrAPI compliance is partial. See [BRAPI_AUDIT.md](docs/BRAPI_AUDIT.md) for details.

---

## 🏗️ Architecture: Parashakti Framework

Bijmantra is built on the Parashakti Framework — a modular architecture where each module operates independently while sharing core infrastructure.

### Module Structure

| # | Module | Status | Description |
|---|--------|--------|-------------|
| 1 | **Plant Sciences** | Active | Breeding, genomics, phenotyping, analysis tools (9 subgroups) |
| 2 | **Seed Bank** | Active | Genetic resources, conservation, MCPD exchange |
| 3 | **Earth Systems** | Active | Climate, weather, GIS, field environment |
| 4 | **Sun-Earth Systems** | Active | Solar radiation, photoperiod, UV index |
| 5 | **Sensor Networks** | Active | IoT, environmental monitoring, alerts |
| 6 | **Commercial** | Active | Traceability, licensing, DUS testing |
| 7 | **Space Research** | Active | Interplanetary agriculture, life support |
| 8 | **Tools** | Active | Utilities, reports, AI assistant |
| 9 | **Settings** | Active | Configuration, users, admin |
| 10 | **Knowledge** | Active | Documentation, training, forums |
| 11 | **Home** | Active | Dashboard, insights, analytics |

### Core Principles

- **Open Source** — Source available, free for non-commercial use (see LICENSE)
- **PWA-First** — Offline-capable, installable, field-ready
- **Modular Architecture** — Modules evolve independently
- **Integration-First** — Connect to external systems, don't rebuild them
- **Multi-Engine Compute** — Python, Rust/WASM, Fortran for different workloads

> **Full Technical Specification:** See [`docs/framework/PARASHAKTI_SPECIFICATION.md`](docs/framework/PARASHAKTI_SPECIFICATION.md)

---

## 📜 License: BSAL v2.0

**Bijmantra Source Available License** — Free to Use, Pay to Sell

| Use Case | Cost |
|----------|------|
| Personal, educational, research | **Free** |
| Non-profit, government | **Free** |
| Internal organizational use | **Free** |
| Self-hosted deployments | **Free** |
| Farmer cooperatives | **Free** |
| Selling the software | **Commercial license required** |
| Paid SaaS/hosted service | **Commercial license required** |

See [LICENSE](LICENSE) and [COMMERCIAL_LICENSE.md](COMMERCIAL_LICENSE.md) for details.

## 🚫 Ethical Use Notice

> **ABSOLUTE PROHIBITION:** This software may NOT be used for Terminator seeds, GURTs, or any technology that restricts farmers' rights to save and replant seeds.

See [ETHICAL_USE_POLICY.md](ETHICAL_USE_POLICY.md) for complete terms.

---

## 🚀 Key Features

### 🪷 Veena AI Assistant
- Natural language queries for breeding data
- Voice commands ("Hey Veena")
- RAG-powered responses with pgvector
- Predictive analytics and recommendations

### Plant Sciences Module
- **Breeding** — Programs, trials, studies, germplasm, pipeline
- **Crossing** — Crosses, projects, planned crosses, progeny, pedigree
- **Selection** — Index, decision, parent selection, prediction, rankings
- **Phenotyping** — Traits, observations, units, events, images
- **Genotyping** — Samples, variants, allele matrix, plates, genome maps
- **Genomics** — Diversity, population genetics, GBLUP, QTL, MAS, G×E
- **Field Ops** — Layout, map, design, planning, harvest, nursery
- **Analysis** — Statistics, visualization, comparison, simulator
- **AI & Compute** — WASM tools, plant vision, yield predictor
- **Analysis Tools (NEW)** — Disease resistance, abiotic stress, bioinformatics, crop calendar, spatial analysis, pedigree analysis, phenotype analysis

### Seed Operations Module
- **Lab Testing** — Sample registration, testing workflow, certificates
- **Processing** — 10-stage batch processing, quality checks, yield tracking
- **Inventory** — Seed lots, warehouse management, stock alerts
- **Dispatch** — Order workflow, firm/dealer management, shipping
- **Traceability** — Chain of custody, QR codes, lineage tracking
- **Licensing** — Variety protection, license agreements, royalties

### Commercial Module
- **DUS Testing** — UPOV variety protection, 10 crop templates, character scoring
- **MCPD Exchange** — Genebank data exchange, CSV/JSON export/import

### AI & Vision Module (NEW)
- **Plant Vision Training Ground** — Custom model training, dataset management

### 🛡️ Security — ASHTA-STAMBHA (अष्ट-स्तम्भ)
Eight Pillars of Protection for mission-critical environments.

See [SECURITY.md](SECURITY.md) for security policy and vulnerability reporting.

### 🦀 High-Performance Genomics
| Tool | Description |
|------|-------------|
| Genomics Benchmark | High-performance benchmark dashboard |
| Genomic BLUP | Genomic BLUP calculator |
| Population Genetics | Diversity, Fst, PCA analysis |
| Linkage Disequilibrium | Linkage disequilibrium & HWE |
| Selection Index | Multi-trait selection calculator |

*Powered by WebAssembly for native-speed calculations*

### 🤖 AI Phenotyping
| Tool | Description |
|------|-------------|
| Plant Vision | Disease detection, growth stage, stress |
| Field Scanner | Real-time camera capture |
| Yield Predictor | AI-powered predictions |
| Crop Health | Trial-level monitoring |

### Compute Engines
| Task | Engine |
|------|--------|
| API, ML inference | Python |
| Genomics, matrices | Rust/WASM |
| BLUP, REML, statistics | Fortran |

### BrAPI v2.1 Compatibility (55%)

| Module | Coverage | Status |
|--------|----------|--------|
| Core | 81% | Programs, Trials, Studies, Locations, Seasons, People |
| Phenotyping | 69% | Observations, Variables, Traits, Events, Images |
| Germplasm | 62% | Germplasm, Crosses, Seed Lots |
| Genotyping | 26% | Samples, basic Variants |

**Missing:** Search endpoints, Lists, Calls, CallSets, References, VariantSets. See [BRAPI_AUDIT.md](docs/BRAPI_AUDIT.md).

---

## 🔧 Tech Stack

### Frontend (React PWA)
- React 18 + TypeScript 5 + Vite 5
- Tailwind CSS + shadcn/ui
- TanStack Query + Zustand
- Dexie.js (IndexedDB) + Workbox

### Backend (FastAPI)
- Python 3.11+ + FastAPI
- SQLAlchemy 2.0 async + Pydantic 2

### Database & Infrastructure
- PostgreSQL 15 + PostGIS + pgvector
- Redis + MinIO + Meilisearch
- Podman + Caddy

---

## 🚀 Getting Started

### Prerequisites
- Podman or Docker
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
│   ├── framework/           # Parashakti core (shell, registry)
│   ├── divisions/           # Module-specific pages (seed-operations, earth-systems, etc.)
│   ├── components/          # Shared components
│   ├── pages/               # 271+ page components
│   └── lib/                 # Utilities, API client
├── backend/app/
│   ├── api/v2/              # BrAPI v2.1 endpoints
│   ├── core/                # Auth, config, database
│   └── models/              # SQLAlchemy models
├── rust/                    # WASM modules
├── fortran/                 # HPC libraries
└── docs/                    # Documentation
```

---

## 📚 Documentation

| Document | Description |
|----------|-------------|
| [SECURITY.md](SECURITY.md) | Security policy & vulnerability reporting |
| [PROJECT_STATUS.md](PROJECT_STATUS.md) | Current status |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | Technical architecture |
| [docs/bijmantra-mindmap.mm.md](docs/bijmantra-mindmap.mm.md) | Visual architecture (Markmap) |
| [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) | Common issues |

---

## 🤝 Contributing

We welcome contributors!

- Test modules and report issues via [GitHub Issues](https://github.com/denishdholaria/bijmantra/issues)
- Share feedback and suggestions
- Submit pull requests

📧 **Contact:** [DenishDholaria@gmail.com](mailto:DenishDholaria@gmail.com)

---

## 📜 License

**Bijmantra Source Available License (BSAL) v2.0** — Free to Use, Pay to Sell

See [LICENSE](LICENSE) and [COMMERCIAL_LICENSE.md](COMMERCIAL_LICENSE.md) for full details.

---

## 🌟 Vision

**Bijmantra** — from Sanskrit "Bij" (बीज, seed) and "Mantra" (मन्त्र, sacred utterance).

A divine gift to plant breeders worldwide, empowering them to nurture the seeds of tomorrow. Built with reverence for the sacred work of those who feed the world.

---

## 👨‍💻 Developer

**R.E.E.V.A.i** — Rural Empowerment through Emerging Value-driven Agro-Intelligence

---

## 🙏 Gratitude

Dedicated to:
- Plant breeders feeding the world
- Open-source communities
- Divine inspiration guiding innovation

---

**ॐ श्री गणेशाय नमः** 🙏

*May Lord Ganesha remove all obstacles in the path of agricultural innovation*

**जय श्री गणेशाय नमो नमः!**
