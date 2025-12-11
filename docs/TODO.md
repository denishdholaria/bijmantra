# Bijmantra - Priority TODO

> **Single Source of Truth** for what needs to be built  
> Last updated: December 11, 2025

---

## ✅ COMPLETED: LIMS & Seed Company Module

> **Source**: ProQRT learnings — See `docs/confidential/IDEAS.md` for full plan

### Phase 1: Lab Sample Management ✅
- [x] `frontend/src/divisions/seed-operations/pages/LabSamples.tsx`
- [x] Sample registration form with dialog
- [x] Sample list with status filters
- [x] Connected to `/api/v2/quality/` API

### Phase 2: Lab Testing Workflow ✅
- [x] `frontend/src/divisions/seed-operations/pages/LabTesting.tsx`
- [x] Test entry forms (germination, purity, moisture, vigor)
- [x] Results recording with pass/fail thresholds
- [x] `frontend/src/divisions/seed-operations/pages/Certificates.tsx`

### Phase 3: Quality Gate Scanner ✅
- [x] `frontend/src/divisions/seed-operations/pages/QualityGate.tsx`
- [x] QR/barcode scanning (hardware scanner support)
- [x] Real-time status display (green/red/orange)
- [x] Decision recording (approve/reject)

### Phase 4: Dispatch Management ✅
- [x] Backend: `/api/v2/dispatch/` endpoints (18 endpoints)
- [x] `frontend/src/divisions/seed-operations/pages/CreateDispatch.tsx`
- [x] `frontend/src/divisions/seed-operations/pages/DispatchHistory.tsx`
- [x] `frontend/src/divisions/seed-operations/pages/Firms.tsx` - Dealer management

### Phase 5: Processing Batches ✅
- [x] Backend: `/api/v2/processing/` endpoints (12 endpoints)
- [x] `frontend/src/divisions/seed-operations/pages/ProcessingBatches.tsx`
- [x] Stage workflow management

---

## ✅ COMPLETED: Frontend UI for New APIs (Dec 10, 2025)

### New API Modules (469 total endpoints)

| Module | API Endpoints | UI Status | Priority |
|--------|---------------|-----------|----------|
| Seed Traceability | `/api/v2/traceability/` (16) | ✅ Connected | DONE |
| Dispatch Management | `/api/v2/dispatch/` (18) | ✅ Connected | DONE |
| Seed Processing | `/api/v2/processing/` (12) | ✅ Connected | DONE |
| Variety Licensing | `/api/v2/licensing/` (17) | ✅ Complete | DONE |
| DUS Testing | `/api/v2/dus/` (17) | ✅ Complete | DONE |
| MCPD Exchange | `/api/v2/seed-bank/mcpd/` (8) | ✅ Complete | DONE |
| Disease Resistance | `/api/v2/disease/` (15) | ✅ Complete | DONE |
| Abiotic Stress | `/api/v2/abiotic/` (11) | ✅ Complete | DONE |
| Spatial Analysis | `/api/v2/spatial/` (11) | ✅ Complete | DONE |
| Pedigree Analysis | `/api/v2/pedigree/` (8) | ✅ Complete | DONE |
| Phenotype Analysis | `/api/v2/phenotype/` (7) | ✅ Complete | DONE |
| Bioinformatics | `/api/v2/bioinformatics/` (7) | ✅ Complete | DONE |
| Crop Calendar | `/api/v2/crop-calendar/` (10) | ✅ Complete | DONE |
| Selection Index | `/api/v2/selection/` (9) | ✅ Complete | DONE |
| Genetic Gain | `/api/v2/genetic-gain/` (9) | ✅ Complete | DONE |
| Harvest Management | `/api/v2/harvest/` (16) | ✅ Complete | DONE |
| Breeding Value | `/api/v2/breeding-value/` (8) | ✅ Complete | DONE |

---

## 🟡 MEDIUM PRIORITY: Computer Vision & WASM

### Plant Vision Models (1-2 weeks)
- [ ] **Disease Detection** — TensorFlow.js model
- [ ] **Growth Stage Classifier** — BBCH scale
- [ ] **Model Serving** — `/api/v2/vision/analyze`

### WASM Compilation (1 week)
- [ ] **Compile Rust to WASM** — GRM, LD, PCA

---

## ✅ COMPLETED (Dec 11, 2025)

### Frontend UI - Backend API Pages (4 pages)
- [x] **Selection Index Calculator** — Smith-Hazel, Desired Gains, Base Index, Independent Culling, Response Prediction
- [x] **Genetic Gain Tracker** — Program tracking, cycle recording, gain calculation, variety releases
- [x] **Harvest Management** — Harvest plans, records, quality grading, storage management
- [x] **Breeding Value Calculator** — BLUP, GBLUP, cross prediction, selection candidates

## ✅ COMPLETED (Dec 10, 2025)

### Frontend UI - Plant Sciences Analysis Tools (8 pages)
- [x] **Disease Resistance** — Disease database, R-gene catalog, gene pyramiding
- [x] **Abiotic Stress** — 8 stress types, tolerance genes, index calculator
- [x] **Bioinformatics** — Sequence analysis, primer design, restriction sites
- [x] **Crop Calendar** — Crop profiles, planting events, GDD tracking
- [x] **Spatial Analysis** — Field registry, plot grid, distance calculator
- [x] **Pedigree Analysis** — Load pedigree, coancestry, ancestry tracing
- [x] **Phenotype Analysis** — Statistics, heritability, selection response

### Frontend UI - Commercial Division
- [x] **DUS Testing** — 3 pages (Trials, Crops, Trial Detail)
- [x] **MCPD Exchange** — Export/import with validation
- [x] **Variety Licensing** — Protection, agreements, royalties
- [x] **Processing Stages** — 10-stage workflow visualization

### All Divisions Now Active
- [x] **Sun-Earth Systems** — Solar activity, photoperiod, UV index
- [x] **Space Research** — Space crops, radiation, life support
- [x] **Sensor Networks** — Devices, live data, alerts
- [x] **Knowledge** — Training hub, community forums

### Backend APIs - Commercial Division (Dec 6)
- [x] **Seed Traceability** — Chain of custody, QR codes, certifications
- [x] **Variety Licensing** — PVP/PBR, license agreements, royalties
- [x] **DUS Testing** — UPOV variety protection, 10 crop templates
- [x] **MCPD Exchange** — Genebank data exchange standard

### Backend APIs - Advanced Analytics
- [x] **Selection Index** — Smith-Hazel, Desired Gains, Independent Culling, Tandem
- [x] **Genetic Gain** — Progress tracking, projections, realized heritability
- [x] **Breeding Value** — BLUP, GBLUP, cross prediction, candidate ranking
- [x] **Spatial Analysis** — GIS, Moran's I, nearest neighbor, field mapping

### Backend APIs - Stress Tolerance
- [x] **Disease Resistance** — 8 diseases, 9 genes, gene pyramiding, screening
- [x] **Abiotic Stress** — 8 stress types, 7 indices (SSI, STI, YSI, GMP, etc.)

### Backend APIs - Operations
- [x] **Harvest Management** — Planning, storage, dry weight calculation

### Previously Completed
- [x] **Veena RAG** — `/api/v2/chat`
- [x] **Veena Voice** — `/api/v2/voice` (VibeVoice + Edge TTS)
- [x] **GWAS Pipeline** — GLM, MLM, kinship, PCA
- [x] **G×E Analysis** — AMMI, GGE, Finlay-Wilkinson
- [x] **Bioinformatics** — Sequence analysis, primer design
- [x] **Pedigree Analysis** — A-matrix, inbreeding, coancestry
- [x] **Phenotype Analysis** — Heritability, genetic correlation
- [x] **MAS** — Marker registration, MABC workflow
- [x] **Trial Design** — RCBD, Alpha-Lattice, Augmented, Split-Plot
- [x] **Nursery Management** — OYT/PYT/AYT/Elite stages
- [x] **MCP Server** — ChatGPT/Claude integration
- [x] **Integration Hub** — API management, event bus
- [x] **271+ pages** — Frontend UI
- [x] **BrAPI v2.1** — 34/34 endpoints (100%)

---

## 📊 Current Metrics

| Metric | Value |
|--------|-------|
| Total API Endpoints | 469 |
| Frontend Pages | 275+ |
| BrAPI Compliance | 100% |
| TypeScript Errors | 0 |
| Tests Passing | 48 |
| Build Size | 5.0MB |
| PWA Entries | 96 |

---

## 🚫 NOT Building (Integrate Instead)

| Don't Build | Integrate With |
|-------------|----------------|
| Full ERP | ERPNext |
| Agrochemical DB | External registries |
| Bioinformatics tools | NCBI, EMBL, Ensembl |
| Weather service | OpenWeather API |

---

## 📚 Documentation Map

| File | Purpose |
|------|---------|
| `README.md` | Project overview |
| `PROJECT_STATUS.md` | Current status |
| `docs/ARCHITECTURE.md` | Technical reference |
| `docs/Godsend.md` | Feature tracking |
| `docs/TODO.md` | This file |
| `docs/confidential/IDEAS.md` | **All ideas consolidated** |
| `.kiro/steering/STATE.md` | AI agent state |
