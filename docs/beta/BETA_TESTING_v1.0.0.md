# BijMantra v1.0.0-beta.1 — Beta Testing Guide

**Version:** 1.0.0-beta.1 Prathama (प्रथम)
**Created:** December 30, 2025
**Purpose:** Systematic QA testing for beta release validation
**Role:** Senior System Architect
-----------------------------

## 📊 Code Verification Summary

**Verification Date:** December 30, 2025
**Method:** Code-Referenced Audit (per GOVERNANCE.md §4.2)

### Endpoint Verification (Code-Based)

| Category          | File(s)                                       | Endpoints Found | Status      |
| ----------------- | --------------------------------------------- | --------------- | ----------- |
| Authentication    | `backend/app/api/auth.py`                   | 3               | ✅ Verified |
| BrAPI Programs    | `backend/app/api/v2/core/programs.py`       | 5               | ✅ Verified |
| BrAPI Trials      | `backend/app/api/v2/core/trials.py`         | 5               | ✅ Verified |
| BrAPI Studies     | `backend/app/api/v2/core/studies.py`        | 5               | ✅ Verified |
| BrAPI Locations   | `backend/app/api/v2/core/locations.py`      | 5               | ✅ Verified |
| Germplasm         | `backend/app/api/brapi/germplasm.py`        | 8               | ✅ Verified |
| Crosses           | `backend/app/api/brapi/crosses.py`          | 4               | ✅ Verified |
| Seedlots          | `backend/app/api/brapi/seedlots.py`         | 7               | ✅ Verified |
| Traits            | `backend/app/api/brapi/traits.py`           | 4               | ✅ Verified |
| Variables         | `backend/app/api/brapi/variables.py`        | 5               | ✅ Verified |
| Observations      | `backend/app/api/brapi/observations.py`     | 7               | ✅ Verified |
| ObservationUnits  | `backend/app/api/brapi/observationunits.py` | 6               | ✅ Verified |
| Images            | `backend/app/api/brapi/images.py`           | 6               | ✅ Verified |
| Variants          | `backend/app/api/brapi/variants.py`         | 3               | ✅ Verified |
| CallSets          | `backend/app/api/brapi/callsets.py`         | 3               | ✅ Verified |
| References        | `backend/app/api/brapi/references.py`       | 3               | ✅ Verified |
| Vendor            | `backend/app/api/brapi/vendor.py`           | 8               | ✅ Verified |
| Seed Bank         | `backend/app/modules/seed_bank/router.py`   | 22              | ✅ Verified |
| Weather           | `backend/app/api/v2/weather.py`             | 6               | ✅ Verified |
| Field Environment | `backend/app/api/v2/field_environment.py`   | 14              | ✅ Verified |
| Sensors           | `backend/app/api/v2/sensors.py`             | 18              | ✅ Verified |
| Chat (Veena)      | `backend/app/api/v2/chat.py`                | 4               | ✅ Verified |
| DevGuru           | `backend/app/api/v2/devguru.py`             | 38              | ✅ Verified |
| Voice             | `backend/app/api/v2/voice.py`               | 5               | ✅ Verified |
| Offline Sync      | `backend/app/api/v2/offline_sync.py`        | 12              | ✅ Verified |

### Frontend Component Verification

| Component          | File                                                         | Status    |
| ------------------ | ------------------------------------------------------------ | --------- |
| Gateway Page       | `frontend/src/pages/WorkspaceGateway.tsx`                  | ✅ EXISTS |
| Workspace Store    | `frontend/src/store/workspaceStore.ts`                     | ✅ EXISTS |
| Workspace Switcher | `frontend/src/components/navigation/WorkspaceSwitcher.tsx` | ✅ EXISTS |
| Mobile Navigation  | `frontend/src/components/navigation/MobileBottomNav.tsx`   | ✅ EXISTS |
| PWA Config         | `frontend/vite.config.ts` (VitePWA)                        | ✅ EXISTS |

### Total Counts

| Metric              | Count | Source                          |
| ------------------- | ----- | ------------------------------- |
| BrAPI Endpoints     | 181   | `backend/app/api/brapi/*.py`  |
| Custom v2 Endpoints | 1,194 | `backend/app/api/v2/**/*.py`  |
| Auth Endpoints      | 3     | `backend/app/api/auth.py`     |
| Frontend Pages      | 310   | `frontend/src/**/pages/*.tsx` |

---

## 📋 Testing Overview

This document provides a structured approach to validate BijMantra v1.0.0-beta.1 before promoting to Release Candidate (RC) status.

### Version Progression

```
1.0.0-beta.1 ← YOU ARE HERE
     ↓ (Complete this testing)
1.0.0-beta.2 ← Bug fixes
     ↓
1.0.0-rc.1   ← Release Candidate
     ↓
1.0.0        ← Stable Release
```

### Testing Scope

| Category       | Items | Priority    |
| -------------- | ----- | ----------- |
| Authentication | 5     | 🔴 Critical |
| Navigation     | 6     | 🔴 Critical |
| BrAPI Core     | 7     | 🔴 Critical |
| Germplasm      | 5     | 🟡 High     |
| Phenotyping    | 5     | 🟡 High     |
| Genotyping     | 5     | 🟡 High     |
| Seed Bank      | 5     | 🟡 High     |
| Environment    | 4     | 🟢 Medium   |
| AI Features    | 4     | 🟢 Medium   |
| Offline/PWA    | 4     | 🟢 Medium   |

---

## 🔐 1. Authentication Testing

### Prerequisites

- Backend running: `make dev-backend` (http://localhost:8000)
- Frontend running: `make dev-frontend` (http://localhost:5173)
- Database seeded: `make db-seed`

### Test Cases

| #   | Test          | Steps                                        | Expected                             | Status |
| --- | ------------- | -------------------------------------------- | ------------------------------------ | ------ |
| 1.1 | Demo Login    | Enter `demo@bijmantra.org` / `demo123`   | Login success, redirect to Gateway   | ⬜     |
| 1.2 | Admin Login   | Enter `admin@bijmantra.org` / `admin123` | Login success,`is_demo: false`     | ⬜     |
| 1.3 | Invalid Login | Enter wrong credentials                      | Error: "Incorrect email or password" | ⬜     |
| 1.4 | Token Refresh | Wait 24h or manually expire token            | Auto-refresh without logout          | ⬜     |
| 1.5 | Logout        | Click logout in user menu                    | Redirect to login, token cleared     | ⬜     |

### API Endpoints to Verify

```bash
# Login
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=demo@bijmantra.org&password=demo123"

# Should return: access_token, user object with is_demo flag
```

---

## 🚪 2. Navigation Testing

### Test Cases

| #   | Test                | Steps                       | Expected                       | Status |
| --- | ------------------- | --------------------------- | ------------------------------ | ------ |
| 2.1 | Gateway Display     | Login → Should see Gateway | 5 workspace cards displayed    | ⬜     |
| 2.2 | Workspace Selection | Click "Plant Breeding"      | Navigate to breeding dashboard | ⬜     |
| 2.3 | Workspace Switching | Use header dropdown         | Switch between workspaces      | ⬜     |
| 2.4 | Sidebar Filtering   | Select workspace            | Only relevant modules shown    | ⬜     |
| 2.5 | Mobile Navigation   | Resize to mobile            | Bottom nav appears             | ⬜     |
| 2.6 | Breadcrumbs         | Navigate deep               | Breadcrumbs show path          | ⬜     |

### Workspaces to Test

- [ ] Plant Breeding (83 pages)
- [ ] Seed Business (22 pages)
- [ ] Innovation Lab (28 pages)
- [ ] Gene Bank (34 pages)
- [ ] Administration (25 pages)

---

## 🌾 3. BrAPI Core Testing

### Test Cases

| #   | Test           | Endpoint                    | Expected                | Status |
| --- | -------------- | --------------------------- | ----------------------- | ------ |
| 3.1 | Programs List  | `GET /brapi/v2/programs`  | Returns programs array  | ⬜     |
| 3.2 | Trials List    | `GET /brapi/v2/trials`    | Returns trials array    | ⬜     |
| 3.3 | Studies List   | `GET /brapi/v2/studies`   | Returns studies array   | ⬜     |
| 3.4 | Locations List | `GET /brapi/v2/locations` | Returns locations array | ⬜     |
| 3.5 | Seasons List   | `GET /brapi/v2/seasons`   | Returns seasons array   | ⬜     |
| 3.6 | People List    | `GET /brapi/v2/people`    | Returns people array    | ⬜     |
| 3.7 | Lists List     | `GET /brapi/v2/lists`     | Returns lists array     | ⬜     |

### API Test Script

```bash
TOKEN="<your_token_here>"

# Test all BrAPI Core endpoints
for endpoint in programs trials studies locations seasons people lists; do
  echo "Testing $endpoint..."
  curl -s "http://localhost:8000/brapi/v2/$endpoint" \
    -H "Authorization: Bearer $TOKEN" | head -c 100
  echo ""
done
```

---

## 🧬 4. Germplasm Testing

### Test Cases

| #   | Test             | Route/Endpoint         | Expected                     | Status |
| --- | ---------------- | ---------------------- | ---------------------------- | ------ |
| 4.1 | Germplasm List   | `/germplasm`         | Table with germplasm entries | ⬜     |
| 4.2 | Germplasm Detail | `/germplasm/:id`     | Detail view with attributes  | ⬜     |
| 4.3 | Pedigree View    | `/pedigree-analysis` | Pedigree tree visualization  | ⬜     |
| 4.4 | Crosses List     | `/crosses`           | Crossing records             | ⬜     |
| 4.5 | Seed Lots        | `/seedlots`          | Seed inventory               | ⬜     |

### BrAPI Endpoints

- `GET /brapi/v2/germplasm`
- `GET /brapi/v2/germplasm/{germplasmDbId}`
- `GET /brapi/v2/pedigree`
- `GET /brapi/v2/crosses`
- `GET /brapi/v2/seedlots`

---

## 📋 5. Phenotyping Testing

### Test Cases

| #   | Test              | Route/Endpoint         | Expected              | Status |
| --- | ----------------- | ---------------------- | --------------------- | ------ |
| 5.1 | Traits List       | `/traits`            | Trait definitions     | ⬜     |
| 5.2 | Variables List    | `/variables`         | Observation variables | ⬜     |
| 5.3 | Observations      | `/observations`      | Observation records   | ⬜     |
| 5.4 | Observation Units | `/observation-units` | Plot/plant units      | ⬜     |
| 5.5 | Images            | `/images`            | Image gallery         | ⬜     |

### BrAPI Endpoints

- `GET /brapi/v2/traits`
- `GET /brapi/v2/variables`
- `GET /brapi/v2/observations`
- `GET /brapi/v2/observationunits`
- `GET /brapi/v2/images`

---

## 🔬 6. Genotyping Testing

### Test Cases

| #   | Test             | Route/Endpoint        | Expected              | Status |
| --- | ---------------- | --------------------- | --------------------- | ------ |
| 6.1 | Variants         | `/variants`         | Variant list          | ⬜     |
| 6.2 | Call Sets        | `/callsets`         | Genotype call sets    | ⬜     |
| 6.3 | References       | `/references`       | Reference genomes     | ⬜     |
| 6.4 | Marker Positions | `/marker-positions` | Genetic map positions | ⬜     |
| 6.5 | Vendor Orders    | `/vendor-orders`    | Genotyping orders     | ⬜     |

### BrAPI Endpoints

- `GET /brapi/v2/variants`
- `GET /brapi/v2/callsets`
- `GET /brapi/v2/references`
- `GET /brapi/v2/markerpositions`
- `GET /brapi/v2/vendor/orders`

---

## 🏛️ 7. Seed Bank Testing

### Test Cases

| #   | Test              | Route                     | Expected                     | Status |
| --- | ----------------- | ------------------------- | ---------------------------- | ------ |
| 7.1 | Dashboard         | `/seed-bank`            | Stats, alerts, quick actions | ⬜     |
| 7.2 | Vaults            | `/seed-bank/vaults`     | Vault list with conditions   | ⬜     |
| 7.3 | Accessions        | `/seed-bank/accessions` | Accession table              | ⬜     |
| 7.4 | Viability Testing | `/seed-bank/viability`  | Test workflow                | ⬜     |
| 7.5 | MTA Management    | `/seed-bank/mta`        | Transfer agreements          | ⬜     |

---

## 🌍 8. Environment Testing

### Test Cases

| #   | Test          | Route                | Expected          | Status |
| --- | ------------- | -------------------- | ----------------- | ------ |
| 8.1 | Weather       | `/weather`         | Forecast display  | ⬜     |
| 8.2 | Soil Analysis | `/soil`            | Soil profiles     | ⬜     |
| 8.3 | Crop Calendar | `/crop-calendar`   | Planting schedule | ⬜     |
| 8.4 | Sensors       | `/sensor-networks` | Device list       | ⬜     |

---

## 🤖 9. AI Features Testing

### Prerequisites

- Ollama running locally (recommended)
- Or: Configure external LLM provider in `.env`

### Test Cases

| #   | Test         | Steps                           | Expected                | Status |
| --- | ------------ | ------------------------------- | ----------------------- | ------ |
| 9.1 | Veena Chat   | Click Veena FAB → Send message | AI response             | ⬜     |
| 9.2 | DevGuru      | Navigate to `/devguru`        | PhD mentor interface    | ⬜     |
| 9.3 | Voice Input  | Click mic icon (if enabled)     | Speech-to-text          | ⬜     |
| 9.4 | Setup Banner | No Ollama running               | "Setup Required" banner | ⬜     |

### Without LLM Provider

If no LLM is configured, Veena should show a "Setup Required" banner instead of crashing.

---

## 📱 10. Offline/PWA Testing

### Test Cases

| #    | Test              | Steps                             | Expected                   | Status |
| ---- | ----------------- | --------------------------------- | -------------------------- | ------ |
| 10.1 | Install Prompt    | Visit site in Chrome              | "Install" option available | ⬜     |
| 10.2 | Offline Indicator | Disconnect network                | Offline banner appears     | ⬜     |
| 10.3 | Cached Pages      | Go offline → Navigate            | Cached pages load          | ⬜     |
| 10.4 | Sync Queue        | Make changes offline → Reconnect | Changes sync               | ⬜     |

---

## 🐛 Bug Report Template

When you find a bug, create an issue with this template:

```markdown
## Bug Report

**Version:** 1.0.0-beta.1
**Test Case:** [e.g., 3.1 Programs List]
**Browser:** [e.g., Chrome 120]
**OS:** [e.g., macOS 14.2]

### Steps to Reproduce
1. 
2. 
3. 

### Expected Behavior


### Actual Behavior


### Screenshots/Logs

```

---

## ✅ Sign-Off Checklist

Before promoting to `1.0.0-rc.1`:

- [ ] All 🔴 Critical tests pass
- [ ] All 🟡 High priority tests pass
- [ ] No blocking bugs open
- [ ] Build passes: `npm run build`
- [ ] Backend starts without errors
- [ ] Database migrations run cleanly

### Tester Sign-Off

| Tester | Date | Categories Tested | Issues Found |
| ------ | ---- | ----------------- | ------------ |
|        |      |                   |              |

---

## 📊 Test Results Summary

### Code Verification Results (Automated)

**Date:** December 30, 2025

| Category       | Code Verified | Endpoints       | Status |
| -------------- | ------------- | --------------- | ------ |
| Authentication | ✅            | 3               | PASS   |
| Navigation     | ✅            | 4 components    | PASS   |
| BrAPI Core     | ✅            | 20+             | PASS   |
| Germplasm      | ✅            | 19              | PASS   |
| Phenotyping    | ✅            | 28              | PASS   |
| Genotyping     | ✅            | 18              | PASS   |
| Seed Bank      | ✅            | 22              | PASS   |
| Environment    | ✅            | 38              | PASS   |
| AI Features    | ✅            | 47              | PASS   |
| Offline/PWA    | ✅            | 12 + PWA config | PASS   |

### Manual Testing Results

| Category        | Total        | Passed | Failed | Blocked |
| --------------- | ------------ | ------ | ------ | ------- |
| Authentication  | 5            | ⬜     | ⬜     | ⬜      |
| Navigation      | 6            | ⬜     | ⬜     | ⬜      |
| BrAPI Core      | 7            | ⬜     | ⬜     | ⬜      |
| Germplasm       | 5            | ⬜     | ⬜     | ⬜      |
| Phenotyping     | 5            | ⬜     | ⬜     | ⬜      |
| Genotyping      | 5            | ⬜     | ⬜     | ⬜      |
| Seed Bank       | 5            | ⬜     | ⬜     | ⬜      |
| Environment     | 4            | ⬜     | ⬜     | ⬜      |
| AI Features     | 4            | ⬜     | ⬜     | ⬜      |
| Offline/PWA     | 4            | ⬜     | ⬜     | ⬜      |
| **Total** | **50** | ⬜     | ⬜     | ⬜      |

---

## 🔗 Related Documents

- [RELEASE_v1.0.0.md](../RELEASE_v1.0.0.md) — Release notes
- [QUICK_START.md](../QUICK_START.md) — Setup guide
- [README.md](../README.md) — Project overview

---

*योगः कर्मसु कौशलम्* — Excellence in Action
