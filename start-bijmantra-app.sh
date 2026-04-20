#!/bin/bash

# Bijmantra main application startup script.
# Starts the app development stack only.
# The private OpenClaw runtime is separate and should be started with
# ops-private/claw-runtime/scripts/bjm-start.sh when needed.

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "🌱 Starting Bijmantra app..."
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Check for podman or docker
if [ -x "/opt/podman/bin/podman" ]; then
    CONTAINER_CMD="/opt/podman/bin/podman"
elif command -v podman &> /dev/null; then
    CONTAINER_CMD="podman"
elif command -v docker &> /dev/null; then
    CONTAINER_CMD="docker"
else
    echo "❌ Error: Neither podman nor docker found. Please install one."
    exit 1
fi

echo -e "${YELLOW}Using: $CONTAINER_CMD${NC}"
echo ""
echo "This script starts the main BijMantra app stack."
echo "For the private runtime stack, use ops-private/claw-runtime/scripts/bjm-start.sh."
echo ""

# Set compose command (podman compose or docker compose)
if [[ "$CONTAINER_CMD" == *"podman"* ]]; then
    COMPOSE_CMD="$CONTAINER_CMD compose"
else
    COMPOSE_CMD="$CONTAINER_CMD compose"
fi

OPTIONAL_SERVICES_RAW="${BIJMANTRA_OPTIONAL_SERVICES:-}"
OPTIONAL_SERVICES_RAW="${OPTIONAL_SERVICES_RAW//,/ }"
SERVICES_TO_START=(postgres)
OPTIONAL_ENABLED=()

add_optional_service() {
    local service="$1"
    local existing
    for existing in "${SERVICES_TO_START[@]}"; do
        if [ "$existing" = "$service" ]; then
            return
        fi
    done
    SERVICES_TO_START+=("$service")
    OPTIONAL_ENABLED+=("$service")
}

for service in $OPTIONAL_SERVICES_RAW; do
    case "$service" in
        all)
            add_optional_service redis
            add_optional_service minio
            add_optional_service meilisearch
            ;;
        redis|minio|meilisearch)
            add_optional_service "$service"
            ;;
        "")
            ;;
        *)
            echo "❌ Error: Unknown optional service '$service'. Use redis, minio, meilisearch, or all."
            exit 1
            ;;
    esac
done

if [ ${#OPTIONAL_ENABLED[@]} -eq 0 ]; then
    echo "Optional services: none"
    echo "Enable Redis, MinIO, or Meilisearch later with BIJMANTRA_OPTIONAL_SERVICES=\"redis minio meilisearch\"."
else
    echo "Optional services enabled: ${OPTIONAL_ENABLED[*]}"
fi
echo ""

# 1. Build PostgreSQL image if needed (includes PostGIS + pgvector)
if ! $CONTAINER_CMD image exists bijmantra-postgres:latest 2>/dev/null; then
    echo "🔨 Building PostgreSQL image with PostGIS + pgvector..."
    $COMPOSE_CMD build postgres
fi

# 2. Start Infrastructure Services
echo "📦 Starting infrastructure: ${SERVICES_TO_START[*]}"
if ! $COMPOSE_CMD up -d "${SERVICES_TO_START[@]}"; then
    echo ""
    echo "❌ Failed to start main infrastructure services."
    echo "If Podman reports a proxy or port conflict, inspect running containers with:"
    echo "  $CONTAINER_CMD ps -a --format '{{.Names}}\t{{.Status}}\t{{.Ports}}'"
    echo "The main app always uses host port 5432 for PostgreSQL."
    echo "Optional services use 6379 (Redis), 9000/9001 (MinIO), and 7700 (Meilisearch) when enabled."
    echo ""
    exit 1
fi
sleep 3

# Wait for PostgreSQL to be ready
echo "⏳ Waiting for PostgreSQL..."
for i in {1..30}; do
    if $CONTAINER_CMD exec bijmantra-postgres pg_isready -U bijmantra_user -d bijmantra_db &> /dev/null; then
        echo -e "${GREEN}✓ PostgreSQL is ready (with PostGIS + pgvector)${NC}"
        break
    fi
    sleep 1
done

# 3. Run migrations
echo ""
echo "🔄 Running database migrations..."
cd backend
source venv/bin/activate
export PYTHONPATH=.
export POSTGRES_SERVER=localhost
export POSTGRES_PORT=5432
export POSTGRES_USER=bijmantra_user
export POSTGRES_PASSWORD=changeme_in_production
export POSTGRES_DB=bijmantra_db
export GOOGLE_APPLICATION_CREDENTIALS=$(pwd)/bijmantra-sa-key.json

venv/bin/python -m alembic upgrade head
PYTHONPATH=. venv/bin/python app/db_seed.py 2>/dev/null || true

# Initialize vector store extension
echo "🧠 Initializing vector store..."
$CONTAINER_CMD exec bijmantra-postgres psql -U bijmantra_user -d bijmantra_db -c "CREATE EXTENSION IF NOT EXISTS vector;" 2>/dev/null || true

# 4. Start Backend
echo ""
echo "🚀 Starting Backend API..."
export DYLD_FALLBACK_LIBRARY_PATH=/opt/homebrew/lib:$DYLD_FALLBACK_LIBRARY_PATH
venv/bin/python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
cd ..
sleep 2

# 5. Start Frontend
echo ""
echo "🎨 Starting Frontend..."
cd frontend
bun run dev &
FRONTEND_PID=$!
cd ..

echo ""
echo -e "${GREEN}════════════════════════════════════════════${NC}"
echo -e "${GREEN}  🌱 Bijmantra is running!${NC}"
echo -e "${GREEN}════════════════════════════════════════════${NC}"
echo ""
echo "  Frontend:     http://localhost:5173"
echo "  Backend:      http://localhost:8000"
echo "  API Docs:     http://localhost:8000/docs"
if [[ " ${OPTIONAL_ENABLED[*]} " == *" meilisearch "* ]]; then
    echo "  Meilisearch:  http://localhost:7700"
fi
if [[ " ${OPTIONAL_ENABLED[*]} " == *" minio "* ]]; then
    echo "  MinIO:        http://localhost:9001"
fi
if [ ${#OPTIONAL_ENABLED[@]} -eq 0 ]; then
    echo "  Optional infra: disabled by default"
fi

echo ""
echo "  🪷 Veena AI:   Click the lotus button in bottom-right"
echo "  🔍 Vector:     /api/v2/vector/search/simple?q=your+query"
echo ""
echo "  Create user:  make create-user"
echo "  Optional infra: BIJMANTRA_OPTIONAL_SERVICES=\"redis minio meilisearch\" bash ./start-bijmantra-app.sh"
echo ""
echo "  Press ⌘K to open Command Palette"
echo "  Press Ctrl+C to stop all services"
echo ""

# Handle shutdown
cleanup() {
    echo ""
    echo "🛑 Stopping Bijmantra..."
    kill $BACKEND_PID 2>/dev/null || true
    kill $FRONTEND_PID 2>/dev/null || true
    $COMPOSE_CMD down
    echo "👋 Goodbye!"
    exit 0
}

trap cleanup SIGINT SIGTERM

# Keep script running
wait