# Soil Division Module

This module manages soil data within the Bijmantra platform, including nutrient tests, physical properties, microbial activity, amendment logs, and soil maps.

## Architecture

The module follows the standard Bijmantra architecture:
- **Models:** SQLAlchemy models defined in `models.py`.
- **Schemas:** Pydantic schemas for data validation in `schemas.py`.
- **Services:** CRUD operations and business logic in `service.py`.
- **Routes:** FastAPI routes in `routes.py`.
- **Frontend:** React components and services in `frontend/src/divisions/soil`.

## Dependencies

- **Backend:**
  - `sqlalchemy`: ORM for database interaction.
  - `pydantic`: Data validation and serialization.
  - `fastapi`: API framework.
  - `geoalchemy2`: Spatial data support (future use, currently standard fields).

- **Frontend:**
  - `react`: UI library.
  - `react-router-dom`: Routing.
  - `tailwindcss`: Styling.

## API Endpoints

- `GET /api/v2/soil/nutrient-tests`: List nutrient tests.
- `POST /api/v2/soil/nutrient-tests`: Create a nutrient test.
- `GET /api/v2/soil/physical-properties`: List physical properties.
- `POST /api/v2/soil/physical-properties`: Create physical properties record.
- `GET /api/v2/soil/microbial-activity`: List microbial activity records.
- `POST /api/v2/soil/microbial-activity`: Create microbial activity record.
- `GET /api/v2/soil/amendment-logs`: List amendment logs.
- `POST /api/v2/soil/amendment-logs`: Create amendment log.
- `GET /api/v2/soil/maps`: List soil maps.
- `POST /api/v2/soil/maps`: Create soil map.

## Usage

The module is integrated into the main application router and frontend navigation. Users can access soil data management through the "Soil" division in the application.
