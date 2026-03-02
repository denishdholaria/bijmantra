# InitializeApp.ps1 - One-click setup for Bijmantra on Windows
# Prepares the environment so you can just press "Play" in Podman Desktop.

$ErrorActionPreference = "Stop"

Write-Host "🌱 Bijmantra Initialization" -ForegroundColor Green
Write-Host "==========================="
Write-Host ""

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

Write-Host "✓ Using $CONTAINER_CMD and $COMPOSE_CMD" -ForegroundColor Green

# 2. Prepare Environment
if (-not (Test-Path .env)) {
    Write-Host "📝 Creating .env file..."
    Copy-Item .env.example .env
} else {
    Write-Host "✓ .env file exists"
}

# 3. Build & Pull Images
Write-Host "🔨 Building and pulling containers (this may take a while)..."
Invoke-Expression "$COMPOSE_CMD -f compose.full.yaml build"
Invoke-Expression "$COMPOSE_CMD -f compose.full.yaml pull"

# 4. Database Setup & Migrations
Write-Host "🐘 Starting database for initialization..."
Invoke-Expression "$COMPOSE_CMD -f compose.full.yaml up -d postgres redis"

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

Write-Host "🔄 Running database migrations..."
Invoke-Expression "$COMPOSE_CMD -f compose.full.yaml run --rm backend alembic upgrade head"

Write-Host "🌱 Seeding database (if needed)..."
try {
    Invoke-Expression "$COMPOSE_CMD -f compose.full.yaml run --rm backend python app/db_seed.py"
} catch {
    # Ignore seeding errors if data exists
}

# 5. Cleanup
Write-Host "🛑 Stopping initialization services..."
Invoke-Expression "$COMPOSE_CMD -f compose.full.yaml down"

Write-Host ""
Write-Host "✅ Setup complete!" -ForegroundColor Green
Write-Host "===================================================="
Write-Host "1. Open Podman Desktop"
Write-Host "2. Find the 'bijmantra' (or 'compose.full') container group"
Write-Host "3. Press the ▶️ (Play) button to start the app"
Write-Host "===================================================="
