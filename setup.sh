#!/bin/bash

# Bijmantra Setup Script
# Automated first-time setup for the local development environment.

set -e

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

echo "🌱 Bijmantra Setup Script"
echo "=========================="
echo ""

# Check if podman is installed
if [ -x "/opt/podman/bin/podman" ]; then
    CONTAINER_CMD="/opt/podman/bin/podman"
elif command -v podman &> /dev/null; then
    CONTAINER_CMD="podman"
elif command -v docker &> /dev/null; then
    CONTAINER_CMD="docker"
else
    echo "❌ Neither Podman nor Docker is installed. Please install Podman first."
    echo "   Visit: https://podman.io/getting-started/installation"
    exit 1
fi

COMPOSE_CMD="$CONTAINER_CMD compose"
OPTIONAL_SERVICES_RAW="${BIJMANTRA_OPTIONAL_SERVICES:-}"
OPTIONAL_SERVICES_RAW="${OPTIONAL_SERVICES_RAW//,/ }"
SERVICES_TO_START=(postgres)

add_optional_service() {
    local service="$1"
    local existing
    for existing in "${SERVICES_TO_START[@]}"; do
        if [ "$existing" = "$service" ]; then
            return
        fi
    done
    SERVICES_TO_START+=("$service")
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
            echo "❌ Unknown optional service '$service'. Use redis, minio, meilisearch, or all."
            exit 1
            ;;
    esac
done

# Check if python3 is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.15+ first."
    exit 1
fi

# Check if node is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js 18+ first."
    exit 1
fi

echo "✓ Core prerequisites check passed"
echo "✓ Using container runtime: $CONTAINER_CMD"
echo ""

# Check for HPC compute prerequisites (optional but recommended)
echo "🔬 Checking HPC compute prerequisites..."
HPC_READY=true

# Check for Rust (for FFI layer)
if command -v rustc &> /dev/null; then
    RUST_VERSION=$(rustc --version | cut -d' ' -f2)
    echo "✓ Rust $RUST_VERSION found"
else
    echo "⚠️  Rust not found (optional - needed for WASM genomics)"
    echo "   Install: curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh"
    HPC_READY=false
fi

# Check for Fortran compiler (for HPC compute engine)
if command -v gfortran &> /dev/null; then
    GFORTRAN_VERSION=$(gfortran --version | head -1)
    echo "✓ $GFORTRAN_VERSION"
else
    echo "⚠️  gfortran not found (optional - needed for HPC compute)"
    echo "   Install on macOS: brew install gcc"
    echo "   Install on Ubuntu: sudo apt install gfortran"
    HPC_READY=false
fi

# Check for CMake (for building Fortran modules)
if command -v cmake &> /dev/null; then
    CMAKE_VERSION=$(cmake --version | head -1)
    echo "✓ $CMAKE_VERSION"
else
    echo "⚠️  CMake not found (optional - needed to build Fortran modules)"
    echo "   Install on macOS: brew install cmake"
    echo "   Install on Ubuntu: sudo apt install cmake"
    HPC_READY=false
fi

# Check for wasm-pack (for browser-side genomics)
if command -v wasm-pack &> /dev/null; then
    echo "✓ wasm-pack found"
else
    echo "⚠️  wasm-pack not found (optional - needed for browser WASM)"
    echo "   Install: cargo install wasm-pack"
    HPC_READY=false
fi

if [ "$HPC_READY" = true ]; then
    echo ""
    echo "✓ All HPC prerequisites available - full compute capabilities enabled"
else
    echo ""
    echo "ℹ️  Some HPC tools missing - basic functionality will work"
    echo "   Install missing tools for full Fortran/WASM compute capabilities"
fi
echo ""

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    if [ -f .env.example ]; then
        echo "📝 Creating .env file from template..."
        cp .env.example .env
        echo "✓ .env file created"
        echo "⚠️  Please review and update .env file with your settings"
        echo ""
    else
        echo "ℹ️  No .env.example found. Continuing with built-in development defaults and environment variables."
        echo ""
    fi
fi

# Build custom PostgreSQL image with PostGIS + pgvector
echo "🔨 Building PostgreSQL image with PostGIS + pgvector..."
$COMPOSE_CMD build postgres

# Start infrastructure
echo "🚀 Starting infrastructure (${SERVICES_TO_START[*]})..."
$COMPOSE_CMD up -d "${SERVICES_TO_START[@]}"

echo "⏳ Waiting for PostgreSQL to be ready..."
for i in {1..30}; do
    if $CONTAINER_CMD exec bijmantra-postgres pg_isready -U bijmantra_user -d bijmantra_db &> /dev/null; then
        echo "✓ PostgreSQL is ready"
        break
    fi
    sleep 1
done

# Verify pgvector extension
echo "🔍 Verifying pgvector extension..."
$CONTAINER_CMD exec bijmantra-postgres psql -U bijmantra_user -d bijmantra_db -c "SELECT extname, extversion FROM pg_extension WHERE extname IN ('vector', 'postgis');" 2>/dev/null || echo "   Extensions will be created on first migration"

# Backend setup
echo ""
echo "🐍 Setting up backend..."
cd backend

if [ ! -d "venv" ]; then
    echo "   Creating virtual environment..."
    python3 -m venv venv
fi

echo "   Activating virtual environment..."
source venv/bin/activate

echo "   Installing dependencies..."
pip install -q --upgrade pip
pip install -q -r requirements.txt

echo "   Running database migrations..."
export PYTHONPATH=.
venv/bin/python -m alembic upgrade head

echo "   Initializing vector store..."
# Vector store will be initialized on first API call or can be done manually

echo "   Seeding database..."
python -m app.db.seed --env=dev

cd ..

# Frontend setup
echo ""
echo "⚛️  Setting up frontend..."
cd frontend

if [ ! -d "node_modules" ]; then
    echo "   Installing dependencies..."
    bun install
fi

cd ..

# Build HPC compute modules (if prerequisites available)
if [ "$HPC_READY" = true ]; then
    echo ""
    echo "🚀 Building HPC compute modules..."
    
    # Build Fortran modules
    if [ -d "fortran" ] && command -v gfortran &> /dev/null && command -v cmake &> /dev/null; then
        echo "   Building Fortran HPC kernels..."
        cd fortran
        mkdir -p build
        cd build
        cmake .. -DCMAKE_BUILD_TYPE=Release 2>/dev/null && make -j$(nproc 2>/dev/null || sysctl -n hw.ncpu) 2>/dev/null && echo "   ✓ Fortran modules built" || echo "   ⚠️  Fortran build skipped (missing dependencies)"
        cd ../..
    fi
    
    # Build Rust FFI layer
    if [ -d "rust" ] && command -v cargo &> /dev/null; then
        echo "   Building Rust FFI layer..."
        cd rust
        cargo build --release 2>/dev/null && echo "   ✓ Rust FFI built" || echo "   ⚠️  Rust build skipped"
        cd ..
    fi
    
    # Build WASM modules
    if [ -d "rust" ] && command -v wasm-pack &> /dev/null; then
        echo "   Building WASM genomics modules..."
        cd rust
        wasm-pack build --target web --out-dir ../frontend/src/wasm/pkg 2>/dev/null && echo "   ✓ WASM modules built" || echo "   ⚠️  WASM build skipped"
        cd ..
    fi
else
    echo ""
    echo "ℹ️  Skipping HPC build (missing prerequisites)"
    echo "   The app will use Python/NumPy fallback for computations"
fi

echo ""
# Install shell welcome tips (idempotent)
WELCOME_LINE='[ -f "'$ROOT_DIR'/scripts/dev_tips.sh" ] && source "'$ROOT_DIR'/scripts/dev_tips.sh"'
if [ -f "$HOME/.bashrc" ] && ! grep -Fq "$WELCOME_LINE" "$HOME/.bashrc"; then
    echo "$WELCOME_LINE" >> "$HOME/.bashrc"
fi

echo "✅ Setup completed successfully!"
echo ""
echo "📚 Next steps:"
echo ""
echo "1. Safe main app startup:"
echo "   bash ./start-bijmantra-app.sh"
echo ""
echo "2. Developer flow with split terminals:"
echo "   make dev"
echo "   make dev-backend"
echo "   make dev-frontend"
echo "   # Optional: make dev-redis / make dev-minio / make dev-meilisearch / make dev-all"
echo ""
echo "3. Access the application:"
echo "   - Frontend: http://localhost:5173"
echo "   - Backend API: http://localhost:8000"
echo "   - API Docs: http://localhost:8000/docs"
echo ""
echo "4. Create your first user if needed:"
echo "   make create-user"
echo ""
echo "🔬 HPC Compute Engine:"
if [ "$HPC_READY" = true ]; then
    echo "   ✓ Fortran HPC kernels available (BLUP, GBLUP, REML)"
    echo "   ✓ Rust FFI layer available"
    echo "   ✓ WASM browser genomics available"
else
    echo "   ⚠️  Using Python/NumPy fallback (install Rust + gfortran for full HPC)"
fi
echo ""
echo "🪷 Veena AI Assistant:"
echo "   Click the lotus button (🪷) in the bottom-right corner"
echo "   Or say 'Hey Veena' with voice commands enabled"
echo ""
