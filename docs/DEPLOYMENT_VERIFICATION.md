# Deployment Verification Instructions

**Purpose**: Verify backend API endpoints and frontend pages before deployment.

**Last Verified**: December 23, 2025  
**Verified Count**: 1143 API endpoints

---

## Quick Verification Commands

### 1. Count All API Endpoints

```bash
# Count endpoints in api/ directory
grep -r "@router\." backend/app/api/ --include="*.py" | grep -E "\.(get|post|put|patch|delete)\(" | wc -l

# Count endpoints in modules/ directory  
grep -r "@router\." backend/app/modules/ --include="*.py" | grep -E "\.(get|post|put|patch|delete)\(" | wc -l

# Count endpoints in main.py (root endpoints)
grep -r "@app\." backend/app/main.py | grep -E "\.(get|post|put|patch|delete)\(" | wc -l

# TOTAL = sum of above three commands
```

**Expected Result (Dec 23, 2025)**: ~1143 total endpoints

### 2. List All Routers Registered

```bash
# Count router registrations in main.py
grep "app.include_router" backend/app/main.py | wc -l
```

**Expected Result**: ~85 routers

### 3. Verify Backend Starts

```bash
cd backend
source venv/bin/activate
python -c "from app.main import app; print('✅ Backend imports successfully')"
```

### 4. Verify Frontend Builds

```bash
cd frontend
npm run build
# Should complete with 0 errors
# Check for "✓ built in Xs" message
```

### 5. Count Frontend Pages

```bash
# Count page components
find frontend/src -name "*.tsx" -path "*/pages/*" | wc -l

# Count routes in App.tsx
grep -E "path=|<Route" frontend/src/App.tsx | wc -l
```

**Expected Result**: ~301 pages

---

## Detailed Endpoint Breakdown

### By Directory

| Directory | Endpoints | Description |
|-----------|-----------|-------------|
| `backend/app/api/v2/` | ~600 | Custom v2 API endpoints |
| `backend/app/api/brapi/` | ~450 | BrAPI v2.1 endpoints |
| `backend/app/api/v2/core/` | ~50 | Core BrAPI endpoints |
| `backend/app/modules/` | ~37 | Division module endpoints |
| `backend/app/main.py` | 4 | Root endpoints (/, /health, etc.) |

### Verify Specific Modules

```bash
# Count endpoints per file
for f in backend/app/api/v2/*.py; do
  count=$(grep -E "@router\.(get|post|put|patch|delete)\(" "$f" 2>/dev/null | wc -l)
  if [ "$count" -gt 0 ]; then
    echo "$f: $count"
  fi
done
```

---

## API Health Check Script

Create `scripts/verify_api.py`:

```python
#!/usr/bin/env python3
"""Verify all API endpoints are registered and accessible."""
import sys
sys.path.insert(0, 'backend')

from app.main import app

# Get all routes
routes = []
for route in app.routes:
    if hasattr(route, 'path'):
        routes.append(route.path)
    if hasattr(route, 'routes'):
        for subroute in route.routes:
            if hasattr(subroute, 'path'):
                routes.append(f"{route.path}{subroute.path}")

print(f"Total registered routes: {len(routes)}")
print(f"\nSample routes:")
for r in sorted(routes)[:20]:
    print(f"  {r}")
```

Run with:
```bash
cd backend && python ../scripts/verify_api.py
```

---

## Pre-Deployment Checklist

### Backend
- [ ] All routers imported in `main.py`
- [ ] All routers registered with `app.include_router()`
- [ ] No import errors: `python -c "from app.main import app"`
- [ ] API docs accessible: `http://localhost:8000/docs`
- [ ] Health check passes: `curl http://localhost:8000/health`

### Frontend
- [ ] Build completes: `npm run build`
- [ ] No TypeScript errors
- [ ] PWA manifest generated
- [ ] Service worker generated

### Database
- [ ] All migrations applied: `alembic upgrade head`
- [ ] Demo data seeded (if needed): `python -m app.db.seed`

---

## Endpoint Count History

| Date | Endpoints | Notes |
|------|-----------|-------|
| Dec 23, 2025 | 1143 | Added phenology, plot-history, statistics |
| Dec 22, 2025 | 1128 | Added field-scanner, label-printing, quick-entry |
| Dec 20, 2025 | 1099 | BrAPI 100% complete |
| Dec 17, 2025 | 935 | Initial forensic audit |

---

## Troubleshooting

### "Module not found" errors
```bash
# Check if module exists
ls backend/app/api/v2/<module_name>.py

# Check if imported in main.py
grep "<module_name>" backend/app/main.py
```

### Router not appearing in /docs
1. Check import statement in `main.py`
2. Check `app.include_router()` call
3. Verify router has `prefix` and `tags`

### Endpoint count mismatch
```bash
# Detailed count with file names
grep -r "@router\." backend/app/api/ --include="*.py" -l | while read f; do
  count=$(grep -E "@router\.(get|post|put|patch|delete)\(" "$f" | wc -l)
  echo "$count $f"
done | sort -rn | head -20
```

---

## Automated Verification (CI/CD)

Add to GitHub Actions:

```yaml
- name: Verify API Endpoints
  run: |
    count=$(grep -r "@router\." backend/app/api/ --include="*.py" | grep -E "\.(get|post|put|patch|delete)\(" | wc -l)
    echo "API Endpoints: $count"
    if [ "$count" -lt 1100 ]; then
      echo "❌ Endpoint count too low!"
      exit 1
    fi
    echo "✅ Endpoint count verified"

- name: Verify Backend Imports
  run: |
    cd backend
    python -c "from app.main import app; print('✅ Backend OK')"

- name: Verify Frontend Build
  run: |
    cd frontend
    npm run build
```

---

*Document created: December 23, 2025*
*Purpose: Prevent hallucinated endpoint counts*
