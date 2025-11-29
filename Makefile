.PHONY: help dev start stop restart logs clean build test lint format install

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

install: ## Install all dependencies (backend + frontend)
	@echo "Installing backend dependencies..."
	cd backend && python -m venv venv && . venv/bin/activate && pip install -r requirements.txt
	@echo "Installing frontend dependencies..."
	cd frontend && npm install
	@echo "✓ All dependencies installed"

dev: ## Start all services in development mode
	podman-compose up -d postgres redis minio
	@echo "Infrastructure started. Run 'make dev-backend' and 'make dev-frontend' in separate terminals"

dev-backend: ## Start backend development server
	cd backend && . venv/bin/activate && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

dev-frontend: ## Start frontend development server
	cd frontend && npm run dev

start: ## Start all services with podman-compose
	podman-compose up -d

stop: ## Stop all services
	podman-compose down

restart: ## Restart all services
	podman-compose restart

logs: ## Show logs from all services
	podman-compose logs -f

logs-backend: ## Show backend logs only
	podman-compose logs -f backend

logs-frontend: ## Show frontend logs only
	podman-compose logs -f frontend

clean: ## Stop and remove all containers, volumes, and images
	podman-compose down -v
	@echo "✓ All containers and volumes removed"

build: ## Build production containers
	podman-compose build

test: ## Run all tests
	@echo "Running backend tests..."
	cd backend && . venv/bin/activate && pytest
	@echo "Running frontend tests..."
	cd frontend && npm run test

test-backend: ## Run backend tests only
	cd backend && . venv/bin/activate && pytest

test-frontend: ## Run frontend tests only
	cd frontend && npm run test

lint: ## Run linters
	@echo "Linting backend..."
	cd backend && . venv/bin/activate && ruff check .
	@echo "Linting frontend..."
	cd frontend && npm run lint

format: ## Format code
	@echo "Formatting backend..."
	cd backend && . venv/bin/activate && ruff format .
	@echo "Formatting frontend..."
	cd frontend && npm run format

db-migrate: ## Run database migrations
	cd backend && . venv/bin/activate && alembic upgrade head

db-revision: ## Create new database migration
	@read -p "Enter migration message: " msg; \
	cd backend && . venv/bin/activate && alembic revision --autogenerate -m "$$msg"

db-reset: ## Reset database (WARNING: destroys all data)
	podman-compose down postgres
	podman volume rm bijmantra_postgres_data || true
	podman-compose up -d postgres
	sleep 5
	cd backend && . venv/bin/activate && alembic upgrade head
	@echo "✓ Database reset complete"

ps: ## Show running containers
	podman ps --pod

shell-backend: ## Open shell in backend container
	podman exec -it bijmantra-backend bash

shell-db: ## Open PostgreSQL shell
	podman exec -it bijmantra-postgres psql -U bijmantra_user -d bijmantra_db

info: ## Show service URLs
	@echo "=== Bijmantra Services ==="
	@echo "Frontend:        http://localhost:5173"
	@echo "Backend API:     http://localhost:8000"
	@echo "API Docs:        http://localhost:8000/docs"
	@echo "PostgreSQL:      localhost:5432"
	@echo "Redis:           localhost:6379"
	@echo "MinIO Console:   http://localhost:9001"
	@echo "MinIO API:       http://localhost:9000"
