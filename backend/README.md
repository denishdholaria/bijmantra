# Bijmantra Backend

**Version:** v1.0.0-beta.1 Prathama (प्रथम)

FastAPI backend publishing all 201 official BrAPI v2.1 operations alongside a broader local `/brapi/v2` surface tracked in `/metrics.json`.

## Setup

This project uses [uv](https://docs.astral.sh/uv/) for dependency management — a Rust-based package manager that is 10–50x faster than pip/Poetry.

```bash
# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies and create .venv automatically
uv sync --extra dev --extra analytics --extra geo

# Run migrations
uv run alembic upgrade head

# Seed database with initial data
uv run python -m app.db.seed --env=dev

# Start development server
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Optional extras

```bash
uv sync --extra ml       # sentence-transformers, transformers, xgboost, etc.
uv sync --extra vision   # opencv-python-headless (add McAfee exclusion on macOS first)
uv sync --extra memory   # mem0ai, pgvector
uv sync --extra pdf      # weasyprint
```

## API Documentation

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- OpenAPI JSON: http://localhost:8000/openapi.json

## Database Migrations

```bash
# Create new migration
uv run alembic revision --autogenerate -m "description"

# Apply migrations
uv run alembic upgrade head

# Rollback one migration
uv run alembic downgrade -1
```

## Testing

```bash
uv run pytest
```

## Code Quality

```bash
# Lint
uv run ruff check .

# Format
uv run ruff format .
```

## Project Structure

```
app/
├── api/                 # API endpoints
│   ├── v2/             # BrAPI v2.1 + BijMantra endpoints
│   ├── brapi/          # BrAPI-specific routers
│   └── auth.py         # Authentication
├── modules/            # Domain modules
│   ├── breeding/       # Breeding programs, trials, selection
│   ├── genomics/       # Genotyping, GWAS, QTL, molecular breeding
│   ├── phenotyping/    # Observations, traits, field operations
│   ├── germplasm/      # Germplasm management
│   ├── environment/    # Weather, climate, soil, sensors
│   ├── spatial/        # GIS, rasterio, spatial analysis
│   ├── ai/             # Veena AI, REEVU, chat
│   ├── interop/        # External integrations
│   ├── plant_sciences/ # Plant science domain
│   └── core/           # Core module routes
├── core/               # Shared infrastructure
│   ├── config.py       # Settings
│   ├── database.py     # Database connection
│   └── security.py     # Authentication
├── models/             # SQLAlchemy models (110)
├── schemas/            # Pydantic schemas
├── services/           # Business logic (legacy flat + domain)
├── control_plane/      # Developer control plane
├── startup/            # App initialization and route registration
├── middleware/          # Request/response middleware
├── workers/            # Background job workers
├── mcp/                # Model Context Protocol server
├── db/seeders/         # Database seeders (15)
├── crud/               # Data access layer
└── main.py             # FastAPI app
```

## Environment Variables

See `.env.example` in the root directory.

## Default Credentials

After starting the server, create your first user:
```bash
make create-user
```

Or use the registration API endpoint.

> **Security:** All credentials should be set via environment variables. Never commit credentials to version control.

⚠️ **Change these credentials in production!**

## Quick Start with Make

From the project root:

```bash
# Install dependencies (uv handles venv automatically)
uv sync --extra dev --extra analytics --extra geo

# Start infrastructure (PostgreSQL, Redis, MinIO)
make dev

# Run migrations and seed
uv run alembic upgrade head
uv run python -m app.db.seed --env=dev

# Start backend
make dev-backend
```

## BrAPI Surface

This backend publishes all 201 official BrAPI v2.1 operations.
The local `/brapi/v2` route also exposes additional BijMantra-specific operations beyond that published set, so use `/metrics.json` for the current exposed count.

| Module | Endpoints | Coverage |
|--------|-----------|----------|
| Core | 50 | 100% |
| Germplasm | 39 | 100% |
| Phenotyping | 51 | 100% |
| Genotyping | 61 | 100% |
| **Total** | **201** | **100%** |

Use [BRAVA](http://webapps.ipk-gatersleben.de/brapivalidator/) to validate the official published BrAPI operations when needed.

## Database Stats

| Metric | Count |
|--------|-------|
| Models | 110 |
| Tables | 119 |
| Migrations | 31 |
| Seeders | 15 |
| Seeded Records | 413 |

> Source of truth: `/metrics.json`

## Database Extensions

BijMantra requires PostgreSQL 16 with the following 8 extensions. All are bundled in the `timescale/timescaledb-ha:pg16-latest` Docker image used by `compose.yaml`.

| Extension | Purpose | Requires `shared_preload_libraries` |
|-----------|---------|-------------------------------------|
| `timescaledb` | IoT telemetry time-series optimization | Yes |
| `vector` (pgvector) | AI embedding similarity search | No |
| `postgis` | Spatial data and geometry queries | No |
| `pg_trgm` | Fuzzy text search with GIN indexes | No |
| `uuid-ossp` | UUID generation | No |
| `pgcrypto` | Database-level credential encryption | No |
| `pgaudit` | Compliance audit logging | Yes |
| `ltree` | Hierarchical organization queries | No |

Extensions requiring `shared_preload_libraries` are configured in `docker/postgres/postgresql.conf`:
```ini
shared_preload_libraries = 'timescaledb,pgaudit'
```

**Environment variable required for pgcrypto:**
```bash
INTEGRATION_ENCRYPTION_KEY=<your-key>  # Used for pgp_sym_encrypt/decrypt
```

See `docs/development/POSTGRESQL_EXTENSIONS.md` for the full extension stack documentation.
