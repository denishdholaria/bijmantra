#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

echo "🌱 Seeding full workstation (DB, Redis, Surreal, Veena)"

# Core infra
make dev || true

# Backend seed
if [ -d backend/venv ]; then
  source backend/venv/bin/activate
fi
python -m backend.app.db.seed --env=dev || python -m app.db.seed --env=dev || true

# Redis warm-up
python - <<'PY'
try:
    import redis
    r = redis.Redis(host='localhost', port=6379, decode_responses=True)
    r.set('bijmantra:dev:hello', 'ready')
    print('✓ Redis seeded')
except Exception as exc:
    print(f'⚠ Redis seed skipped: {exc}')
PY

# Surreal placeholder bootstrap
if command -v surreal >/dev/null 2>&1; then
  echo "DEFINE TABLE dev_notes;" | surreal sql --conn http://localhost:8001 --user root --pass root >/dev/null || true
  echo "✓ Surreal seeded"
else
  echo "⚠ Surreal CLI not found; skipped"
fi

# Veena placeholder cache file
mkdir -p backend/.veena
cat > backend/.veena/bootstrap.json <<'JSON'
{"persona":"veena","status":"seeded","createdBy":"seed_full_workstation.sh"}
JSON

echo "✅ Workstation seed completed"
