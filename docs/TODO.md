# Bijmantra - Priority TODO

> Last updated: 2025-12-05 (Phase 6 Complete)

## 🔴 Immediate (This Week)

- [x] Commit all new documentation to git ✅
  - `docs/framework/PARASHAKTI_SPECIFICATION.md`
  - `docs/confidential/idea-organised.md`
  - Updated `.kiro/steering/bijmantra-development.md`

- [ ] Review and test existing Plant Sciences functionality
  - Current modules need testing before restructuring

---

## 🟠 Phase 1: Framework Foundation (Week 1-2)

- [x] Create `frontend/src/framework/` folder structure ✅
  - [x] `registry/` — Division registry types and definitions ✅
  - [x] `shell/` — App shell components (DivisionNavigation) ✅
  - [x] `auth/` — Authentication provider (useAuth, ProtectedRoute) ✅
  - [x] `features/` — Feature flag system ✅

- [x] Create `backend/app/core/` structure ✅
  - [x] `events.py` — Event bus for inter-division communication ✅
  - [x] `features.py` — Feature flag service ✅

- [x] Implement Division Registry ✅
  - [x] Define Division interface ✅
  - [x] Register all 9 divisions ✅
  - [x] Integrate navigation with SmartNavigation ✅

---

## 🟡 Phase 2: Restructure Plant Sciences (Week 3-4)

- [x] Create `frontend/src/divisions/plant-sciences/` ✅
  - [x] Define routes.tsx with 80+ routes organized by subsection ✅
  - [x] Add Suspense loading fallback ✅
  - [ ] Gradually migrate pages (existing routes still work)

- [x] Create routing utilities ✅
  - [x] `createDivisionRoutes` helper ✅
  - [x] `createProtectedRoute` helper ✅
  - [x] `createLazyRoute` helper ✅

- [x] Create `backend/app/modules/plant_sciences/` ✅
  - [x] breeding/ — dashboard, pipeline, genetic gain ✅
  - [x] genomics/ — diversity, GRM, GEBV, LD ✅
  - [x] phenotyping/ — dashboard, data quality ✅
  - [x] genotyping/ — dashboard, marker summary ✅

- [ ] Implement lazy loading for division routes (gradual migration)

---

## 🟢 Phase 3: Core Services (Week 5-6) ✅ COMPLETE

- [x] Implement Event Bus (backend) ✅
- [x] Implement Permission middleware (RBAC) ✅
- [x] Create Integration Adapter base class ✅
- [x] Add first integration adapter (BrAPI) ✅
- [x] Add Integration Hub API routes ✅

---

## 🔵 Phase 4: Offline Sync (Week 7-8) ✅ COMPLETE

- [x] Set up Dexie.js with proper schema ✅
- [x] Implement sync engine ✅
- [x] Add pending operations queue ✅
- [x] Create sync hooks (useSync, useOfflineData, useSyncStatus) ✅
- [x] Update service worker caching strategies ✅

---

## ⚪ Phase 5: Seed Bank Division (Week 9+) ✅ COMPLETE

- [x] Create Seed Bank division (Division 2) ✅
  - [x] Frontend structure with 8 pages ✅
    - Dashboard, Accessions, AccessionDetail, VaultManagement
    - Conservation, GermplasmExchange, ViabilityTesting, RegenerationPlanning
  - [x] Backend module (models, schemas, router) ✅
  - [x] Full REST API with CRUD operations ✅
  - [x] IndexedDB schema for offline support ✅
  - [x] Enhanced service worker caching ✅

---

## 🟣 Phase 6: Polish & Integration ✅ COMPLETE

- [x] Connect Seed Bank frontend to backend API ✅
- [x] Add database migrations for Seed Bank tables ✅
- [x] Implement real data fetching with demo fallback ✅
- [x] Add form components (AccessionForm, VaultForm) ✅
- [x] Add offline sync hooks (useOfflineVaults, useOfflineAccessions) ✅
- [x] Update README to reflect Parashakti framework ✅

---

## 📋 Ongoing

- [ ] Testing — All modules need thorough testing
- [ ] Documentation — Keep specs updated as we build
- [ ] README — Update to reflect Parashakti framework (remove BrAPI focus)

---

## 🚫 NOT Now (Defer)

- Microservices split — Not needed until scale demands
- Full ERP — Integrate with ERPNext instead
- Agrochemical database — Just log inputs, link to external DBs
- Sun-Earth Systems — Visionary, foundation only
- Space Research — Visionary, foundation only

---

## 📚 Reference Documents

- `docs/framework/PARASHAKTI_SPECIFICATION.md` — Full technical spec
- `docs/confidential/idea-organised.md` — Vision and division structure
- `.kiro/steering/bijmantra-development.md` — Development guidelines
