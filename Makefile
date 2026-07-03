.PHONY: help dev dev-redis dev-minio dev-meilisearch dev-all dev-auth dev-auth-down dev-auth-logs dev-beingbijmantra dev-beingbijmantra-down dev-beingbijmantra-logs start start-all stop restart logs clean build bij rust-fmt rust-check rust-clippy rust-test rust-live-test rust-live-test-run rust-live-db-create rust-live-db-reset rust-live-db-head rust-live-db-migrate rust-live-db-scratch-upgrade rust-serve rust-inspect rust-doctor rust-services rust-probe rust-logs rust-plan-dev rust-plan-status rust-plan-stop rust-plan-logs rust-dev rust-stop rust-run-start rust-run-stop rust-run-restart rust-run-processes rust-build test test-backend test-backend-all test-backend-integration test-backend-integration-ci test-backend-integration-postgres test-backend-performance test-frontend test-frontend-watch lint format install dx-check reevu-gate overnight-plan update-state public-exclude-check control-surfaces-check devil-flags-check control-surfaces-ci ai-history-audit startup-doctor migration-doctor rls-drift-check pr-review-pack mem0-help mem0-status control-plane-completion-assist control-plane-auth-token update-graphify wasm check-wasm-sync test-wasm-props

# ============================================
# Container Runtime Configuration
# Standardized on Podman (rootless, daemonless, OCI-compliant)
# ============================================
CONTAINER_RUNTIME := /opt/homebrew/bin/podman
COMPOSE_CMD := $(CONTAINER_RUNTIME) compose
BIJMANTRA_JS_PACKAGE_MANAGER ?= bun
JS_INSTALL_CMD = $(BIJMANTRA_JS_PACKAGE_MANAGER) install
JS_RUN_CMD = $(BIJMANTRA_JS_PACKAGE_MANAGER) run
BEINGBIJMANTRA_SURREAL_PORT ?= 8083
export BEINGBIJMANTRA_SURREAL_PORT
BACKEND_DEFAULT_TEST_MARKERS := not integration and not performance
BACKEND_CI_INTEGRATION_TEST_MARKERS := integration and not postgres_integration
RUST_PRODUCT_PACKAGES := -p bijmantra-core -p bijmantra-runtime -p bijmantra-server -p bijmantra-cli

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

# ============================================
# Kaggle Integration
# ============================================

kaggle-list: ## List downloaded Kaggle datasets and models
	cd backend && uv run python scripts/kaggle_download.py list

kaggle-plant-diseases: ## Download plant disease image dataset (87,900 images, ~3-5 GB)
	cd backend && uv run python scripts/kaggle_download.py plant-diseases

kaggle-crop-yield: ## Download crop yield dataset (replaces FAOSTAT)
	cd backend && uv run python scripts/kaggle_download.py crop-yield

kaggle-crop-recommendation: ## Download crop recommendation dataset (for REEVU)
	cd backend && uv run python scripts/kaggle_download.py crop-recommendation

kaggle-fertilizer: ## Download fertilizer prediction dataset (~500 KB)
	cd backend && uv run python scripts/kaggle_download.py fertilizer

kaggle-weather: ## Download daily climate time series dataset (~50 MB)
	cd backend && uv run python scripts/kaggle_download.py weather

kaggle-rice-diseases: ## Download rice disease image dataset (~500 MB)
	cd backend && uv run python scripts/kaggle_download.py rice-diseases

kaggle-wheat-diseases: ## Download wheat leaf disease dataset (~300 MB)
	cd backend && uv run python scripts/kaggle_download.py wheat-diseases

kaggle-indian-agriculture: ## Download Indian agriculture crop production dataset (~2 MB)
	cd backend && uv run python scripts/kaggle_download.py indian-agriculture

kaggle-download-all: ## Download all recommended Kaggle datasets
	$(MAKE) kaggle-crop-yield
	$(MAKE) kaggle-crop-recommendation
	$(MAKE) kaggle-fertilizer
	$(MAKE) kaggle-weather
	$(MAKE) kaggle-rice-diseases
	$(MAKE) kaggle-wheat-diseases
	$(MAKE) kaggle-indian-agriculture

kaggle-info: ## Get info about a Kaggle dataset (usage: make kaggle-info SLUG=owner/dataset-name)
	cd backend && uv run python scripts/kaggle_download.py info $(SLUG)

rls-drift-check: ## Fail if tenant tables lack enabled/forced RLS or registry coverage
	cd backend && uv run python scripts/check_rls_drift.py

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
	@echo "✓ PostgreSQL started. Use './dev.sh --all' for the product-development stack."

dev-redis: ## Start optional Redis service
	$(COMPOSE_CMD) --profile infra up -d redis
	@echo "✓ Redis started on localhost:6379"

dev-minio: ## Start optional MinIO service
	$(COMPOSE_CMD) --profile infra up -d minio
	@echo "✓ MinIO started on http://localhost:9001"

dev-meilisearch: ## Start optional Meilisearch service
	$(COMPOSE_CMD) --profile infra up -d meilisearch
	@echo "✓ Meilisearch started on http://localhost:7700"

dev-all: ## Start PostgreSQL plus product infra (Redis, MinIO, Meilisearch)
	$(COMPOSE_CMD) --profile infra up -d postgres redis minio meilisearch
	@echo "✓ Product infrastructure started"

dev-auth: ## Start local Keycloak identity provider and auth database
	$(COMPOSE_CMD) --profile auth up -d keycloak-postgres keycloak
	@echo "✓ Keycloak started on http://localhost:8084"

dev-auth-down: ## Stop local Keycloak identity provider
	-$(CONTAINER_RUNTIME) stop bijmantra-keycloak bijmantra-keycloak-postgres
	-$(CONTAINER_RUNTIME) rm -f bijmantra-keycloak bijmantra-keycloak-postgres
	@echo "✓ Keycloak stopped"

dev-auth-logs: ## Show local Keycloak logs
	$(COMPOSE_CMD) --profile auth logs -f keycloak

dev-beingbijmantra: ## Start explicit experimental BeingBijmantra autonomy sidecar
	$(COMPOSE_CMD) --profile beingbijmantra up -d beingbijmantra-surrealdb
	@echo "✓ Being Bijmantra sidecar started on http://localhost:$(BEINGBIJMANTRA_SURREAL_PORT)"

dev-beingbijmantra-down: ## Stop explicit experimental BeingBijmantra autonomy sidecar
	-$(CONTAINER_RUNTIME) stop beingbijmantra-surrealdb
	-$(CONTAINER_RUNTIME) rm -f beingbijmantra-surrealdb
	@echo "✓ Being Bijmantra sidecar stopped"

dev-beingbijmantra-logs: ## Show explicit experimental BeingBijmantra sidecar logs
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

bij: ## Build the Bij developer CLI
	$(MAKE) -C tools/bij bij

rust-fmt: ## Check formatting for the Rust product runtime
	cargo fmt --check

rust-check: ## Type-check the Rust product runtime
	cargo check $(RUST_PRODUCT_PACKAGES) --all-targets --locked

rust-clippy: ## Run clippy for the Rust product runtime
	cargo clippy $(RUST_PRODUCT_PACKAGES) --all-targets --locked -- -D warnings

rust-test: ## Run Rust product runtime tests
	cargo test $(RUST_PRODUCT_PACKAGES) --locked

rust-live-test: ## Print the opt-in live Postgres BrAPI read test helper
	cargo run -p bijmantra-cli -- live-test --workspace .

rust-live-test-run: ## Run the opt-in live Postgres BrAPI read fixture
	./scripts/rust_live_db.sh live-test

rust-live-db-create: ## Create the guarded disposable Rust live test database
	./scripts/rust_live_db.sh create

rust-live-db-reset: ## Reset only the guarded disposable Rust live test database
	./scripts/rust_live_db.sh reset

rust-live-db-head: ## Print Alembic heads for live Rust DB troubleshooting
	./scripts/rust_live_db.sh head

rust-live-db-migrate: ## Upgrade the guarded disposable Rust live test database to Alembic head
	./scripts/rust_live_db.sh migrate

rust-live-db-scratch-upgrade: ## Reset and upgrade a guarded scratch Rust database to Alembic head
	./scripts/rust_live_db.sh scratch-upgrade

rust-build: ## Build the release BijMantra Rust CLI/API binary
	cargo build --release --locked -p bijmantra-cli

rust-serve: ## Run the Rust API server on localhost:8000
	cargo run -p bijmantra-cli -- serve --workspace .

rust-inspect: ## Print Rust product manifest and metrics
	cargo run -p bijmantra-cli -- inspect --workspace .

rust-doctor: ## Diagnose Rust product runtime prerequisites
	cargo run -p bijmantra-cli -- doctor --workspace .

rust-services: ## List Rust product runtime services
	cargo run -p bijmantra-cli -- services --workspace .

rust-probe: ## Probe core Rust product runtime services
	cargo run -p bijmantra-cli -- probe --workspace .

rust-logs: ## Print Rust product runtime log tail commands
	cargo run -p bijmantra-cli -- logs --workspace . --group autonomy

rust-plan-dev: ## Plan Rust product runtime startup actions
	cargo run -p bijmantra-cli -- plan dev --workspace . --group infra

rust-plan-status: ## Plan/probe Rust product runtime status
	cargo run -p bijmantra-cli -- plan status --workspace . --group autonomy

rust-plan-stop: ## Plan Rust product runtime shutdown actions
	cargo run -p bijmantra-cli -- plan stop --workspace . --group infra

rust-plan-logs: ## Plan Rust product runtime log commands
	cargo run -p bijmantra-cli -- plan logs --workspace . --group autonomy

rust-dev: ## Start the ordered Rust product runtime stack
	cargo run -p bijmantra-cli -- dev --workspace . --group infra

rust-stop: ## Stop the ordered Rust product runtime stack
	cargo run -p bijmantra-cli -- stop --workspace . --group infra

rust-run-start: ## Start one Rust product runtime service, e.g. make rust-run-start SERVICE=backend
	cargo run -p bijmantra-cli -- run start $(SERVICE) --workspace .

rust-run-stop: ## Stop one Rust product runtime service, e.g. make rust-run-stop SERVICE=backend
	cargo run -p bijmantra-cli -- run stop $(SERVICE) --workspace .

rust-run-restart: ## Restart one Rust product runtime service, e.g. make rust-run-restart SERVICE=backend
	cargo run -p bijmantra-cli -- run restart $(SERVICE) --workspace .

rust-run-processes: ## List Rust product runtime tracked processes
	cargo run -p bijmantra-cli -- run processes --workspace .

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
# WASM Engine
# ============================================

wasm: ## Build Rust WASM module and copy artifacts to frontend/public/wasm/
	@if ! command -v wasm-pack > /dev/null 2>&1; then \
	    echo "⚙️  wasm-pack not found — installing..."; \
	    cargo install wasm-pack || { \
	        echo "❌ wasm-pack installation failed. Install manually: cargo install wasm-pack"; \
	        exit 1; \
	    }; \
	fi
	@cd rust && bash build.sh
	@echo "✅ WASM artifacts in frontend/public/wasm/ — restart the dev server if it is already running."

check-wasm-sync: ## Warn if WASM binary is older than Cargo.lock (exits 1 if stale)
	@LOCK=rust/Cargo.lock; \
	WASM=frontend/public/wasm/bijmantra_genomics_bg.wasm; \
	if [ ! -f "$$LOCK" ]; then \
	    echo "❌ Cargo.lock missing — run 'make wasm' to build the engine."; \
	    exit 1; \
	fi; \
	if [ ! -f "$$WASM" ]; then \
	    echo "⚠️  WASM binary missing — run 'make wasm' to build the engine."; \
	    exit 1; \
	fi; \
	if [ "$$LOCK" -nt "$$WASM" ]; then \
	    echo "⚠️  WASM binary is stale — Cargo.lock is newer than the binary. Run 'make wasm' to rebuild."; \
	    exit 1; \
	fi; \
	echo "✅ WASM binary is up to date."

test-wasm-props: ## Run property-based tests for the WASM genomics engine (native target)
	cd rust && cargo test --test genomics_props

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

db-seed: ## Seed deterministic Demo Organization data (development)
	cd backend && uv run python -m app.db.seed --env=dev --scope=system --only=admin_user
	cd backend && uv run python -m app.db.seed --env=dev --scope=system --only=reference_data
	cd backend && SEED_DEMO_DATA=true uv run python -m app.db.seed --env=dev
	@echo "✓ Demo data seeded"

db-seed-test: ## Seed deterministic Demo Organization fixtures for tests
	cd backend && uv run python -m app.db.seed --env=test --scope=system --only=admin_user
	cd backend && uv run python -m app.db.seed --env=test --scope=system --only=reference_data
	cd backend && SEED_DEMO_DATA=true uv run python -m app.db.seed --env=test
	@echo "✓ Test fixtures seeded"

db-seed-clear: ## Clear Demo Organization seeded data only
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
	@echo "Frontend:        http://localhost:5656"
	@echo "Backend API:     http://localhost:8000"
	@echo "API Docs:        http://localhost:8000/docs"
	@echo "PostgreSQL:      localhost:5432"
	@echo "Redis:           localhost:6379 (optional)"
	@echo "MinIO Console:   http://localhost:9001 (optional)"
	@echo "MinIO API:       http://localhost:9000 (optional)"
	@echo "Meilisearch:     http://localhost:7700 (optional)"
	@echo "Keycloak:        http://localhost:8084 (optional auth)"
	@echo "Being Sidecar:   http://localhost:$(BEINGBIJMANTRA_SURREAL_PORT) (experimental, explicit)"

# ============================================
# Development Environment (Product Infra + Tools)
# ============================================

dev-full: ## Start product infra plus local dev tools
	$(COMPOSE_CMD) --profile infra --profile tools up -d
	@echo "✓ Product infra and development tools started"

dev-tools: ## Start dev tools (Adminer, Redis Commander, OmShriMaatreNamahaDB)
	$(COMPOSE_CMD) --profile infra --profile tools up -d
	@echo "✓ Development tools started"
	@echo "Adminer:         http://localhost:8080"
	@echo "Redis Commander: http://localhost:8081"
	@echo "OmShriMaatreNamahaDB: http://localhost:8082"

dev-down: ## Stop all development services
	$(COMPOSE_CMD) --profile infra --profile auth --profile tools --profile beingbijmantra --profile chloe down
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
	$(COMPOSE_CMD) --profile infra --profile auth --profile tools --profile beingbijmantra --profile chloe down -v --rmi local
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
