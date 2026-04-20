.PHONY: help dev dev-redis dev-minio dev-meilisearch dev-all dev-beingbijmantra dev-beingbijmantra-down dev-beingbijmantra-logs start start-all stop restart logs clean build test test-backend test-backend-all test-backend-integration test-backend-integration-ci test-backend-integration-postgres test-backend-performance test-frontend test-frontend-watch lint format install dx-check reevu-gate overnight-plan update-state public-exclude-check control-surfaces-check devil-flags-check control-surfaces-ci ai-history-audit startup-doctor migration-doctor pr-review-pack mem0-help mem0-status control-plane-completion-assist control-plane-auth-token

# ============================================
# Container Runtime Configuration
# Standardized on Podman (rootless, daemonless, OCI-compliant)
# ============================================
CONTAINER_RUNTIME := /opt/podman/bin/podman
COMPOSE_CMD := $(CONTAINER_RUNTIME) compose
BIJMANTRA_JS_PACKAGE_MANAGER ?= bun
JS_INSTALL_CMD = $(BIJMANTRA_JS_PACKAGE_MANAGER) install
JS_RUN_CMD = $(BIJMANTRA_JS_PACKAGE_MANAGER) run
OPTIONAL_INFRA_PROFILES := --profile redis --profile minio --profile meilisearch
BEINGBIJMANTRA_SURREAL_PORT ?= 8083
export BEINGBIJMANTRA_SURREAL_PORT
BEINGBIJMANTRA_COMPOSE_FILES := -f compose.yaml -f compose.beingbijmantra.yaml
BACKEND_DEFAULT_TEST_MARKERS := not integration and not performance
BACKEND_CI_INTEGRATION_TEST_MARKERS := integration and not postgres_integration

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install all dependencies (backend + frontend)
	@echo "Installing backend dependencies..."
	cd backend && python -m venv venv && . venv/bin/activate && pip install -r requirements.txt
	@echo "Installing frontend dependencies..."
	cd frontend && $(JS_INSTALL_CMD)
	@echo "✓ All dependencies installed"

# ============================================
# Development Commands
# ============================================

startup-doctor: ## Diagnose local startup prerequisites and runtime availability
	python3 scripts/startup_doctor.py

mem0-help: ## Show Mem0 CLI help through the repo wrapper
	./scripts/mem0-cli.sh --help

mem0-status: ## Check Mem0 CLI connectivity using repo .env settings
	./scripts/mem0-cli.sh status

control-plane-completion-assist: ## Stage a headless reviewed completion assist from the runtime autonomy-cycle response
	python3 scripts/stage_control_plane_completion_assist.py

control-plane-auth-token: ## Refresh the local superuser JWT used for hidden developer-control-plane headless runtime calls
	python3 scripts/refresh_developer_control_plane_auth_token.py

migration-doctor: ## Diagnose Alembic revision-chain and schema-drift issues
	cd backend && export PYTHONPATH=. && venv/bin/python scripts/migration_doctor.py

control-surfaces-ci: ## Run CI-safe control-surface and publication guardrails
	$(MAKE) control-surfaces-check
	$(MAKE) devil-flags-check
	$(MAKE) public-exclude-check
	python3 scripts/check_public_docs_for_internal.py

pr-review-pack: ## Run deterministic baseline PR review checks
	$(MAKE) control-surfaces-ci
	$(MAKE) migration-doctor

dev: ## Start core infrastructure (PostgreSQL only)
	$(COMPOSE_CMD) up -d postgres
	@echo "✓ Core infrastructure started. Optional services remain off by default."
	@echo "  Use 'make dev-redis', 'make dev-minio', 'make dev-meilisearch', or 'make dev-all' when needed"

dev-redis: ## Start optional Redis service
	$(COMPOSE_CMD) --profile redis up -d redis
	@echo "✓ Redis started on localhost:6379"

dev-minio: ## Start optional MinIO service
	$(COMPOSE_CMD) --profile minio up -d minio
	@echo "✓ MinIO started on http://localhost:9001"

dev-meilisearch: ## Start optional Meilisearch service
	$(COMPOSE_CMD) --profile meilisearch up -d meilisearch
	@echo "✓ Meilisearch started on http://localhost:7700"

dev-all: ## Start PostgreSQL plus all optional development services
	$(COMPOSE_CMD) $(OPTIONAL_INFRA_PROFILES) up -d postgres redis minio meilisearch
	@echo "✓ Core and optional infrastructure started. Run 'make dev-backend' and 'make dev-frontend' in separate terminals"

dev-beingbijmantra: ## Start optional Being Bijmantra project-brain sidecar
	$(COMPOSE_CMD) $(BEINGBIJMANTRA_COMPOSE_FILES) --profile beingbijmantra up -d beingbijmantra-surrealdb
	@echo "✓ Being Bijmantra project-brain sidecar started on http://localhost:$(BEINGBIJMANTRA_SURREAL_PORT)"
	@echo "  This sidecar is optional and separate from the main BijMantra app stack"

dev-beingbijmantra-down: ## Stop optional Being Bijmantra project-brain sidecar
	-$(CONTAINER_RUNTIME) stop beingbijmantra-surrealdb
	-$(CONTAINER_RUNTIME) rm -f beingbijmantra-surrealdb
	@echo "✓ Being Bijmantra project-brain sidecar stopped"

dev-beingbijmantra-logs: ## Show Being Bijmantra project-brain sidecar logs
	$(COMPOSE_CMD) $(BEINGBIJMANTRA_COMPOSE_FILES) logs -f beingbijmantra-surrealdb

dev-backend: ## Start backend development server
	cd backend && bash ./start_dev.sh

dev-frontend: ## Start frontend development server
	cd frontend && $(JS_RUN_CMD) dev

start: ## Start default core services
	$(COMPOSE_CMD) up -d

start-all: ## Start core and optional services
	$(COMPOSE_CMD) $(OPTIONAL_INFRA_PROFILES) up -d

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

test: ## Run default correctness-focused tests
	@echo "Running backend tests..."
	cd backend && . venv/bin/activate && pytest -m "$(BACKEND_DEFAULT_TEST_MARKERS)"
	@echo "Running frontend tests..."
	cd frontend && $(JS_RUN_CMD) test:run

test-backend: ## Run default backend correctness tests only
	cd backend && . venv/bin/activate && pytest -m "$(BACKEND_DEFAULT_TEST_MARKERS)"

test-backend-all: ## Run all backend tests, including integration and performance
	cd backend && . venv/bin/activate && pytest

test-backend-integration: ## Run backend integration tests only
	cd backend && . venv/bin/activate && pytest -m integration

test-backend-integration-ci: ## Run backend integration tests that do not require a private Postgres DSN
	cd backend && . venv/bin/activate && pytest -m "$(BACKEND_CI_INTEGRATION_TEST_MARKERS)"

test-backend-integration-postgres: ## Run DSN-gated Postgres integration proof tests only
	cd backend && . venv/bin/activate && pytest -m postgres_integration

test-backend-performance: ## Run backend performance and benchmark tests only
	cd backend && . venv/bin/activate && pytest -m performance

test-frontend: ## Run frontend tests once and exit
	cd frontend && $(JS_RUN_CMD) test:run

test-frontend-watch: ## Run frontend tests in watch mode
	cd frontend && $(JS_RUN_CMD) test

reevu-gate: ## Run REEVU backend validation gate (tests + eval + ops report)
	cd backend && bash scripts/run_reevu_gate_v2.sh

# ============================================
# Code Quality Commands
# ============================================

lint: ## Run linters
	@echo "Linting backend..."
	cd backend && . venv/bin/activate && ruff check .
	@echo "Linting frontend..."
	cd frontend && $(JS_RUN_CMD) lint

format: ## Format code
	@echo "Formatting backend..."
	cd backend && . venv/bin/activate && ruff format .
	@echo "Formatting frontend..."
	cd frontend && $(JS_RUN_CMD) format

# ============================================
# Database Commands
# ============================================

db-migrate: ## Run database migrations
	cd backend && export PYTHONPATH=. && venv/bin/python -m alembic upgrade head

db-revision: ## Create new database migration
	@read -p "Enter migration message: " msg; \
	cd backend && . venv/bin/activate && alembic revision --autogenerate -m "$$msg"

db-reset: ## Reset database (WARNING: destroys all data)
	$(COMPOSE_CMD) down postgres
	$(CONTAINER_RUNTIME) volume rm bijmantra_postgres_data || true
	$(COMPOSE_CMD) up -d postgres
	sleep 5
	cd backend && export PYTHONPATH=. && venv/bin/python -m alembic upgrade head
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
	@echo "Redis:           localhost:6379 (optional)"
	@echo "MinIO Console:   http://localhost:9001 (optional)"
	@echo "MinIO API:       http://localhost:9000 (optional)"
	@echo "Meilisearch:     http://localhost:7700 (optional)"
	@echo "Being Sidecar:   http://localhost:$(BEINGBIJMANTRA_SURREAL_PORT) (optional, separate)"

# ============================================
# Development Environment (Full Stack)
# ============================================

dev-full: ## Start full development environment
	$(COMPOSE_CMD) -f compose.yaml -f compose.dev.yaml $(OPTIONAL_INFRA_PROFILES) up -d
	@echo "✓ Development environment started"
	@echo "Backend:    http://localhost:8000"
	@echo "API Docs:   http://localhost:8000/docs"
	@echo "PostgreSQL: localhost:5432"
	@echo "Redis:      localhost:6379"
	@echo "MinIO:      http://localhost:9001"
	@echo "Meilisearch: http://localhost:7700"

dev-full-frontend: ## Start dev environment with frontend container
	$(COMPOSE_CMD) -f compose.yaml -f compose.dev.yaml $(OPTIONAL_INFRA_PROFILES) --profile frontend up -d
	@echo "✓ Full development environment started"

dev-tools: ## Start dev environment with admin tools (Adminer, Redis Commander)
	$(COMPOSE_CMD) -f compose.yaml -f compose.dev.yaml $(OPTIONAL_INFRA_PROFILES) --profile tools up -d
	@echo "✓ Development tools started"
	@echo "Adminer:         http://localhost:8080"
	@echo "Redis Commander: http://localhost:8081"
	@echo "OmShriMaatreNamahaDB (orchestration): http://localhost:8082"
	@echo "Use 'make dev-beingbijmantra' for the separate project-brain sidecar"

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
	$(COMPOSE_CMD) -f compose.yaml -f compose.prod.yaml $(OPTIONAL_INFRA_PROFILES) up -d
	@echo "✓ Production environment started"

prod-build: ## Build production images
	$(COMPOSE_CMD) -f compose.yaml -f compose.prod.yaml $(OPTIONAL_INFRA_PROFILES) build
	@echo "✓ Production images built"

prod-down: ## Stop production environment
	$(COMPOSE_CMD) -f compose.yaml -f compose.prod.yaml down
	@echo "✓ Production environment stopped"

prod-logs: ## Show production logs
	$(COMPOSE_CMD) -f compose.yaml -f compose.prod.yaml logs -f

prod-backup: ## Start production with backup service
	$(COMPOSE_CMD) -f compose.yaml -f compose.prod.yaml $(OPTIONAL_INFRA_PROFILES) --profile backup up -d
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


# ============================================
# Developer Experience Automation
# ============================================

dx-check: ## Run developer-experience automation checks
	@echo "Generating API docs..."
	cd backend && . venv/bin/activate && python -m app.scripts.generate_api_docs
	@echo "Tracking API changes..."
	cd backend && . venv/bin/activate && python -m app.scripts.api_change_tracker
	@echo "Verifying BrAPI compliance..."
	cd backend && . venv/bin/activate && python -m app.scripts.verify_brapi_compliance
	@echo "Verifying OpenAPI output..."
	cd backend && . venv/bin/activate && python -m app.scripts.verify_openapi_output
	@echo "Generating service dependency graph..."
	cd backend && . venv/bin/activate && python -m app.scripts.service_dependency_graph
	@echo "Running complexity audit..."
	cd backend && . venv/bin/activate && python -m app.scripts.code_complexity_audit
	@echo "Checking Pydantic docstrings..."
	cd backend && . venv/bin/activate && python -m app.scripts.check_pydantic_docstrings
	@echo "Running auto-migration checker..."
	cd backend && . venv/bin/activate && python -m app.scripts.auto_migration_checker
	@echo "Generating experimental Zustand stores..."
	cd backend && . venv/bin/activate && python -m app.scripts.generate_zustand_stores
	@echo "Checking docs for internal markers..."
	python scripts/check_public_docs_for_internal.py
	@echo "Checking potentially unused dependencies..."
	python scripts/check_unused_dependencies.py
	@echo "DX checks complete"

public-exclude-check: ## Verify required private paths are excluded from public sync
	python3 scripts/validate_public_exclude.py .

control-surfaces-check: ## Validate active agent-control JSON/markdown surfaces
	python3 scripts/check_control_surfaces.py

devil-flags-check: ## Scan red and orange devil-file hotspots without failing on existing debt
	python3 scripts/devil_flag_scanner.py --max-results 20

ai-history-audit: ## Audit historical legacy references inside the .ai evidence trail
	python3 scripts/audit_ai_historical_references.py

overnight-plan: ## Build the OmShriMaatreNamaha overnight dispatch plan from JSON job cards
	@echo "Planning overnight queue..."
	python3 scripts/run_overnight_queue.py
	@echo "✓ Overnight dispatch plan refreshed"

autonomy-cycle: ## Evaluate one bounded developer control-plane autonomy cycle
	@echo "Evaluating developer control-plane autonomy cycle..."
	python3 scripts/run_control_plane_autonomy_cycle.py
	@echo "  Completion assist staging activates automatically when BIJMANTRA_DEVELOPER_CONTROL_PLANE_AUTH_TOKEN is configured"
	@echo "✓ Developer control-plane autonomy cycle refreshed"

update-state: ## Refresh metrics and current-state visualization input for OmShriMaatreNamaha and JSON Crack
	@echo "Refreshing metrics.json..."
	python3 scripts/update_metrics.py
	@echo "Planning overnight queue..."
	python3 scripts/run_overnight_queue.py
	@echo "Evaluating developer control-plane autonomy cycle..."
	python3 scripts/run_control_plane_autonomy_cycle.py
	@echo "Exporting current app state..."
	python3 scripts/export_current_state.py
	@echo "✓ Current-state visualization input refreshed"
