.PHONY: help dev dev-redis dev-minio dev-meilisearch dev-all dev-beingbijmantra dev-beingbijmantra-down dev-beingbijmantra-logs start start-all stop restart logs clean build test test-backend test-backend-all test-backend-integration test-backend-integration-ci test-backend-integration-postgres test-backend-performance test-frontend test-frontend-watch lint format install dx-check reevu-gate overnight-plan update-state public-exclude-check control-surfaces-check devil-flags-check control-surfaces-ci ai-history-audit startup-doctor migration-doctor pr-review-pack mem0-help mem0-status control-plane-completion-assist control-plane-auth-token update-graphify

# ============================================
# Container Runtime Configuration
# Standardized on Podman (rootless, daemonless, OCI-compliant)
# ============================================
CONTAINER_RUNTIME := /opt/podman/bin/podman
COMPOSE_CMD := $(CONTAINER_RUNTIME) compose
BIJMANTRA_JS_PACKAGE_MANAGER ?= bun
JS_INSTALL_CMD = $(BIJMANTRA_JS_PACKAGE_MANAGER) install
JS_RUN_CMD = $(BIJMANTRA_JS_PACKAGE_MANAGER) run
BEINGBIJMANTRA_SURREAL_PORT ?= 8083
export BEINGBIJMANTRA_SURREAL_PORT
BACKEND_DEFAULT_TEST_MARKERS := not integration and not performance
BACKEND_CI_INTEGRATION_TEST_MARKERS := integration and not postgres_integration

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install all dependencies (backend + frontend)
	@echo "Installing backend dependencies..."
	cd backend && uv sync --extra dev --extra analytics --extra geo
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
	cd backend && uv run python scripts/migration_doctor.py

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
	@echo "✓ PostgreSQL started. Use './dev.sh' for the full stack."

dev-redis: ## Start optional Redis service
	$(COMPOSE_CMD) --profile infra up -d redis
	@echo "✓ Redis started on localhost:6379"

dev-minio: ## Start optional MinIO service
	$(COMPOSE_CMD) --profile infra up -d minio
	@echo "✓ MinIO started on http://localhost:9001"

dev-meilisearch: ## Start optional Meilisearch service
	$(COMPOSE_CMD) --profile infra up -d meilisearch
	@echo "✓ Meilisearch started on http://localhost:7700"

dev-all: ## Start PostgreSQL plus all optional development services
	$(COMPOSE_CMD) --profile infra up -d postgres redis minio meilisearch
	@echo "✓ All infrastructure started"

dev-beingbijmantra: ## Start optional Being Bijmantra project-brain sidecar
	$(COMPOSE_CMD) --profile beingbijmantra up -d beingbijmantra-surrealdb
	@echo "✓ Being Bijmantra sidecar started on http://localhost:$(BEINGBIJMANTRA_SURREAL_PORT)"

dev-beingbijmantra-down: ## Stop optional Being Bijmantra project-brain sidecar
	-$(CONTAINER_RUNTIME) stop beingbijmantra-surrealdb
	-$(CONTAINER_RUNTIME) rm -f beingbijmantra-surrealdb
	@echo "✓ Being Bijmantra sidecar stopped"

dev-beingbijmantra-logs: ## Show Being Bijmantra project-brain sidecar logs
	$(COMPOSE_CMD) logs -f beingbijmantra-surrealdb

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
	cd backend && uv run pytest -m "$(BACKEND_DEFAULT_TEST_MARKERS)"
	@echo "Running frontend tests..."
	cd frontend && $(JS_RUN_CMD) test:run

test-backend: ## Run default backend correctness tests only
	cd backend && uv run pytest -m "$(BACKEND_DEFAULT_TEST_MARKERS)"

test-backend-all: ## Run all backend tests, including integration and performance
	cd backend && uv run pytest

test-backend-integration: ## Run backend integration tests only
	cd backend && uv run pytest -m integration

test-backend-integration-ci: ## Run backend integration tests that do not require a private Postgres DSN
	cd backend && uv run pytest -m "$(BACKEND_CI_INTEGRATION_TEST_MARKERS)"

test-backend-integration-postgres: ## Run DSN-gated Postgres integration proof tests only
	cd backend && uv run pytest -m postgres_integration

test-backend-performance: ## Run backend performance and benchmark tests only
	cd backend && uv run pytest -m performance

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
	cd backend && uv run ruff check .
	@echo "Linting frontend..."
	cd frontend && $(JS_RUN_CMD) lint

format: ## Format code
	@echo "Formatting backend..."
	cd backend && uv run ruff format .
	@echo "Formatting frontend..."
	cd frontend && $(JS_RUN_CMD) format

# ============================================
# Database Commands
# ============================================

db-migrate: ## Run database migrations
	cd backend && uv run alembic upgrade head

db-revision: ## Create new database migration
	@read -p "Enter migration message: " msg; \
	cd backend && uv run alembic revision --autogenerate -m "$$msg"

db-reset: ## Reset database (WARNING: destroys all data)
	$(COMPOSE_CMD) down postgres
	$(CONTAINER_RUNTIME) volume rm bijmantraorg_postgres_data || true
	$(COMPOSE_CMD) up -d postgres
	sleep 5
	cd backend && uv run alembic upgrade head
	@echo "✓ Database reset complete"

db-seed: ## Seed database with demo data (development)
	cd backend && uv run python -m app.db.seed --env=dev
	@echo "✓ Demo data seeded"

db-seed-test: ## Seed database with test fixtures
	cd backend && uv run python -m app.db.seed --env=test
	@echo "✓ Test fixtures seeded"

db-seed-clear: ## Clear all seeded data
	cd backend && uv run python -m app.db.seed --clear
	@echo "✓ Seeded data cleared"

db-seed-list: ## List available seeders
	cd backend && uv run python -m app.db.seed --list

create-user: ## Create a new user interactively
	cd backend && uv run python -m app.scripts.create_user

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

dev-full: ## Start full development environment (all infra + tools)
	$(COMPOSE_CMD) --profile infra --profile tools up -d
	@echo "✓ Full development environment started"

dev-tools: ## Start dev tools (Adminer, Redis Commander, OmShriMaatreNamahaDB)
	$(COMPOSE_CMD) --profile infra --profile tools up -d
	@echo "✓ Development tools started"
	@echo "Adminer:         http://localhost:8080"
	@echo "Redis Commander: http://localhost:8081"
	@echo "OmShriMaatreNamahaDB: http://localhost:8082"

dev-down: ## Stop all development services
	$(COMPOSE_CMD) --profile infra --profile tools --profile beingbijmantra down
	@echo "✓ Development environment stopped"

# ============================================
# Production Environment
# ============================================
# Production compose was removed (outdated, would need full rewrite).
# When deployment is needed, create a fresh compose.prod.yaml derived
# from the current compose.yaml with production overrides.
# Supporting files still exist: Caddyfile.prod, backend/Dockerfile.

# ============================================
# Cleanup Commands
# ============================================

clean-all: ## Remove all containers, volumes, and images for this project
	$(COMPOSE_CMD) --profile infra --profile tools --profile beingbijmantra down -v --rmi local
	@echo "✓ All container resources cleaned"

status: ## Show container status
	$(COMPOSE_CMD) ps

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
	cd backend && uv run python -m app.scripts.generate_api_docs
	@echo "Tracking API changes..."
	cd backend && uv run python -m app.scripts.api_change_tracker
	@echo "Verifying BrAPI compliance..."
	cd backend && uv run python -m app.scripts.verify_brapi_compliance
	@echo "Verifying OpenAPI output..."
	cd backend && uv run python -m app.scripts.verify_openapi_output
	@echo "Generating service dependency graph..."
	cd backend && uv run python -m app.scripts.service_dependency_graph
	@echo "Running complexity audit..."
	cd backend && uv run python -m app.scripts.code_complexity_audit
	@echo "Checking Pydantic docstrings..."
	cd backend && uv run python -m app.scripts.check_pydantic_docstrings
	@echo "Running auto-migration checker..."
	cd backend && uv run python -m app.scripts.auto_migration_checker
	@echo "Generating experimental Zustand stores..."
	cd backend && uv run python -m app.scripts.generate_zustand_stores
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

# ============================================
# Knowledge Graph Management
# ============================================

update-graphify: ## Update all graphify knowledge graphs (root + frontend + backend)
	@bash scripts/update-graphify.sh
