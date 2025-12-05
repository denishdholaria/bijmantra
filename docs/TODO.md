# Bijmantra - Priority TODO

> Last updated: 2025-12-05

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
  - [ ] `auth/` — Authentication provider
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

- [ ] Create `frontend/src/divisions/plant-sciences/`
  - [ ] Move existing pages into division structure
  - [ ] Organize by subsection (breeding, genomics, molecular, etc.)
  - [ ] Update imports and routes

- [ ] Create `backend/app/modules/plant_sciences/`
  - [ ] Reorganize existing API routes
  - [ ] Group by subsection

- [ ] Implement lazy loading for division routes

---

## 🟢 Phase 3: Core Services (Week 5-6)

- [ ] Implement Event Bus (backend)
- [ ] Implement Permission middleware
- [ ] Create Integration Adapter base class
- [ ] Add first integration adapter (BrAPI export)

---

## 🔵 Phase 4: Offline Sync (Week 7-8)

- [ ] Set up Dexie.js with proper schema
- [ ] Implement sync engine
- [ ] Add pending operations queue
- [ ] Update service worker caching strategies

---

## ⚪ Phase 5: New Division (Week 9+)

- [ ] Create Seed Bank division (Division 2)
  - [ ] Frontend structure
  - [ ] Backend module
  - [ ] Basic pages (Vault, Accessions, Conservation)
  - [ ] Register in Division Registry
  - [ ] Test feature flag toggling

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
