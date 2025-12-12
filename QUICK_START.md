# Bijmantra Quick Start Guide

Get up and running with Bijmantra in 5 minutes.

---

## 🚀 One-Command Setup

```bash
./setup.sh
```

This will:
- Start PostgreSQL, Redis, and MinIO containers
- Setup Python virtual environment
- Install backend dependencies
- Run database migrations
- Seed initial data
- Install frontend dependencies

---

## 🏃 Start Development

### Option 1: Using Make (Recommended)

```bash
# Terminal 1: Start backend
make dev-backend

# Terminal 2: Start frontend (when ready)
make dev-frontend
```

### Option 2: Manual

```bash
# Terminal 1: Backend
cd backend
source venv/bin/activate
uvicorn app.main:app --reload

# Terminal 2: Frontend (when ready)
cd frontend
npm run dev
```

---

## 🌐 Access Points

| Service | URL | Description |
|---------|-----|-------------|
| Frontend | http://localhost:5173 | React PWA (271+ pages) |
| Backend API | http://localhost:8000 | FastAPI server (469 endpoints) |
| API Docs | http://localhost:8000/docs | Swagger UI |
| ReDoc | http://localhost:8000/redoc | Alternative docs |
| BrAPI | http://localhost:8000/brapi/v2 | BrAPI v2.1 (100%) |
| Meilisearch | http://localhost:7700 | Instant search |
| PostgreSQL | localhost:5432 | Database |
| Redis | localhost:6379 | Cache |
| MinIO Console | http://localhost:9001 | Object storage |

---

## 🔑 Default Credentials

### Application
- **Email**: admin@example.org
- **Password**: admin123

### MinIO
- **Username**: minioadmin
- **Password**: minioadmin123

⚠️ **Change these in production!**

---

## 🧪 Test the API

```bash
cd backend
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
python -m app.db_seed

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

# Format code
npm run format
```

### Infrastructure

```bash
# Start all services
make dev
# or: podman compose up -d

# Stop all services
make stop
# or: podman compose down

# View logs
make logs

# View backend logs only
make logs-backend

# Reset database (⚠️ destroys data)
make db-reset

# Show service status
make ps

# Show service URLs
make info
```

---

## 🗂️ Project Structure

```
bijmantra/
├── backend/              # FastAPI backend
│   ├── app/
│   │   ├── api/         # API endpoints
│   │   ├── core/        # Config, database, security
│   │   ├── models/      # SQLAlchemy models
│   │   ├── schemas/     # Pydantic schemas
│   │   ├── crud/        # Database operations
│   │   └── main.py      # FastAPI app
│   ├── alembic/         # Database migrations
│   └── requirements.txt
│
├── frontend/            # React PWA (in progress)
│   ├── src/
│   │   ├── api/        # BrAPI client
│   │   ├── components/ # React components
│   │   ├── pages/      # Page components
│   │   └── App.tsx
│   └── package.json
│
├── compose.yaml         # Podman Compose config
├── Caddyfile           # Reverse proxy config
├── Makefile            # Development commands
├── setup.sh            # Setup script
└── .env                # Environment variables
```

---

## 🔧 Troubleshooting

### Backend won't start

```bash
# Check if PostgreSQL is running
podman ps | grep postgres

# Check logs
make logs-backend

# Reset database
make db-reset
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
podman restart bijmantra-postgres

# Check connection
podman exec -it bijmantra-postgres psql -U bijmantra_user -d bijmantra_db
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
4. **Check project status**: See `PROJECT_STATUS.md`
5. **Start coding**: Follow the development workflow in steering guide

---

## 🆘 Getting Help

- **Documentation**: See `docs/` folder
- **Issues**: GitHub Issues
- **Discussions**: GitHub Discussions
- **Code of Conduct**: See `CODE_OF_CONDUCT.md`

---

## 🎯 What's Implemented

### Backend ✅ (469 API Endpoints)
- Authentication (JWT)
- BrAPI v2.1 (34/34 endpoints - 100%)
- Plant Sciences (breeding, genomics, phenotyping, analysis tools)
- Seed Operations (dispatch, processing, quality)
- Commercial (traceability, licensing, DUS testing)
- Advanced Analytics (GWAS, G×E, selection index)
- AI/ML (Veena RAG, voice, vector search)
- Sun-Earth Systems (solar, photoperiod, UV)
- Space Research (crops, radiation, life support)
- Sensor Networks (devices, alerts, live data)
- Multi-tenancy (organization-based)
- Database migrations
- API documentation

### Frontend ✅ (271+ Pages)
- Complete Plant Sciences module (8 new analysis pages)
- Complete Seed Operations module (18 pages)
- Complete Commercial module (DUS, Licensing)
- Earth Systems module
- Sun-Earth Systems module
- Space Research module
- Sensor Networks module
- Knowledge module (Training, Forums)
- Integration Hub
- Veena AI Assistant with voice
- WASM Genomics tools

---

## 📝 Example API Calls

### Login

```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@example.org&password=admin123"
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

---

**Happy Coding!** 🌱

**Jay Shree Ganeshay Namo Namah!** 🙏
