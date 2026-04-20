# InitializeApp.ps1 - First-time setup for Bijmantra on Windows.
# Prepares the local development environment; it is not the daily startup script.

$ErrorActionPreference = "Stop"

Write-Host "🌱 Bijmantra Initialization" -ForegroundColor Green
Write-Host "==========================="
Write-Host ""

$RepoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $RepoRoot

# 1. Check Prerequisites
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

if (Get-Command py -ErrorAction SilentlyContinue) {
    $PYTHON_CMD = "py -3"
} elseif (Get-Command python -ErrorAction SilentlyContinue) {
    $PYTHON_CMD = "python"
} else {
    Write-Error "❌ Python 3 is missing. Please install Python 3.11+ first."
    exit 1
}

if (-not (Get-Command node -ErrorAction SilentlyContinue)) {
    Write-Error "❌ Node.js is missing. Please install Node.js first."
    exit 1
}

if (-not (Get-Command npm -ErrorAction SilentlyContinue)) {
    Write-Error "❌ npm is missing. Please install Node.js/npm first."
    exit 1
}

Write-Host "✓ Using $CONTAINER_CMD and $COMPOSE_CMD" -ForegroundColor Green
Write-Host "✓ Using $PYTHON_CMD for Python" -ForegroundColor Green

# 2. Prepare Environment
if (-not (Test-Path .env)) {
    Write-Host "📝 Creating .env file..."
    Copy-Item .env.example .env
} else {
    Write-Host "✓ .env file exists"
}

# 3. Build infrastructure image and start infra
Write-Host "🔨 Building PostgreSQL image with PostGIS + pgvector..."
Invoke-Expression "$COMPOSE_CMD build postgres"

Write-Host "🐘 Starting infrastructure for initialization..."
Invoke-Expression "$COMPOSE_CMD up -d postgres redis minio meilisearch"

Write-Host "⏳ Waiting for PostgreSQL to be ready..."
for ($i = 0; $i -lt 30; $i++) {
    try {
        Invoke-Expression "$CONTAINER_CMD exec bijmantra-postgres pg_isready -U bijmantra_user -d bijmantra_db" | Out-Null
        Write-Host "✓ PostgreSQL is ready"
        break
    } catch {
        Start-Sleep -Seconds 2
    }
}

if (-not (Test-Path "backend\venv")) {
    Write-Host "🐍 Creating backend virtual environment..."
    Invoke-Expression "$PYTHON_CMD -m venv backend\venv"
}

Write-Host "📦 Installing backend dependencies..."
Invoke-Expression "backend\venv\Scripts\python.exe -m pip install --upgrade pip"
Invoke-Expression "backend\venv\Scripts\python.exe -m pip install -r backend\requirements.txt"

Write-Host "🔄 Running database migrations..."
Push-Location backend
$env:PYTHONPATH = "."
Invoke-Expression ".\venv\Scripts\python.exe -m alembic upgrade head"

Write-Host "🌱 Seeding database (if needed)..."
try {
    Invoke-Expression ".\venv\Scripts\python.exe -m app.db.seed --env=dev"
} catch {
    Write-Host "Seed step skipped or already applied."
}
Pop-Location

Write-Host "⚛️ Installing frontend dependencies..."
Push-Location frontend
Invoke-Expression "bun install"
Pop-Location

Write-Host ""
Write-Host "✅ Setup complete!" -ForegroundColor Green
Write-Host "===================================================="
Write-Host "This script prepared the local development environment."
Write-Host ""
Write-Host "Recommended developer flow:"
Write-Host "1. Start infrastructure: $COMPOSE_CMD up -d postgres redis minio meilisearch"
Write-Host "2. Start backend: cd backend; .\venv\Scripts\Activate.ps1; uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
Write-Host "3. Start frontend: cd frontend; bun run dev"
Write-Host ""
Write-Host "If you use Git Bash or WSL, you can also use: bash ./start-bijmantra-app.sh"
Write-Host "===================================================="
