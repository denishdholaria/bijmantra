# Bijmantra Quick Start Guide

Get up and running with Bijmantra in 5 minutes.

🌐 **Website:** [bijmantra.org](https://bijmantra.org)  
📦 **Version:** v1.0.0-beta.1 Prathama (प्रथम)

---

## 🚀 One-Command Setup

> **Docker users**: BijMantra uses **Podman** instead of Docker. Commands are identical — just use `podman` instead of `docker`. [Why Podman?](docs/ARCHITECTURE.md#container-runtime-podman)

```bash
./setup.sh
```

This will:
- Start PostgreSQL, Redis, and MinIO containers (via Podman)
- Setup Python virtual environment
- Install backend dependencies
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

# Terminal 2: Start backend
make dev-backend

# Terminal 3: Start frontend
make dev-frontend
```

### Option 2: Manual

```bash
# Terminal 1: Start infrastructure
/opt/podman/bin/podman compose up -d postgres redis minio

# Terminal 2: Backend
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 3: Frontend
cd frontend
npm run dev
```

---

## 🌐 Access Points

| Service | URL | Description |
|---------|-----|-------------|
| Frontend | http://localhost:5173 | React PWA (221 pages) |
| Backend API | http://localhost:8000 | FastAPI server (1,370 endpoints) |
| API Docs | http://localhost:8000/docs | Swagger UI |
| ReDoc | http://localhost:8000/redoc | Alternative docs |
| BrAPI | http://localhost:8000/brapi/v2 | BrAPI v2.1 (201 endpoints, 100%) |
| PostgreSQL | localhost:5432 | Database (PostGIS + pgvector) |
| Redis | localhost:6379 | Cache |
| MinIO Console | http://localhost:9001 | Object storage |

---

## 🔑 Default Credentials

### Application
- **Admin Email**: admin@bijmantra.org
- **Admin Password**: admin123
- **Demo Email**: demo@bijmantra.org
- **Demo Password**: demo123

### MinIO
- **Username**: minioadmin
- **Password**: minioadmin123

⚠️ **Change these in production!**

---

## 🧪 Test the API

```bash
cd backend
source venv/bin/activate
python test_api.py
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
# Activate virtual environment
cd backend && source venv/bin/activate

# Run migrations
alembic upgrade head

# Create new migration
alembic revision --autogenerate -m "description"

# Seed database
python -m app.db.seed --env=dev

# Clear seeded data
python -m app.db.seed --clear

# List available seeders
python -m app.db.seed --list

# Run tests
pytest

# Lint code
ruff check .

# Format code
ruff format .
```

### Frontend

```bash
cd frontend

# Install dependencies
npm install

# Start dev server
npm run dev

# Build for production
npm run build

# Run tests
npm run test

# Lint code
npm run lint
```

### Infrastructure (Podman)

```bash
# Start infrastructure services
make dev

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
│   │   ├── core/        # Config, database, security
│   │   ├── models/      # SQLAlchemy models (106)
│   │   ├── services/    # Business logic
│   │   ├── db/seeders/  # Database seeders (15)
│   │   └── main.py      # FastAPI app
│   ├── alembic/         # Database migrations (21)
│   └── requirements.txt
│
├── frontend/            # React PWA
│   ├── src/
│   │   ├── components/  # React components
│   │   ├── divisions/   # Module pages
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
# Backend
cd backend
source venv/bin/activate
pip install -r requirements.txt

# Frontend
cd frontend
rm -rf node_modules
npm install
```

---

## 📖 Next Steps

1. **Explore the API**: Visit http://localhost:8000/docs
2. **Read the docs**: Check `docs/` folder
3. **Review steering guide**: See `.kiro/steering/bijmantra-development.md`
4. **Check metrics**: See `metrics.json` for current stats
5. **Start coding**: Follow the development workflow in steering guide

---

## 🆘 Getting Help

- **Documentation**: See `docs/` folder
- **Issues**: GitHub Issues
- **Discussions**: GitHub Discussions
- **Code of Conduct**: See `CODE_OF_CONDUCT.md`

---

## 🎯 What's Implemented (v1.0.0-beta.1)

### Backend ✅ (1,370 API Endpoints)

| Module | Endpoints | Description |
|--------|-----------|-------------|
| BrAPI v2.1 | 201 | 100% coverage (Core, Germplasm, Phenotyping, Genotyping) |
| Breeding | 120 | Programs, trials, crossing, selection, pedigree |
| Phenotyping | 85 | Observations, traits, field operations |
| Genomics | 107 | Genotyping, GWAS, QTL, molecular breeding |
| Seed Bank | 59 | Vaults, accessions, conservation, MTA |
| Environment | 97 | Weather, climate, soil, sensors |
| Seed Operations | 96 | Quality, processing, DUS testing |
| Knowledge | 35 | Forums, training |
| Settings & Admin | 79 | Users, teams, integrations |

### Frontend ✅ (221 Pages, 211 Functional)

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
- 🌐 BrAPI v2.1 100% compliant
- 📱 PWA with offline support
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
  -d "username=admin@bijmantra.org&password=admin123"
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
| Frontend | React 18, TypeScript 5, Vite 5, Tailwind CSS, TanStack Query |
| Backend | Python 3.11, FastAPI, SQLAlchemy 2.0, Pydantic 2 |
| Database | PostgreSQL 15, PostGIS, pgvector, Redis |
| Compute | Rust/WASM, Fortran |
| Container | Podman (rootless, daemonless) |

---

**Happy Coding!** 🌱
