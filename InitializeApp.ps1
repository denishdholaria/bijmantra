# InitializeApp.ps1 - First-time setup for Bijmantra on Windows.
# Prepares the local development environment; it is not the daily startup script.
# THIS SCRIPT MAY NEED UPDATE (DATE: 2026-MAY-28) AS IT FOR WINDOWS, I HAVE NOT TESTED IT.
# After running this, use Git Bash or WSL to run: ./dev.sh

$ErrorActionPreference = "Stop"

Write-Host "🌱 Bijmantra Initialization" -ForegroundColor Green
Write-Host "==========================="
Write-Host ""

$RepoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $RepoRoot

# ── Check Prerequisites ──────────────────────────────────────────────

# Container runtime
if (Get-Command podman -ErrorAction SilentlyContinue) {
    $CONTAINER_CMD = "podman"
    if (Get-Command podman-compose -ErrorAction SilentlyContinue) {
        $COMPOSE_CMD = "podman-compose"
    } elseif ((podman compose version) -match "version") {
        $COMPOSE_CMD = "podman compose"
    } else {
        Write-Error "❌ Podman Compose is missing. Please install it."
        exit 1
    }
} elseif (Get-Command docker -ErrorAction SilentlyContinue) {
    $CONTAINER_CMD = "docker"
    $COMPOSE_CMD = "docker compose"
} else {
    Write-Error "❌ Neither Podman nor Docker found. Please install Podman Desktop."
    exit 1
}

# uv (Python package manager)
if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    Write-Host "📦 Installing uv..."
    Invoke-Expression "powershell -ExecutionPolicy ByPass -c `"irm https://astral.sh/uv/install.ps1 | iex`""
}

# Node.js
if (-not (Get-Command node -ErrorAction SilentlyContinue)) {
    Write-Error "❌ Node.js is missing. Please install Node.js 18+ first."
    exit 1
}

# Bun
if (-not (Get-Command bun -ErrorAction SilentlyContinue)) {
    Write-Host "⚠️  Bun not found. Install it: npm install -g bun"
}

Write-Host "✓ Using $CONTAINER_CMD and $COMPOSE_CMD" -ForegroundColor Green
Write-Host "✓ Using uv for Python dependency management" -ForegroundColor Green

# ── Prepare Environment ──────────────────────────────────────────────

if (-not (Test-Path .env)) {
    if (Test-Path .env.example) {
        Write-Host "📝 Creating .env file from template..."
        Copy-Item .env.example .env
    }
} else {
    Write-Host "✓ .env file exists"
}

# ── Build and Start Infrastructure ───────────────────────────────────

Write-Host "🔨 Building PostgreSQL image with PostGIS + pgvector..."
Invoke-Expression "$COMPOSE_CMD build postgres"

Write-Host "🐘 Starting PostgreSQL..."
Invoke-Expression "$COMPOSE_CMD up -d postgres"

Write-Host "⏳ Waiting for PostgreSQL to be ready..."
for ($i = 0; $i -lt 30; $i++) {
    try {
        Invoke-Expression "$CONTAINER_CMD exec bijmantra-postgres pg_isready -U bijmantra_user -d bijmantra_db" | Out-Null
        Write-Host "✓ PostgreSQL is ready" -ForegroundColor Green
        break
    } catch {
        Start-Sleep -Seconds 2
    }
}

# ── Backend Setup (uv) ──────────────────────────────────────────────

Write-Host ""
Write-Host "🐍 Installing backend dependencies with uv..."
Push-Location backend
Invoke-Expression "uv sync --extra dev --extra analytics --extra geo"

Write-Host "🔄 Running database migrations..."
Invoke-Expression "uv run alembic upgrade head"

Write-Host "🌱 Seeding database..."
try {
    Invoke-Expression "uv run python -m app.db.seed --env=dev"
} catch {
    Write-Host "Seed step skipped or already applied."
}
Pop-Location

# ── Frontend Setup ───────────────────────────────────────────────────

Write-Host ""
Write-Host "⚛️  Installing frontend dependencies..."
Push-Location frontend
Invoke-Expression "bun install"
Pop-Location

# ── Done ─────────────────────────────────────────────────────────────

Write-Host ""
Write-Host "✅ Setup complete!" -ForegroundColor Green
Write-Host "===================================================="
Write-Host ""
Write-Host "Daily development (Git Bash or WSL):"
Write-Host "  ./dev.sh              # PostgreSQL + backend + frontend"
Write-Host "  ./dev.sh --all        # + Redis, MinIO, Meilisearch, SurrealDB"
Write-Host "  ./dev.sh --stop       # stop everything"
Write-Host ""
Write-Host "Or manually in PowerShell:"
Write-Host "  $COMPOSE_CMD up -d postgres"
Write-Host "  cd backend; uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
Write-Host "  cd frontend; bun run dev"
Write-Host "===================================================="
