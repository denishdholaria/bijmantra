#!/bin/bash
source venv/bin/activate
export POSTGRES_SERVER=localhost
export POSTGRES_PORT=5432
export POSTGRES_USER=bijmantra_user
export POSTGRES_PASSWORD=changeme_in_production
export POSTGRES_DB=bijmantra_db
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
