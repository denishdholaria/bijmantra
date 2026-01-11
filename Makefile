.PHONY: help dev start stop restart logs clean build test lint format install

# ============================================
# Container Runtime Configuration
# Standardized on Podman (rootless, daemonless, OCI-compliant)
# ============================================
CONTAINER_RUNTIME := /opt/podman/bin/podman
COMPOSE_CMD := $(CONTAINER_RUNTIME) compose

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install all dependencies (backend + frontend)
	@echo "Installing backend dependencies..."
	cd backend && python -m venv venv && . venv/bin/activate && pip install -r requirements.txt
	@echo "Installing frontend dependencies..."
	cd frontend && npm install
	@echo "✓ All dependencies installed"

# ============================================
# Development Commands
# ============================================

dev: ## Start infrastructure services (postgres, redis, minio)
	$(COMPOSE_CMD) up -d postgres redis minio
	@echo "✓ Infrastructure started. Run 'make dev-backend' and 'make dev-frontend' in separate terminals"

dev-backend: ## Start backend development server
	cd backend && . venv/bin/activate && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

dev-frontend: ## Start frontend development server
	cd frontend && npm run dev

start: ## Start all services
	$(COMPOSE_CMD) up -d

stop: ## Stop all services
	$(COMPOSE_CMD) down

restart: ## Restart all services
	$(COMPOSE_CMD) restart

logs: ## Show logs from all services
	$(COMPOSE_CMD) logs -f

logs-backend: ## Show backend logs only
	$(COMPOSE_CMD) logs -f backend

logs-frontend: ## Show frontend logs only
	$(COMPOSE_CMD) logs -f frontend

clean: ## Stop and remove all containers, volumes
	$(COMPOSE_CMD) down -v
	@echo "✓ All containers and volumes removed"

build: ## Build production containers
	$(COMPOSE_CMD) build

# ============================================
# Testing Commands
# ============================================

test: ## Run all tests
	@echo "Running backend tests..."
	cd backend && . venv/bin/activate && pytest
	@echo "Running frontend tests..."
	cd frontend && npm run test

test-backend: ## Run backend tests only
	cd backend && . venv/bin/activate && pytest

test-frontend: ## Run frontend tests only
	cd frontend && npm run test

# ============================================
# Code Quality Commands
# ============================================

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

# ============================================
# Database Commands
# ============================================

db-migrate: ## Run database migrations
	cd backend && . venv/bin/activate && alembic upgrade head

db-revision: ## Create new database migration
	@read -p "Enter migration message: " msg; \
	cd backend && . venv/bin/activate && alembic revision --autogenerate -m "$$msg"

db-reset: ## Reset database (WARNING: destroys all data)
	$(COMPOSE_CMD) down postgres
	$(CONTAINER_RUNTIME) volume rm bijmantra_postgres_data || true
	$(COMPOSE_CMD) up -d postgres
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

create-user: ## Create a new user interactively
	cd backend && . venv/bin/activate && python -m app.scripts.create_user

# ============================================
# Container Management Commands
# ============================================

ps: ## Show running containers
	$(CONTAINER_RUNTIME) ps

pods: ## Show running pods
	$(CONTAINER_RUNTIME) pod ps

shell-backend: ## Open shell in backend container
	$(CONTAINER_RUNTIME) exec -it bijmantra-backend bash

shell-db: ## Open PostgreSQL shell
	$(CONTAINER_RUNTIME) exec -it bijmantra-postgres psql -U bijmantra_user -d bijmantra_db

info: ## Show service URLs
	@echo "=== BijMantra Services ==="
	@echo "Frontend:        http://localhost:5173"
	@echo "Backend API:     http://localhost:8000"
	@echo "API Docs:        http://localhost:8000/docs"
	@echo "PostgreSQL:      localhost:5432"
	@echo "Redis:           localhost:6379"
	@echo "MinIO Console:   http://localhost:9001"
	@echo "MinIO API:       http://localhost:9000"

# ============================================
# Development Environment (Full Stack)
# ============================================

dev-full: ## Start full development environment
	$(COMPOSE_CMD) -f compose.yaml -f compose.dev.yaml up -d
	@echo "✓ Development environment started"
	@echo "Backend:    http://localhost:8000"
	@echo "API Docs:   http://localhost:8000/docs"
	@echo "PostgreSQL: localhost:5432"
	@echo "Redis:      localhost:6379"
	@echo "MinIO:      http://localhost:9001"

dev-full-frontend: ## Start dev environment with frontend container
	$(COMPOSE_CMD) -f compose.yaml -f compose.dev.yaml --profile frontend up -d
	@echo "✓ Full development environment started"

dev-tools: ## Start dev environment with admin tools (Adminer, Redis Commander)
	$(COMPOSE_CMD) -f compose.yaml -f compose.dev.yaml --profile tools up -d
	@echo "✓ Development tools started"
	@echo "Adminer:         http://localhost:8080"
	@echo "Redis Commander: http://localhost:8081"

dev-down: ## Stop development environment
	$(COMPOSE_CMD) -f compose.yaml -f compose.dev.yaml --profile frontend --profile tools down
	@echo "✓ Development environment stopped"

# ============================================
# Production Environment
# ============================================

prod: ## Start production environment
	@if [ ! -f .env ]; then \
		echo "ERROR: .env file not found!"; \
		echo "Copy .env.production.example to .env and configure it first."; \
		exit 1; \
	fi
	$(COMPOSE_CMD) -f compose.yaml -f compose.prod.yaml up -d
	@echo "✓ Production environment started"

prod-build: ## Build production images
	$(COMPOSE_CMD) -f compose.yaml -f compose.prod.yaml build
	@echo "✓ Production images built"

prod-down: ## Stop production environment
	$(COMPOSE_CMD) -f compose.yaml -f compose.prod.yaml down
	@echo "✓ Production environment stopped"

prod-logs: ## Show production logs
	$(COMPOSE_CMD) -f compose.yaml -f compose.prod.yaml logs -f

prod-backup: ## Start production with backup service
	$(COMPOSE_CMD) -f compose.yaml -f compose.prod.yaml --profile backup up -d
	@echo "✓ Production with backup service started"

# ============================================
# Cleanup Commands
# ============================================

clean-all: ## Remove all containers, volumes, and images for this project
	$(COMPOSE_CMD) -f compose.yaml -f compose.dev.yaml -f compose.prod.yaml down -v --rmi local
	@echo "✓ All container resources cleaned"

status: ## Show container status
	$(COMPOSE_CMD) -f compose.yaml ps

# ============================================
# Podman Machine Management (macOS)
# ============================================

machine-start: ## Start Podman machine (macOS)
	$(CONTAINER_RUNTIME) machine start

machine-stop: ## Stop Podman machine (macOS)
	$(CONTAINER_RUNTIME) machine stop

machine-status: ## Show Podman machine status (macOS)
	$(CONTAINER_RUNTIME) machine info

