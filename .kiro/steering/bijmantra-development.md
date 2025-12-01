---
inclusion: always
---

# Bijmantra Development Steering Guide

## Project Overview

**Bijmantra** is a BrAPI v2.1-compliant Progressive Web Application (PWA) for plant breeding data management. It's designed to be fully open-source, offline-capable, and suitable for both small research teams and large breeding programs.

### Core Vision

- **100% Open Source** - No proprietary dependencies
- **PWA-First** - Offline-capable, installable, mobile-friendly
- **BrAPI v2.1 Compliant** - Full implementation of all 4 modules (Core, Phenotyping, Genotyping, Germplasm)
- **Field-Ready** - Optimized for offline data collection in remote locations
- **Federated** - Each organization owns their data with optional federation
- **Secure** - JWT authentication, HTTPS, data sovereignty, RBAC

---

## Technology Stack

### Frontend (React PWA)
- **React 18+** - UI framework
- **TypeScript 5+** - Type safety
- **Vite 5+** - Build tool with fast HMR
- **Tailwind CSS 3+** - Utility-first styling
- **shadcn/ui** - Modern component library
- **TanStack Query 5+** - Server state management and caching
- **Zustand 4+** - Lightweight local state management
- **React Hook Form 7+** - Form handling
- **Zod 3+** - Schema validation
- **Dexie.js** - IndexedDB wrapper for offline storage
- **Workbox 7+** - Service worker strategies
- **Recharts 2+** - Data visualization
- **TanStack Table 8+** - Data tables
- **Leaflet 1.9+** - Maps for field locations

### Backend (FastAPI)
- **Python 3.11+** - Main language
- **FastAPI 0.110+** - REST API framework
- **Pydantic 2+** - Data validation
- **SQLAlchemy 2.0+** - ORM
- **Alembic 1.13+** - Database migrations
- **asyncpg** - Async PostgreSQL driver
- **python-jose** - JWT tokens
- **passlib** - Password hashing (bcrypt)
- **Pillow** - Image processing
- **pytest** - Testing framework

### Infrastructure
- **PostgreSQL 15+** - Main database
- **PostGIS 3.3+** - Spatial extension for locations
- **Redis 7+** - Caching and sessions
- **MinIO** - S3-compatible object storage for images
- **Podman 5+** - Container runtime
- **Caddy 2+** - Reverse proxy with automatic HTTPS

---

## Project Structure

```
bijmantra/
├── backend/                    # FastAPI BrAPI Server
│   ├── app/
│   │   ├── api/v2/            # BrAPI v2.1 endpoints
│   │   │   ├── core/          # Programs, Trials, Studies, Locations
│   │   │   ├── phenotyping/   # Observations, Variables, Images
│   │   │   ├── genotyping/    # Samples, Variants, Calls
│   │   │   └── germplasm/     # Germplasm, Pedigree, Crosses
│   │   ├── core/              # Config, security, database
│   │   ├── models/            # SQLAlchemy models
│   │   ├── schemas/           # Pydantic schemas (BrAPI)
│   │   ├── crud/              # Database operations
│   │   ├── tests/             # Test suite
│   │   └── main.py            # FastAPI app entry
│   ├── alembic/               # Database migrations
│   ├── requirements.txt
│   ├── Containerfile
│   └── README.md
│
├── frontend/                   # React PWA
│   ├── src/
│   │   ├── api/               # BrAPI client
│   │   ├── components/        # React components
│   │   ├── hooks/             # Custom hooks
│   │   ├── lib/               # Utilities (db, validators)
│   │   ├── pages/             # Page components
│   │   ├── store/             # Zustand stores
│   │   ├── types/             # TypeScript types
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── public/                # Static assets
│   ├── package.json
│   ├── vite.config.ts
│   ├── tailwind.config.js
│   └── README.md
│
├── compose.yaml               # Podman Compose config
├── Caddyfile                  # Reverse proxy config
├── Makefile                   # Development commands
├── .env.example               # Environment template
├── docs/                      # Documentation
└── README.md
```

---

## Development Workflow

### Initial Setup

```bash
# Clone and install
git clone <repo> bijmantra
cd bijmantra
make install

# Start infrastructure
make dev

# In separate terminals:
make dev-backend    # http://localhost:8000
make dev-frontend   # http://localhost:5173
```

### Common Commands

```bash
make dev              # Start infrastructure
make dev-backend      # Start FastAPI server
make dev-frontend     # Start React dev server
make test             # Run all tests
make lint             # Run linters
make format           # Format code
make db-migrate       # Run migrations
make db-revision      # Create new migration
make clean            # Stop and remove containers
make info             # Show service URLs
```

### Database Migrations

```bash
# Create new migration
make db-revision

# Apply migrations
make db-migrate

# Reset database (WARNING: destroys data)
make db-reset
```

---

## BrAPI v2.1 Implementation

### Module Structure

Each BrAPI module is organized as:
- **Endpoints** - REST API routes in `app/api/v2/{module}/`
- **Models** - SQLAlchemy ORM models in `app/models/{module}.py`
- **Schemas** - Pydantic validation schemas in `app/schemas/{module}.py`
- **CRUD** - Database operations in `app/crud/{module}.py`

### Core Module (Priority 1)
- Programs, Trials, Studies
- Locations (with PostGIS)
- People, Lists
- Search services

### Phenotyping Module (Priority 2)
- Observation Units, Observations
- Observation Variables, Traits, Scales, Methods
- Images (stored in MinIO)
- Field data collection forms

### Genotyping Module (Priority 3)
- Samples, Markers
- Variant Sets, Variants, Calls
- Call Sets, References

### Germplasm Module (Priority 4)
- Germplasm catalog
- Germplasm Attributes
- Seed Lots, Crosses
- Pedigree trees

---

## Code Standards

### Backend (Python)

- **Linter**: Ruff
- **Formatter**: Ruff format
- **Type hints**: Required for all functions
- **Docstrings**: Google-style docstrings
- **Testing**: pytest with async support
- **Async**: Use async/await for I/O operations

Example:
```python
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db

router = APIRouter()

@router.get("/programs")
async def list_programs(
    skip: int = 0,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
):
    """List breeding programs with pagination."""
    # Implementation
    pass
```

### Frontend (TypeScript/React)

- **Linter**: ESLint
- **Formatter**: Prettier
- **Type safety**: Strict TypeScript
- **Component style**: Functional components with hooks
- **State management**: Zustand for local, TanStack Query for server
- **Styling**: Tailwind CSS with shadcn/ui components

Example:
```typescript
import { useQuery } from '@tanstack/react-query';
import { useStore } from '@/store';

export function ProgramList() {
  const { data: programs, isLoading } = useQuery({
    queryKey: ['programs'],
    queryFn: () => api.programs.list(),
  });

  if (isLoading) return <div>Loading...</div>;
  return <div>{/* render programs */}</div>;
}
```

---

## API Design Principles

### BrAPI Compliance
- Follow BrAPI v2.1 specification exactly
- Use standard response format with metadata and pagination
- Implement filtering, sorting, and pagination on all list endpoints
- Use consistent error responses

### Response Format
```json
{
  "metadata": {
    "datafiles": [],
    "pagination": {
      "currentPage": 0,
      "pageSize": 20,
      "totalCount": 100,
      "totalPages": 5
    },
    "status": [
      {
        "message": "Success",
        "messageType": "INFO"
      }
    ]
  },
  "result": {
    // Actual data
  }
}
```

### Pagination
- Default page size: 20
- Max page size: 1000
- Use `skip` and `limit` query parameters
- Always return pagination metadata

---

## Database Design

### Multi-Tenancy
- All tables include `organization_id` foreign key
- Row-level security via organization context
- Separate data per organization

### Spatial Data
- Use PostGIS for location coordinates
- Store as POINT geometry type
- Index spatial columns for performance

### Indexing Strategy
- Index all foreign keys
- Index frequently filtered columns
- Index sort columns
- Use composite indexes for common queries

---

## Offline-First Architecture

### Service Worker Strategy
- **Static Assets**: Cache First (instant load)
- **BrAPI Metadata**: Stale While Revalidate (fast + fresh)
- **Observation Data**: Network First + Offline Queue
- **Images**: Cache First with 7-day expiration

### IndexedDB Stores
- `observations` - Pending sync queue
- `traits` - Cached metadata
- `studies` - Cached study data
- `germplasm` - Cached germplasm data
- `images` - Base64 image blobs

### Sync Strategy
- Queue observations when offline
- Sync when connection restored
- Handle conflicts (server wins)
- Show sync status to user

---

## Security

### Authentication
- JWT tokens with 24-hour expiration
- Refresh tokens with 7-day expiration
- Secure HTTP-only cookies for tokens
- Password hashing with bcrypt

### Authorization
- Role-based access control (RBAC)
- Organization-scoped data access
- Endpoint-level permission checks
- Row-level security via organization

### Data Protection
- HTTPS only (Caddy automatic)
- CORS configured for frontend domain
- Rate limiting via Redis
- Input validation with Pydantic
- SQL injection protection via SQLAlchemy ORM

---

## Testing Strategy

### Backend
- Unit tests for business logic
- Integration tests for API endpoints
- Database tests with fixtures
- BrAPI compliance validation
- Load testing with Locust

### Frontend
- Component tests with React Testing Library
- Hook tests with Vitest
- E2E tests with Playwright
- PWA tests with Lighthouse
- Accessibility tests with axe-core

### Running Tests
```bash
make test              # All tests
make test-backend      # Backend only
make test-frontend     # Frontend only
```

---

## Deployment

### Development
- Local Podman containers
- Hot reload for both frontend and backend
- Automatic database migrations

### Production
- Podman with systemd integration
- Caddy for HTTPS and reverse proxy
- PostgreSQL with regular backups
- MinIO for distributed storage
- Redis for caching
- Environment-based configuration

### Environment Variables
See `.env.example` for all required variables:
- Database credentials
- JWT secret
- CORS origins
- MinIO credentials
- Redis connection

---

## Performance Optimization

### Backend
- Database connection pooling
- Query optimization with eager loading
- Pagination on all list endpoints
- Redis caching for frequently accessed data
- Async/await for I/O operations

### Frontend
- Code splitting with Vite
- Lazy loading of routes
- Image optimization
- Service worker caching
- IndexedDB for offline data

### Database
- Strategic indexes on frequently queried fields
- Composite indexes for common queries
- Partitioning for large tables (future)
- Query analysis and optimization

---

## Git Workflow

### Commit Messages
Use conventional commits:
```
feat: add program creation endpoint
fix: resolve offline sync race condition
docs: update API documentation
test: add tests for location filtering
chore: update dependencies
```

### Branch Naming
```
feature/brapi-core-endpoints
fix/offline-sync-bug
docs/api-documentation
```

### Pull Requests
- Descriptive title and description
- Link to related issues
- Include test coverage
- Request review from maintainers

---

## Documentation

### Code Documentation
- Docstrings for all functions and classes
- Type hints for all parameters
- Inline comments for complex logic
- README files in each module

### API Documentation
- Auto-generated from FastAPI (Swagger UI at `/docs`)
- BrAPI specification compliance notes
- Example requests and responses
- Error codes and meanings

### Development Guides
- Setup instructions
- Development workflow
- Testing procedures
- Deployment process

---

## Common Development Tasks

### Adding a New BrAPI Endpoint

1. **Define Pydantic Schema** (`app/schemas/{module}.py`)
   ```python
   class ProgramCreate(BaseModel):
       name: str
       description: Optional[str] = None
   ```

2. **Create SQLAlchemy Model** (`app/models/{module}.py`)
   ```python
   class Program(Base):
       __tablename__ = "programs"
       id = Column(Integer, primary_key=True)
       name = Column(String, nullable=False)
   ```

3. **Implement CRUD** (`app/crud/{module}.py`)
   ```python
   async def create_program(db: AsyncSession, program: ProgramCreate):
       db_program = Program(**program.dict())
       db.add(db_program)
       await db.commit()
       return db_program
   ```

4. **Create Endpoint** (`app/api/v2/{module}/{resource}.py`)
   ```python
   @router.post("/programs")
   async def create_program(program: ProgramCreate, db: AsyncSession = Depends(get_db)):
       return await crud.create_program(db, program)
   ```

5. **Add Tests** (`app/tests/test_{module}.py`)
   ```python
   async def test_create_program(client, db):
       response = client.post("/brapi/v2/programs", json={...})
       assert response.status_code == 201
   ```

### Adding a Frontend Page

1. **Create Page Component** (`src/pages/ProgramList.tsx`)
2. **Add Route** (`src/App.tsx`)
3. **Create API Client** (`src/api/programs.ts`)
4. **Add State Management** (`src/store/programs.ts`)
5. **Add Tests** (`src/pages/__tests__/ProgramList.test.tsx`)

---

## Troubleshooting

### Backend Issues

**Database connection fails**
```bash
# Check PostgreSQL is running
podman ps | grep postgres

# Check logs
make logs-backend

# Reset database
make db-reset
```

**Migrations fail**
```bash
# Check migration status
cd backend && alembic current

# Downgrade and retry
cd backend && alembic downgrade -1
make db-migrate
```

### Frontend Issues

**Module not found errors**
```bash
# Clear node_modules and reinstall
cd frontend && rm -rf node_modules && npm install
```

**Service worker issues**
```bash
# Clear browser cache and service workers
# DevTools → Application → Clear storage
# Then hard refresh (Cmd+Shift+R)
```

### Container Issues

**Port already in use**
```bash
# Find and stop conflicting container
podman ps
podman stop <container-id>
```

**Volume permission errors**
```bash
# Podman runs rootless, check volume permissions
podman volume ls
podman volume inspect <volume-name>
```

---

## Resources

- [BrAPI Specification](https://brapi.org)
- [FastAPI Documentation](https://fastapi.tiangolo.com)
- [React Documentation](https://react.dev)
- [Vite PWA Plugin](https://vite-pwa-org.netlify.app)
- [Workbox Documentation](https://developer.chrome.com/docs/workbox)
- [Podman Documentation](https://docs.podman.io)
- [PostgreSQL Documentation](https://www.postgresql.org/docs)
- [PostGIS Documentation](https://postgis.net/documentation)

---

## Key Contacts & Community

- **GitHub Issues**: Report bugs and request features
- **GitHub Discussions**: Ask questions and discuss ideas
- **Code of Conduct**: See CODE_OF_CONDUCT.md
- **Security Issues**: See SECURITY.md

---

## Development Priorities

### Phase 1: MVP (Core Module)
- [ ] Backend: BrAPI Core endpoints (Programs, Trials, Studies, Locations)
- [ ] Frontend: Authentication, Dashboard, Data tables
- [ ] Database: Core schema with PostGIS
- [ ] Deployment: Podman Compose setup

### Phase 2: Phenotyping
- [ ] Backend: Observations, Variables, Images
- [ ] Frontend: Field data collection forms
- [ ] Offline sync: Observation queue and sync

### Phase 3: Genotyping & Germplasm
- [ ] Backend: Genotyping and Germplasm modules
- [ ] Frontend: Variant analysis, Pedigree visualization
- [ ] Advanced features: Statistical analysis

### Phase 4: Production Ready
- [ ] Performance optimization
- [ ] Security hardening
- [ ] Comprehensive testing
- [ ] Documentation completion
- [ ] Multi-language support

