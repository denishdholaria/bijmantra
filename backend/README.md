# Bijmantra Backend

FastAPI backend implementing BrAPI v2.1 specification.

## Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run migrations
alembic upgrade head

# Start development server
uvicorn app.main:app --reload
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
│   └── germplasm/      # Germplasm module
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

## BrAPI Compliance

This backend implements BrAPI v2.1 specification. Test compliance using [BRAVA](http://webapps.ipk-gatersleben.de/brapivalidator/).
