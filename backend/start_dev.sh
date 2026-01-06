#!/bin/bash
source venv/bin/activate
export POSTGRES_SERVER=localhost
export POSTGRES_PORT=5432
export POSTGRES_USER=bijmantra_user
export POSTGRES_PASSWORD=changeme_in_production
export POSTGRES_DB=bijmantra_db
# Stable SECRET_KEY for development - tokens persist across restarts
export SECRET_KEY=dev_secret_key_for_local_development_only_do_not_use_in_production
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
