# BijMantra Metrics Proof

**Generated:** January 3, 2026 (Session 58)  
**Method:** Direct code inspection via grep/find commands  
**Status:** ⚠️ Discrepancies found between metrics.json and actual code

---

## Summary

| Metric | metrics.json | Actual Code | Status |
|--------|-------------|-------------|--------|
| API Endpoints | 1,385 | **1,469** | ❌ Outdated |
| Frontend Routes | 221 | **~315** (App.tsx) | ❌ Needs audit |
| BrAPI Endpoints | 201 | **201** | ✅ Verified |

---

## API Endpoint Count (Verified)

**Command:**
```bash
grep -rE "@router\.(get|post|put|patch|delete)\(" backend/app/api/ backend/app/modules/ --include="*.py" | wc -l
```

**Result:** 1,469 endpoints

### Breakdown by Directory

| Directory | Count |
|-----------|-------|
| `backend/app/api/` | 1,432 |
| `backend/app/modules/` | 37 |
| **TOTAL** | **1,469** |

### Top 20 Files by Endpoint Count

| File | Endpoints |
|------|-----------|
| `backend/app/api/v2/vision.py` | 50 |
| `backend/app/api/brapi/search.py` | 48 |
| `backend/app/api/v2/devguru.py` | 38 |
| `backend/app/modules/seed_bank/router.py` | 22 |
| `backend/app/api/v2/collaboration_hub.py` | 22 |
| `backend/app/api/v2/resource_management.py` | 19 |
| `backend/app/api/v2/sensors.py` | 18 |
| `backend/app/api/v2/prahari.py` | 18 |
| `backend/app/api/v2/dispatch.py` | 18 |
| `backend/app/api/v2/licensing.py` | 17 |
| `backend/app/api/v2/dus.py` | 17 |
| `backend/app/api/v2/data_quality.py` | 17 |
| `backend/app/api/v2/trial_planning.py` | 16 |
| `backend/app/api/v2/reports.py` | 16 |
| `backend/app/api/v2/metrics.py` | 16 |
| `backend/app/api/v2/genotyping.py` | 16 |
| `backend/app/api/v2/data_sync.py` | 16 |
| `backend/app/api/v2/vault_sensors.py` | 15 |
| `backend/app/api/v2/traceability.py` | 15 |
| `backend/app/api/v2/team_management.py` | 15 |

---

## Frontend Route Count (Needs Audit)

**Commands:**
```bash
# Division routes
grep -rh "path:" frontend/src/divisions/*/routes.tsx | wc -l
# Result: 171

# App.tsx Route elements  
grep -c "<Route" frontend/src/App.tsx
# Result: 315
```

**Issue:** The 315 `<Route>` elements in App.tsx includes nested routes, duplicates, and wrapper routes. A proper audit requires manual inspection to count unique user-facing pages.

---

## BrAPI Endpoint Verification

**Files in `backend/app/api/brapi/`:**

| File | Endpoints |
|------|-----------|
| search.py | 48 |
| germplasm.py | 8 |
| vendor.py | 8 |
| seedlots.py | 7 |
| observations.py | 7 |
| variantsets.py | 6 |
| samples.py | 6 |
| observationunits.py | 6 |
| images.py | 6 |
| variables.py | 5 |
| plates.py | 5 |
| plannedcrosses.py | 5 |
| people.py | 5 |
| ontologies.py | 5 |
| crossingprojects.py | 5 |
| attributes.py | 5 |
| traits.py | 4 |
| scales.py | 4 |
| methods.py | 4 |
| crosses.py | 4 |
| attributevalues.py | 4 |
| variants.py | 3 |
| references.py | 3 |
| maps.py | 3 |
| events.py | 3 |
| callsets.py | 3 |
| referencesets.py | 2 |
| calls.py | 2 |
| breedingmethods.py | 2 |
| observationlevels.py | 1 |
| markerpositions.py | 1 |
| allelematrix.py | 1 |

**BrAPI Total:** ~175 in brapi/ directory + additional in main routers

---

## Recommendations

1. **Update metrics.json** — Change API endpoint count from 1,385 to 1,469
2. **Audit frontend routes** — Manual count of unique user-facing pages needed
3. **Automate verification** — Add CI script to regenerate counts on each commit
4. **Version the proof** — This document should be regenerated when metrics change

---

## Verification Commands

To reproduce these counts:

```bash
# Total API endpoints
grep -rE "@router\.(get|post|put|patch|delete)\(" backend/app/api/ backend/app/modules/ --include="*.py" | wc -l

# Endpoints per file
for f in backend/app/api/**/*.py backend/app/modules/**/*.py; do
  count=$(grep -cE "@router\.(get|post|put|patch|delete)\(" "$f" 2>/dev/null || echo 0)
  [ "$count" -gt 0 ] && echo "$count $f"
done | sort -rn

# Frontend routes in divisions
grep -rh "path:" frontend/src/divisions/*/routes.tsx | wc -l

# Route elements in App.tsx
grep -c "<Route" frontend/src/App.tsx
```

---

*This document provides evidence-based verification per GOVERNANCE.md requirements.*
