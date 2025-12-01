# Bijmantra - Plant Breeding PWA Tech Stack

**Bijmantra** is a BrAPI v2.1-compatible Progressive Web Application (PWA) for plant breeding data management, field data collection, and breeding program operations.

---

## 🧠 Core Principles

- **100% Open Source** - No proprietary dependencies
- **PWA-First** - Offline-capable, installable, mobile-friendly
- **BrAPI v2.1 Compliant** - Full implementation of all 4 modules
- **Field-Ready** - Optimized for offline data collection in remote locations
- **AI-Friendly** - Clean architecture suitable for AI-assisted development
- **Scalable** - From single researcher to large breeding programs
- **Cross-Platform** - Works on desktop, tablet, and mobile devices

---

## 🧱 Complete Tech Stack

### **Frontend (PWA)**

| Technology               | Version | Purpose                                                      |
| ------------------------ | ------- | ------------------------------------------------------------ |
| **React**                | 18+     | UI framework - best ecosystem for data-heavy apps            |
| **TypeScript**           | 5+      | Type safety, better DX, BrAPI schema validation              |
| **Vite**                 | 5+      | Build tool - fast HMR, optimized production builds           |
| **Tailwind CSS**         | 3+      | Utility-first styling - rapid development, consistent design |
| **shadcn/ui**            | Latest  | Modern component library built on Radix UI                   |
| **TanStack Query**       | 5+      | Server state management, caching, offline sync               |
| **Zustand**              | 4+      | Lightweight local state management                           |
| **React Hook Form**      | 7+      | Performant form handling with validation                     |
| **Zod**                  | 3+      | Schema validation (can validate BrAPI schemas)               |
| **Vite PWA Plugin**      | Latest  | Service worker generation using Workbox                      |
| **Workbox**              | 7+      | Service worker strategies, offline caching                   |
| **IndexedDB + Dexie.js** | Latest  | Offline data storage, large dataset support                  |
| **Recharts**             | 2+      | Data visualization (phenotype distributions, trends)         |
| **TanStack Table**       | 8+      | Powerful data tables for breeding data                       |
| **Leaflet**              | 1.9+    | Maps for field locations and trial layouts                   |
| **date-fns**             | 3+      | Date manipulation and formatting                             |

### **Backend (BrAPI Server)**

| Technology           | Version | Purpose                                               |
| -------------------- | ------- | ----------------------------------------------------- |
| **Python**           | 3.11+   | Main backend language, scientific computing ecosystem |
| **FastAPI**          | 0.110+  | REST API framework, auto OpenAPI docs, async support  |
| **Pydantic**         | 2+      | Data validation, BrAPI schema models                  |
| **SQLAlchemy**       | 2.0+    | ORM for database operations                           |
| **Alembic**          | 1.13+   | Database migrations and versioning                    |
| **asyncpg**          | Latest  | Async PostgreSQL driver for performance               |
| **python-jose**      | Latest  | JWT token generation and validation                   |
| **passlib**          | Latest  | Password hashing (bcrypt)                             |
| **python-multipart** | Latest  | File upload support (plant images)                    |
| **Pillow**           | Latest  | Image processing for plant photos                     |
| **uvicorn**          | Latest  | ASGI server for FastAPI                               |
| **pytest**           | Latest  | Testing framework                                     |
| **httpx**            | Latest  | Async HTTP client for testing                         |

### **Database & Storage**

| Technology     | Version | Purpose                                                |
| -------------- | ------- | ------------------------------------------------------ |
| **PostgreSQL** | 15+     | Main relational database                               |
| **PostGIS**    | 3.3+    | Spatial extension for field locations, GPS coordinates |
| **Redis**      | 7+      | Caching, session storage, rate limiting                |
| **MinIO**      | Latest  | S3-compatible object storage for plant images          |

### **Containerization & Deployment**

| Technology         | Version | Purpose                                             |
| ------------------ | ------- | --------------------------------------------------- |
| **Podman**         | 5+      | Rootless container runtime (Docker alternative)     |
| **podman-compose** | Latest  | Multi-container orchestration                       |
| **Caddy**          | 2+      | Reverse proxy, automatic HTTPS, static file serving |

### **Development Tools**

| Technology     | Purpose                         |
| -------------- | ------------------------------- |
| **ESLint**     | JavaScript/TypeScript linting   |
| **Prettier**   | Code formatting                 |
| **Ruff**       | Python linting and formatting   |
| **Husky**      | Git hooks for pre-commit checks |
| **Commitizen** | Conventional commit messages    |

---

## 📦 Architecture Overview

### **System Architecture**

```
┌─────────────────────────────────────────────────────────────┐
│                     Client Devices                          │
│  (Desktop Browser / Tablet / Mobile Phone)                  │
│                                                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │         Bijmantra PWA (React + TypeScript)         │    │
│  │                                                      │    │
│  │  ├─ UI Components (shadcn/ui + Tailwind)           │    │
│  │  ├─ State Management (TanStack Query + Zustand)    │    │
│  │  ├─ Service Worker (Workbox)                       │    │
│  │  ├─ IndexedDB (Dexie.js) - Offline Storage         │    │
│  │  └─ BrAPI Client (Fetch + TanStack Query)          │    │
│  └────────────────────────────────────────────────────┘    │
└──────────────────────┬──────────────────────────────────────┘
                       │ HTTPS
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                    Caddy Reverse Proxy                      │
│                  (Automatic HTTPS + Routing)                │
│                                                              │
│  ┌──────────────┐              ┌──────────────┐            │
│  │  /api/*      │              │  /*          │            │
│  │  → Backend   │              │  → Frontend  │            │
│  └──────┬───────┘              └──────────────┘            │
└─────────┼──────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────┐
│              FastAPI Backend (BrAPI v2.1 Server)            │
│                                                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │  BrAPI v2.1 Endpoints                              │    │
│  │  ├─ Core Module (Programs, Trials, Studies)       │    │
│  │  ├─ Phenotyping (Observations, Variables)          │    │
│  │  ├─ Genotyping (Samples, Variants, Calls)          │    │
│  │  └─ Germplasm (Germplasm, Pedigree, Crosses)       │    │
│  └────────────────────────────────────────────────────┘    │
│                                                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │  Business Logic Layer                              │    │
│  │  ├─ Authentication & Authorization (JWT)           │    │
│  │  ├─ Data Validation (Pydantic)                     │    │
│  │  └─ File Processing (Images)                       │    │
│  └────────────────────────────────────────────────────┘    │
│                                                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │  Data Access Layer (SQLAlchemy)                    │    │
│  └────────────────────────────────────────────────────┘    │
└──────────────────────┬──────────────────────────────────────┘
                       │
          ┌────────────┼────────────┬──────────────┐
          ▼            ▼            ▼              ▼
    ┌──────────┐ ┌─────────┐ ┌─────────┐    ┌─────────┐
    │PostgreSQL│ │ PostGIS │ │  Redis  │    │  MinIO  │
    │          │ │         │ │ (Cache) │    │ (Images)│
    └──────────┘ └─────────┘ └─────────┘    └─────────┘
```

### **PWA Offline Strategy**

```
┌─────────────────────────────────────────────────────────────┐
│                    Service Worker (Workbox)                 │
│                                                              │
│  Cache Strategies:                                          │
│  ┌────────────────────────────────────────────────────┐    │
│  │ Static Assets (JS, CSS, Images)                    │    │
│  │ → Cache First (instant load)                       │    │
│  └────────────────────────────────────────────────────┘    │
│                                                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │ BrAPI Metadata (Traits, Methods, Scales)           │    │
│  │ → Stale While Revalidate (fast + fresh)            │    │
│  └────────────────────────────────────────────────────┘    │
│                                                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │ Observation Data                                    │    │
│  │ → Network First + Offline Queue                    │    │
│  └────────────────────────────────────────────────────┘    │
│                                                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │ Plant Images                                        │    │
│  │ → Cache First with Expiration (7 days)             │    │
│  └────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                 IndexedDB (Dexie.js)                        │
│                                                              │
│  Stores:                                                    │
│  ├─ observations (pending sync)                            │
│  ├─ traits (cached metadata)                               │
│  ├─ studies (cached data)                                  │
│  ├─ germplasm (cached data)                                │
│  └─ images (base64 blobs for offline)                      │
└─────────────────────────────────────────────────────────────┘
```

---

## 🗂️ BrAPI v2.1 Module Implementation

### **Core Module**

- Programs, Trials, Studies
- Locations (with PostGIS integration)
- People, Lists
- Search services

### **Phenotyping Module**

- Observation Units, Observations
- Observation Variables, Traits, Scales, Methods
- Images (stored in MinIO)
- Field data collection forms

### **Genotyping Module**

- Samples, Markers
- Variant Sets, Variants, Calls
- Call Sets, References
- Vendor Orders

### **Germplasm Module**

- Germplasm catalog
- Germplasm Attributes
- Seed Lots, Crosses
- Pedigree trees, Progeny

---

## 🎯 MVP Phase 1 Goals

### **Backend**

- [x] FastAPI project structure
- [ ] BrAPI Core endpoints (Programs, Trials, Studies, Locations)
- [ ] BrAPI Phenotyping endpoints (Observations, Variables)
- [ ] PostgreSQL + PostGIS database schema
- [ ] JWT authentication
- [ ] Image upload to MinIO
- [ ] Auto-generated OpenAPI documentation

### **Frontend**

- [ ] React + Vite + TypeScript setup
- [ ] PWA configuration with offline support
- [ ] Authentication UI (login, register)
- [ ] Dashboard (programs, trials overview)
- [ ] Field data collection form (offline-capable)
- [ ] Data tables with filtering and sorting
- [ ] Responsive design (mobile-first)

### **Deployment**

- [ ] Podman compose configuration
- [ ] Caddy reverse proxy setup
- [ ] Production build pipeline
- [ ] Database migrations

---

## 🚀 Future Enhancements (Phase 2+)

### **Advanced Features**

- [ ] Germplasm module (pedigree visualization)
- [ ] Genotyping module (variant analysis)
- [ ] Advanced analytics (statistical analysis, heritability)
- [ ] Multi-language support (i18n)
- [ ] Multi-tenant organization support
- [ ] Role-based access control (RBAC)

### **Performance & Scaling**

- [ ] Celery + Redis for background tasks
- [ ] GraphQL API (optional, alongside REST)
- [ ] Real-time updates (WebSockets)
- [ ] Horizontal scaling with load balancer
- [ ] CDN for static assets

### **Integrations**

- [ ] R integration for breeding analytics (rpy2)
- [ ] Python scientific libraries (NumPy, Pandas, SciPy)
- [ ] Export to Excel, CSV, JSON
- [ ] Import from other BrAPI servers
- [ ] Third-party BrAPI server sync

---

## 🏗️ Project Structure

```
bijmantra/
├── frontend/                      # React PWA
│   ├── public/
│   │   ├── manifest.json         # PWA manifest
│   │   ├── icons/                # App icons (various sizes)
│   │   └── robots.txt
│   ├── src/
│   │   ├── api/                  # BrAPI client
│   │   │   ├── client.ts         # Base fetch configuration
│   │   │   ├── core/             # Core module endpoints
│   │   │   ├── phenotyping/      # Phenotyping endpoints
│   │   │   ├── genotyping/       # Genotyping endpoints
│   │   │   └── germplasm/        # Germplasm endpoints
│   │   ├── components/           # React components
│   │   │   ├── ui/               # shadcn/ui components
│   │   │   ├── layout/           # Layout components
│   │   │   ├── forms/            # Form components
│   │   │   └── tables/           # Table components
│   │   ├── hooks/                # Custom React hooks
│   │   │   ├── useAuth.ts
│   │   │   ├── useBrAPI.ts
│   │   │   └── useOfflineSync.ts
│   │   ├── lib/                  # Utilities
│   │   │   ├── db.ts             # Dexie.js IndexedDB setup
│   │   │   ├── utils.ts
│   │   │   └── validators.ts
│   │   ├── pages/                # Page components
│   │   ├── store/                # Zustand stores
│   │   ├── types/                # TypeScript types (BrAPI schemas)
│   │   ├── App.tsx
│   │   ├── main.tsx
│   │   └── sw.ts                 # Service worker
│   ├── index.html
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   └── tailwind.config.js
│
├── backend/                       # FastAPI BrAPI Server
│   ├── app/
│   │   ├── api/
│   │   │   └── v2/               # BrAPI v2.1 endpoints
│   │   │       ├── core/
│   │   │       │   ├── programs.py
│   │   │       │   ├── trials.py
│   │   │       │   ├── studies.py
│   │   │       │   └── locations.py
│   │   │       ├── phenotyping/
│   │   │       │   ├── observations.py
│   │   │       │   ├── variables.py
│   │   │       │   └── images.py
│   │   │       ├── genotyping/
│   │   │       └── germplasm/
│   │   ├── core/
│   │   │   ├── config.py         # Settings
│   │   │   ├── security.py       # JWT, password hashing
│   │   │   └── database.py       # DB connection
│   │   ├── models/               # SQLAlchemy models
│   │   │   ├── core.py
│   │   │   ├── phenotyping.py
│   │   │   ├── genotyping.py
│   │   │   └── germplasm.py
│   │   ├── schemas/              # Pydantic schemas (BrAPI)
│   │   │   ├── core.py
│   │   │   ├── phenotyping.py
│   │   │   ├── genotyping.py
│   │   │   └── germplasm.py
│   │   ├── crud/                 # Database operations
│   │   ├── tests/
│   │   └── main.py               # FastAPI app entry point
│   ├── alembic/                  # Database migrations
│   ├── requirements.txt
│   ├── pyproject.toml
│   └── Containerfile             # Podman container definition
│
├── compose.yaml                   # Podman Compose configuration
├── Caddyfile                      # Caddy reverse proxy config
├── .env.example                   # Environment variables template
├── Makefile                       # Development commands
├── README.md
└── docs/
    ├── api/                       # API documentation
    ├── deployment/                # Deployment guides
    └── development/               # Development guides
```

---

## 🔧 Development Workflow

### **Initial Setup**

```bash
# Clone repository
git clone <repository-url> bijmantra
cd bijmantra

# Start infrastructure (PostgreSQL, Redis, MinIO)
podman-compose up -d postgres redis minio

# Backend setup
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload

# Frontend setup
cd ../frontend
npm install
npm run dev

# Access application
# Frontend: http://localhost:5173
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

### **Common Commands (Makefile)**

```bash
make dev          # Start all services in development mode
make test         # Run all tests
make lint         # Run linters
make format       # Format code
make build        # Build production containers
make deploy       # Deploy to production
```

---

## 📊 Database Schema Overview

### **Core Tables**

- `programs` - Breeding programs
- `trials` - Field trials
- `studies` - Studies within trials
- `locations` - Field locations (with PostGIS geometry)
- `people` - Users and contacts
- `lists` - Custom lists

### **Phenotyping Tables**

- `observation_units` - Plots, plants, samples
- `observations` - Phenotypic measurements
- `observation_variables` - Trait definitions
- `traits`, `scales`, `methods` - Variable components
- `images` - Plant/field images (metadata, actual files in MinIO)

### **Genotyping Tables**

- `samples` - DNA samples
- `variant_sets` - Collections of variants
- `variants` - Genetic variants
- `call_sets` - Genotype calls for samples
- `calls` - Individual genotype calls

### **Germplasm Tables**

- `germplasm` - Germplasm accessions
- `germplasm_attributes` - Custom attributes
- `seed_lots` - Seed inventory
- `crosses` - Crossing records
- `pedigree` - Parent-offspring relationships

---

## 🔐 Security Considerations

- **JWT Authentication** - Secure token-based auth
- **Password Hashing** - bcrypt with salt
- **HTTPS** - Automatic with Caddy
- **CORS** - Configured for frontend domain
- **Rate Limiting** - Redis-based rate limiting
- **Input Validation** - Pydantic schemas
- **SQL Injection Protection** - SQLAlchemy ORM
- **File Upload Validation** - Type and size checks
- **Rootless Containers** - Podman security

---

## 📈 Performance Optimizations

- **Database Indexing** - Strategic indexes on frequently queried fields
- **Query Optimization** - SQLAlchemy eager loading, pagination
- **Caching** - Redis for frequently accessed data
- **CDN** - Static assets served via CDN (production)
- **Image Optimization** - Automatic resizing and compression
- **Code Splitting** - Vite automatic code splitting
- **Service Worker Caching** - Offline-first architecture
- **Database Connection Pooling** - SQLAlchemy async pool

---

## 🧪 Testing Strategy

### **Backend**

- Unit tests (pytest)
- Integration tests (FastAPI TestClient)
- BrAPI compliance tests (BRAVA validator)
- Load testing (Locust)

### **Frontend**

- Component tests (Vitest + React Testing Library)
- E2E tests (Playwright)
- PWA tests (Lighthouse)
- Accessibility tests (axe-core)

---

## 📦 Deployment Options

### **Development**

- Local Podman containers
- Hot reload for frontend and backend

### **Production**

- Podman with systemd integration
- Caddy for HTTPS and reverse proxy
- PostgreSQL with regular backups
- MinIO for distributed object storage
- Redis for caching and sessions

### **Cloud Options**

- Any VPS (DigitalOcean, Linode, Hetzner)
- Kubernetes (can generate K8s YAML from Podman pods)
- Self-hosted on-premise servers

---

## 🎓 Learning Resources

- [BrAPI Specification](https://brapi.org)
- [FastAPI Documentation](https://fastapi.tiangolo.com)
- [React Documentation](https://react.dev)
- [Vite PWA Plugin](https://vite-pwa-org.netlify.app)
- [Workbox Documentation](https://developer.chrome.com/docs/workbox)
- [Podman Documentation](https://docs.podman.io)

---

## 🤝 Contributing

This is an open-source project. Contributions are welcome!

---

## 📝 License

To be determined (suggest: MIT or Apache 2.0)

---

## 🚀 Next Steps

**Choose what to build first:**

1. **Backend Foundation** - FastAPI project structure + BrAPI Core endpoints
2. **Frontend Foundation** - React PWA setup + authentication UI
3. **Database Schema** - PostgreSQL schema for all BrAPI modules
4. **Complete Scaffold** - Full project structure with all components
5. **Deployment Setup** - Podman compose + Caddy configuration

**What would you like to start with?**
