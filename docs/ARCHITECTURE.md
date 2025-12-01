# Bijmantra Architecture

**Version**: 0.1.0  
**Last Updated**: January 2024

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Client Layer                              │
│  ┌────────────────────────────────────────────────────────┐    │
│  │         Browser (Desktop / Tablet / Mobile)            │    │
│  │                                                          │    │
│  │  ┌────────────────────────────────────────────────┐   │    │
│  │  │      Bijmantra PWA (React + TypeScript)        │   │    │
│  │  │                                                  │   │    │
│  │  │  • UI Components (shadcn/ui)                   │   │    │
│  │  │  • State Management (TanStack Query + Zustand) │   │    │
│  │  │  • Service Worker (Workbox)                    │   │    │
│  │  │  • IndexedDB (Dexie.js)                        │   │    │
│  │  │  • BrAPI Client                                │   │    │
│  │  └────────────────────────────────────────────────┘   │    │
│  └────────────────────────────────────────────────────────┘    │
└──────────────────────┬──────────────────────────────────────────┘
                       │ HTTPS (REST API)
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Reverse Proxy Layer                          │
│  ┌────────────────────────────────────────────────────────┐    │
│  │              Caddy 2+ (Automatic HTTPS)                │    │
│  │                                                          │    │
│  │  Routes:                                                │    │
│  │  • /brapi/v2/*  → Backend API                          │    │
│  │  • /api/*       → Backend API                          │    │
│  │  • /*           → Frontend Static Files                │    │
│  └────────────────────────────────────────────────────────┘    │
└──────────────────────┬──────────────────────────────────────────┘
                       │
          ┌────────────┼────────────┐
          ▼            ▼            ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Application Layer                             │
│  ┌────────────────────────────────────────────────────────┐    │
│  │         FastAPI Backend (Python 3.11+)                 │    │
│  │                                                          │    │
│  │  ┌────────────────────────────────────────────────┐   │    │
│  │  │         BrAPI v2.1 Endpoints                   │   │    │
│  │  │  • Core (Programs, Trials, Studies, Locations)│   │    │
│  │  │  • Phenotyping (Observations, Variables)       │   │    │
│  │  │  • Genotyping (Samples, Variants, Calls)       │   │    │
│  │  │  • Germplasm (Germplasm, Pedigree, Crosses)    │   │    │
│  │  └────────────────────────────────────────────────┘   │    │
│  │                                                          │    │
│  │  ┌────────────────────────────────────────────────┐   │    │
│  │  │         Business Logic Layer                   │   │    │
│  │  │  • Authentication (JWT)                        │   │    │
│  │  │  • Authorization (RBAC)                        │   │    │
│  │  │  • Data Validation (Pydantic)                  │   │    │
│  │  │  • Multi-Tenancy (Organization-based)          │   │    │
│  │  └────────────────────────────────────────────────┘   │    │
│  │                                                          │    │
│  │  ┌────────────────────────────────────────────────┐   │    │
│  │  │         Data Access Layer                      │   │    │
│  │  │  • CRUD Operations                             │   │    │
│  │  │  • SQLAlchemy ORM (Async)                      │   │    │
│  │  │  • Query Building                              │   │    │
│  │  │  • Pagination                                  │   │    │
│  │  └────────────────────────────────────────────────┘   │    │
│  └────────────────────────────────────────────────────────┘    │
└──────────────────────┬──────────────────────────────────────────┘
                       │
          ┌────────────┼────────────┬──────────────┐
          ▼            ▼            ▼              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Data Layer                                  │
│                                                                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ PostgreSQL   │  │    Redis     │  │    MinIO     │          │
│  │   15+ +      │  │      7+      │  │  (S3-compat) │          │
│  │   PostGIS    │  │              │  │              │          │
│  │              │  │              │  │              │          │
│  │ • Programs   │  │ • Sessions   │  │ • Images     │          │
│  │ • Trials     │  │ • Cache      │  │ • Documents  │          │
│  │ • Studies    │  │ • Rate Limit │  │ • Files      │          │
│  │ • Locations  │  │ • Queues     │  │              │          │
│  │ • Users      │  │              │  │              │          │
│  │ • Obs Data   │  │              │  │              │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔄 Request Flow

### 1. Authentication Flow

```
User → Frontend → POST /api/auth/login
                    ↓
              FastAPI Auth Endpoint
                    ↓
              Validate Credentials
                    ↓
              Generate JWT Token
                    ↓
              Return Token to Frontend
                    ↓
              Store in Memory/LocalStorage
```

### 2. Authenticated Request Flow

```
User → Frontend → GET /brapi/v2/programs
                    ↓ (with JWT in header)
              Caddy Reverse Proxy
                    ↓
              FastAPI Endpoint
                    ↓
              Verify JWT Token
                    ↓
              Extract Organization ID
                    ↓
              CRUD Operation (filtered by org)
                    ↓
              PostgreSQL Query
                    ↓
              Format BrAPI Response
                    ↓
              Return to Frontend
```

### 3. Offline Data Collection Flow

```
User → Field Data Entry (Offline)
         ↓
    IndexedDB Storage
         ↓
    Service Worker Queue
         ↓
    Network Available?
         ↓ (yes)
    Sync to Backend
         ↓
    POST /brapi/v2/observations
         ↓
    Save to PostgreSQL
         ↓
    Clear Local Queue
```

---

## 📦 Component Architecture

### Backend Components

```
FastAPI Application
├── API Layer
│   ├── Authentication (JWT)
│   ├── BrAPI v2.1 Endpoints
│   │   ├── Core Module
│   │   ├── Phenotyping Module
│   │   ├── Genotyping Module
│   │   └── Germplasm Module
│   └── Dependencies (auth, db session)
│
├── Business Logic Layer
│   ├── CRUD Operations
│   ├── Data Validation (Pydantic)
│   ├── Authorization (RBAC)
│   └── Multi-Tenancy Logic
│
├── Data Access Layer
│   ├── SQLAlchemy Models
│   ├── Database Session Management
│   ├── Query Building
│   └── Transaction Management
│
└── Core Infrastructure
    ├── Configuration (Pydantic Settings)
    ├── Database Connection (Async)
    ├── Security (JWT, Password Hashing)
    └── Logging
```

### Frontend Components (Planned)

```
React PWA Application
├── UI Layer
│   ├── Pages (Routes)
│   ├── Components (shadcn/ui)
│   ├── Forms (React Hook Form)
│   └── Tables (TanStack Table)
│
├── State Management
│   ├── Server State (TanStack Query)
│   ├── Local State (Zustand)
│   └── Form State (React Hook Form)
│
├── API Layer
│   ├── BrAPI Client
│   ├── HTTP Client (Fetch)
│   └── Request/Response Interceptors
│
├── Offline Layer
│   ├── Service Worker (Workbox)
│   ├── IndexedDB (Dexie.js)
│   ├── Sync Queue
│   └── Cache Strategies
│
└── Core Infrastructure
    ├── Routing (React Router)
    ├── Authentication Context
    ├── Theme Provider
    └── Error Boundaries
```

---

## 🗄️ Database Schema

### Core Tables

```
organizations
├── id (PK)
├── name (unique)
├── description
├── contact_email
├── website
└── is_active

users
├── id (PK)
├── organization_id (FK → organizations)
├── email (unique)
├── hashed_password
├── full_name
├── is_active
└── is_superuser

programs
├── id (PK)
├── organization_id (FK → organizations)
├── program_db_id (unique, BrAPI ID)
├── program_name
├── abbreviation
├── objective
├── lead_person_db_id (FK → people)
├── additional_info (JSON)
└── external_references (JSON)

locations
├── id (PK)
├── organization_id (FK → organizations)
├── location_db_id (unique, BrAPI ID)
├── location_name
├── location_type
├── country_name
├── country_code
├── coordinates (PostGIS POINT)
├── altitude
├── additional_info (JSON)
└── external_references (JSON)

trials
├── id (PK)
├── organization_id (FK → organizations)
├── program_id (FK → programs)
├── location_id (FK → locations)
├── trial_db_id (unique, BrAPI ID)
├── trial_name
├── trial_description
├── start_date
├── end_date
├── active
├── additional_info (JSON)
└── external_references (JSON)

studies
├── id (PK)
├── organization_id (FK → organizations)
├── trial_id (FK → trials)
├── location_id (FK → locations)
├── study_db_id (unique, BrAPI ID)
├── study_name
├── study_description
├── start_date
├── end_date
├── active
├── observation_levels (JSON)
├── additional_info (JSON)
└── external_references (JSON)
```

### Relationships

```
Organization (1) ──→ (N) Users
Organization (1) ──→ (N) Programs
Organization (1) ──→ (N) Locations
Organization (1) ──→ (N) Trials
Organization (1) ──→ (N) Studies

Program (1) ──→ (N) Trials
Trial (1) ──→ (N) Studies
Location (1) ──→ (N) Trials
Location (1) ──→ (N) Studies
```

---

## 🔐 Security Architecture

### Authentication Flow

```
1. User Login
   ↓
2. Validate Credentials (bcrypt)
   ↓
3. Generate JWT Token
   {
     "sub": "user_id",
     "exp": "expiration_timestamp"
   }
   ↓
4. Return Token to Client
   ↓
5. Client Stores Token
   ↓
6. Include Token in Requests
   Authorization: Bearer <token>
   ↓
7. Backend Validates Token
   ↓
8. Extract User & Organization
   ↓
9. Process Request (org-scoped)
```

### Authorization Layers

```
1. Authentication Layer
   • JWT token validation
   • User existence check
   • Active user check

2. Organization Layer
   • Extract organization_id from user
   • Filter all queries by organization
   • Prevent cross-organization access

3. Role-Based Access Control (Future)
   • Admin: Full access
   • Manager: Program/Trial management
   • Researcher: Data collection
   • Viewer: Read-only access
```

---

## 🚀 Deployment Architecture

### Development

```
Developer Machine
├── Backend (uvicorn --reload)
├── Frontend (vite dev server)
└── Infrastructure (Podman containers)
    ├── PostgreSQL
    ├── Redis
    └── MinIO
```

### Production

```
Server (VPS / Cloud)
├── Caddy (Reverse Proxy + HTTPS)
│   ├── Port 443 (HTTPS)
│   └── Port 80 (HTTP → HTTPS redirect)
│
├── Backend (Podman container)
│   └── FastAPI (uvicorn)
│
├── Frontend (Static files served by Caddy)
│
└── Infrastructure (Podman containers)
    ├── PostgreSQL (persistent volume)
    ├── Redis (persistent volume)
    └── MinIO (persistent volume)
```

---

## 📊 Data Flow Patterns

### 1. Create Operation

```
Frontend Form
    ↓ (user input)
Validation (Zod)
    ↓
API Request (POST)
    ↓
Backend Validation (Pydantic)
    ↓
CRUD Create
    ↓
Generate BrAPI DbId
    ↓
Add Organization ID
    ↓
SQLAlchemy Insert
    ↓
PostgreSQL
    ↓
Return Created Object
    ↓
Format BrAPI Response
    ↓
Frontend Update (TanStack Query cache)
```

### 2. List Operation with Pagination

```
Frontend Request
    ↓ (page, pageSize, filters)
API Request (GET)
    ↓
Backend Endpoint
    ↓
Build Query (SQLAlchemy)
    ↓
Apply Organization Filter
    ↓
Apply User Filters
    ↓
Count Total Records
    ↓
Apply Pagination (offset, limit)
    ↓
Execute Query
    ↓
Format BrAPI Response
    {
      metadata: {
        pagination: {...},
        status: [...]
      },
      result: {
        data: [...]
      }
    }
    ↓
Frontend Display
```

### 3. Offline Sync Pattern

```
User Action (Offline)
    ↓
Save to IndexedDB
    ↓
Add to Sync Queue
    ↓
Service Worker Monitors Network
    ↓
Network Available
    ↓
Process Sync Queue
    ↓
POST to Backend (with retry)
    ↓
Backend Saves to PostgreSQL
    ↓
Return Success
    ↓
Remove from Sync Queue
    ↓
Update IndexedDB
    ↓
Notify User
```

---

## 🔧 Technology Stack Details

### Backend Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Framework | FastAPI 0.110+ | REST API framework |
| Language | Python 3.11+ | Main language |
| ORM | SQLAlchemy 2.0+ | Database abstraction |
| Validation | Pydantic 2+ | Data validation |
| Migrations | Alembic 1.13+ | Schema versioning |
| Database | PostgreSQL 15+ | Relational database |
| Spatial | PostGIS 3.3+ | Geographic data |
| Cache | Redis 7+ | Caching & sessions |
| Storage | MinIO | Object storage |
| Auth | python-jose | JWT tokens |
| Password | passlib | Bcrypt hashing |
| Testing | pytest | Test framework |
| Linting | Ruff | Code quality |

### Frontend Stack (Planned)

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Framework | React 18+ | UI framework |
| Language | TypeScript 5+ | Type safety |
| Build | Vite 5+ | Build tool |
| Styling | Tailwind CSS 3+ | Utility CSS |
| Components | shadcn/ui | Component library |
| State | TanStack Query 5+ | Server state |
| State | Zustand 4+ | Local state |
| Forms | React Hook Form 7+ | Form handling |
| Validation | Zod 3+ | Schema validation |
| Tables | TanStack Table 8+ | Data tables |
| Charts | Recharts 2+ | Visualizations |
| Maps | Leaflet 1.9+ | Geographic maps |
| PWA | Vite PWA Plugin | Service worker |
| Offline | Workbox 7+ | Cache strategies |
| Storage | Dexie.js | IndexedDB wrapper |
| Testing | Vitest | Test framework |
| E2E | Playwright | End-to-end tests |

---

## 📈 Scalability Considerations

### Horizontal Scaling

```
Load Balancer
    ├── Backend Instance 1
    ├── Backend Instance 2
    └── Backend Instance N
         ↓
    Shared Database
         ↓
    PostgreSQL (Primary + Replicas)
```

### Caching Strategy

```
Request
    ↓
Check Redis Cache
    ↓ (miss)
Query PostgreSQL
    ↓
Store in Redis (TTL)
    ↓
Return Response
```

### Database Optimization

- Indexes on foreign keys
- Indexes on frequently queried fields
- Composite indexes for common queries
- Spatial indexes for location queries
- Connection pooling (10 base, 20 max)
- Query optimization with EXPLAIN ANALYZE

---

## 🎯 Design Principles

1. **Separation of Concerns** - Clear layer boundaries
2. **Single Responsibility** - Each component has one job
3. **Dependency Injection** - Loose coupling
4. **Type Safety** - Pydantic and TypeScript
5. **Async First** - Non-blocking I/O
6. **API First** - Backend-agnostic frontend
7. **Offline First** - PWA with service workers
8. **Security by Design** - Multi-tenancy, JWT, RBAC
9. **BrAPI Compliance** - Standard API format
10. **Developer Experience** - Clear docs, tooling, testing

---

## 📚 References

- [BrAPI Specification v2.1](https://brapi.org)
- [FastAPI Documentation](https://fastapi.tiangolo.com)
- [SQLAlchemy 2.0 Documentation](https://docs.sqlalchemy.org)
- [PostGIS Documentation](https://postgis.net)
- [React Documentation](https://react.dev)
- [Vite PWA Plugin](https://vite-pwa-org.netlify.app)

---

**Jay Shree Ganeshay Namo Namah!** 🙏
