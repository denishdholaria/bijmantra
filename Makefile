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

db-seed: ## Seed database with demo data (development)
	cd backend && . venv/bin/activate && python -m app.db.seed --env=dev
	@echo "✓ Demo data seeded"

db-seed-test: ## Seed database with test fixtures
	cd backend && . venv/bin/activate && python -m app.db.seed --env=test
	@echo "✓ Test fixtures seeded"

db-seed-clear: ## Clear all seeded data
	cd backend && . venv/bin/activate && python -m app.db.seed --clear
	@echo "✓ Seeded data cleared"

db-seed-list: ## List available seeders
	cd backend && . venv/bin/activate && python -m app.db.seed --list

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

# ============================================
# Docker Dev/Prod Commands
# ============================================

dev-docker: ## Start development environment with Docker
	docker compose -f compose.yaml -f compose.dev.yaml up -d
	@echo "✓ Development environment started"
	@echo "Backend:    http://localhost:8000"
	@echo "API Docs:   http://localhost:8000/docs"
	@echo "PostgreSQL: localhost:5432"
	@echo "Redis:      localhost:6379"
	@echo "MinIO:      http://localhost:9001"

dev-docker-full: ## Start dev environment with frontend container
	docker compose -f compose.yaml -f compose.dev.yaml --profile frontend up -d
	@echo "✓ Full development environment started"

dev-docker-tools: ## Start dev environment with admin tools (Adminer, Redis Commander)
	docker compose -f compose.yaml -f compose.dev.yaml --profile tools up -d
	@echo "✓ Development tools started"
	@echo "Adminer:         http://localhost:8080"
	@echo "Redis Commander: http://localhost:8081"

dev-docker-down: ## Stop development environment
	docker compose -f compose.yaml -f compose.dev.yaml --profile frontend --profile tools down
	@echo "✓ Development environment stopped"

prod-docker: ## Start production environment with Docker
	@if [ ! -f .env ]; then \
		echo "ERROR: .env file not found!"; \
		echo "Copy .env.production.example to .env and configure it first."; \
		exit 1; \
	fi
	docker compose -f compose.yaml -f compose.prod.yaml up -d
	@echo "✓ Production environment started"

prod-docker-build: ## Build production images
	docker compose -f compose.yaml -f compose.prod.yaml build
	@echo "✓ Production images built"

prod-docker-down: ## Stop production environment
	docker compose -f compose.yaml -f compose.prod.yaml down
	@echo "✓ Production environment stopped"

prod-docker-logs: ## Show production logs
	docker compose -f compose.yaml -f compose.prod.yaml logs -f

prod-docker-backup: ## Start production with backup service
	docker compose -f compose.yaml -f compose.prod.yaml --profile backup up -d
	@echo "✓ Production with backup service started"

docker-clean: ## Remove all Docker containers, volumes, and images for this project
	docker compose -f compose.yaml -f compose.dev.yaml -f compose.prod.yaml down -v --rmi local
	@echo "✓ All Docker resources cleaned"

docker-status: ## Show Docker container status
	docker compose -f compose.yaml ps
