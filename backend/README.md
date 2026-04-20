# Bijmantra Backend

**Version:** v1.0.0-beta.1 Prathama (प्रथम)

FastAPI backend publishing all 201 official BrAPI v2.1 operations alongside a broader local `/brapi/v2` surface tracked in `/metrics.json`.

## Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run migrations
alembic upgrade head

# Seed database with initial data
python -m app.db.seed --env=dev

# Start development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## API Documentation

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- OpenAPI JSON: http://localhost:8000/openapi.json

## Database Migrations

```bash
# Create new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1
```

## Testing

```bash
pytest
```

## Code Quality

```bash
# Lint
ruff check .

# Format
ruff format .
```

## Project Structure

```
app/
├── api/v2/              # BrAPI v2.1 endpoints
│   ├── core/           # Core module
│   ├── phenotyping/    # Phenotyping module
│   ├── genotyping/     # Genotyping module
│   ├── germplasm/      # Germplasm module
│   └── speed_breeding/ # Speed Breeding module
├── core/               # Core configuration
│   ├── config.py       # Settings
│   ├── database.py     # Database connection
│   └── security.py     # Authentication
├── models/             # SQLAlchemy models
├── schemas/            # Pydantic schemas
├── crud/               # Database operations
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
# Install dependencies
make install

# Start infrastructure (PostgreSQL, Redis, MinIO)
make dev

# Run migrations and seed
cd backend && alembic upgrade head && python -m app.db.seed --env=dev

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
| Models | 106 |
| Tables | 115 |
| Migrations | 21 |
| Seeders | 15 |
| Seeded Records | 413 |
