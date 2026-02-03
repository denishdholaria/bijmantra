# BijMantra Data Lake — Target Architecture

> **Status**: TARGET ARCHITECTURE — Not Yet Implemented  
> **Classification**: Roadmap / Vision Document  
> **Current State**: See `DATA_ARCHITECTURE_CURRENT.md`

---

## Document Purpose

This document defines the **intended analytical data architecture** for BijMantra. It describes a target state that will be implemented incrementally alongside the existing PostgreSQL-based operational system.

**This is NOT a description of current implementation.**

For the current, code-verified architecture, see: `DATA_ARCHITECTURE_CURRENT.md`

---

## Architectural Vision

### Core Philosophy

> **Humans read CSV/TSV. Machines work on Parquet. AI thinks in Arrow. APIs speak JSON.**

This principle guides the target state but is **not yet implemented** in the codebase.

### Dual-Plane Architecture

BijMantra is designed to become a **dual-plane system**:

```
┌─────────────────────────────────────────────────────────────────┐
│                    BijMantra Dual-Plane                          │
├─────────────────────────────┬───────────────────────────────────┤
│     Operational Plane       │        Analytical Plane           │
│     (OLTP - Current)        │        (OLAP - Target)            │
├─────────────────────────────┼───────────────────────────────────┤
│  PostgreSQL                 │  Parquet files in MinIO           │
│  SQLAlchemy 2.0             │  PyArrow / Polars                 │
│  FastAPI endpoints          │  DuckDB (backend + WASM)          │
│  Real-time CRUD             │  Batch analytics                  │
│  BrAPI v2.1 interface       │  AI feature pipelines             │
│  Row-oriented storage       │  Column-oriented storage          │
│  Transactional integrity    │  Analytical performance           │
└─────────────────────────────┴───────────────────────────────────┘
```

**Key insight**: These planes **coexist** — the analytical plane augments, not replaces, the operational plane.

---

## Target Data Format Tiers

### Tier 1 — External Interface (Ingress / Egress)

**Purpose**: Human-readable data exchange

**Formats**:
- CSV / TSV — Researcher exports, spreadsheet compatibility
- JSON — API responses, BrAPI payloads

**Rules** (Target State):
- No CSV/TSV used for internal analytics
- No JSON used for bulk data storage
- No schema-less data past ingestion layer

---

### Tier 2 — Canonical Analytical Storage

**Purpose**: Persistent analytical datasets

**Format**: Parquet

**Why Parquet**:
- Columnar (optimized for analytical queries)
- Compressed (efficient storage)
- Schema-enforced (type safety)
- Fast scans (predicate pushdown)
- AI-friendly (native Arrow integration)

**Target Rule**:
> All analytical datasets normalized to Parquet for AI/ML pipelines.

---

### Tier 3 — Compute Layer

**Purpose**: In-memory analytics and AI processing

**Formats**:
- Apache Arrow — Cross-language interchange
- Feather — In-memory only (never persisted)

**Rules**:
- Arrow is the interchange format between Python, Rust, JavaScript
- Feather is ephemeral compute format

---

## Target Storage Layout

```
MinIO Buckets (Target Structure)
├── bijmantra-raw/
│   ├── phenotype/
│   ├── genotype/
│   ├── sensor/
│   ├── climate/
│   └── soil/
│
├── bijmantra-normalized/
│   ├── phenotype/     (Parquet)
│   ├── genotype/      (Parquet)
│   ├── sensor/        (Parquet)
│   ├── climate/       (Parquet)
│   └── soil/          (Parquet)
│
├── bijmantra-curated/
│   ├── analysis_ready/
│   ├── ai_features/
│   └── reports/
│
├── bijmantra-metadata/
│   ├── schemas/
│   ├── dictionaries/
│   └── lineage/
│
└── bijmantra-images/   (Current - Already Implemented)
```

---

## Target Data Flows

### Ingestion Pipeline (Target)

```
External Data (CSV/TSV/JSON)
         ↓
    Validation Service
         ↓
    Schema Mapping
         ↓
    Type Enforcement
         ↓
    Parquet Write (MinIO)
         ↓
    Catalog Registration
         ↓
    Available for Analytics
```

### Hybrid Query Flow (Target)

```
┌─────────────────────────────────────────────────────────┐
│                    Query Router                          │
├─────────────────────────────────────────────────────────┤
│  OLTP Query?          │  OLAP Query?                    │
│  (CRUD, real-time)    │  (Analytics, bulk)              │
│         ↓             │         ↓                       │
│    PostgreSQL         │    DuckDB + Parquet             │
│         ↓             │         ↓                       │
│    JSON Response      │    Arrow → JSON Response        │
└─────────────────────────────────────────────────────────┘
```

### AI Pipeline Contract (Target)

```
PostgreSQL → ETL → Parquet → Arrow → Model → JSON
     ↑                                    ↓
     └────────── Predictions ─────────────┘
```

---

## BrAPI Integration (Target State)

BrAPI remains the **external interface layer**. The analytical plane operates behind it.

### Inbound Flow (Target)

```
BrAPI JSON Payload
         ↓
    Schema Validation
         ↓
    PostgreSQL (operational)
         ↓
    ETL Job (async)
         ↓
    Parquet (analytical)
```

### Outbound Flow (Target)

```
Query Type?
    ├── Simple lookup → PostgreSQL → BrAPI JSON
    └── Analytics → DuckDB/Parquet → BrAPI JSON
```

**Principle**:
> BrAPI defines how data moves. Parquet defines how data lives (analytically).

---

## Schema Governance (Target)

### Required Metadata per Dataset

```yaml
dataset:
  name: trial_observations_2026
  version: v3
  schema_version: 1.2.0
  
fields:
  - name: yield_kg_per_ha
    type: float64
    nullable: false
    unit: kg/ha
    description: Harvested yield per hectare
    domain: phenotype
    
  - name: observation_date
    type: date
    nullable: false
    format: ISO-8601
    
lineage:
  source: postgresql.observations
  transformation: etl_observations_v3
  created: 2026-01-15T00:00:00Z
```

### Versioning Strategy

```
bijmantra-normalized/
  phenotype/
    observations/
      v1/
      v2/
      v3/  ← current
```

- No in-place mutation
- All transformations additive
- Old versions retained for reproducibility

---

## Implementation Roadmap

### Phase 1 — OLTP Stabilization (Current)

**Status**: ✅ Complete

- PostgreSQL as source of truth
- BrAPI v2.1 fully implemented
- CRUD workflows operational
- 137 tables, 1,475 endpoints

### Phase 2 — Analytical Shadow Layer

**Status**: 🔜 Planned

**Deliverables**:
- [ ] PyArrow / Polars integration in backend
- [ ] MinIO bucket structure for Parquet
- [ ] Nightly ETL: PostgreSQL → Parquet
- [ ] DuckDB backend service for analytics
- [ ] DuckDB-WASM frontend completion

**Dependencies**:
- `pyarrow` or `polars` added to backend
- MinIO bucket policies configured
- ETL scheduler (Celery or similar)

### Phase 3 — AI-Native Pipelines

**Status**: 🔜 Planned (Post Phase 2)

**Deliverables**:
- [ ] Arrow-based feature extraction
- [ ] Agent workflow integration (Veena)
- [ ] Real-time + batch fusion queries
- [ ] Cross-domain AI reasoning on Parquet

### Phase 4 — Partial Source Shift (Long-Term)

**Status**: 📋 Conceptual

**Consideration**:
- High-volume domains (sensor, genotype) may shift to Parquet-first
- PostgreSQL retains transactional roles
- Requires careful evaluation of trade-offs

---

## What Is Explicitly Forbidden (Target State)

Once the analytical plane is implemented:

- ❌ CSV/TSV used for internal analytics
- ❌ JSON blobs used for analytical storage
- ❌ Schema-less datasets in normalized tier
- ❌ Mixing compute formats with storage formats
- ❌ Ad-hoc file naming in data lake

---

## Dependencies for Implementation

| Dependency | Purpose | Status |
|------------|---------|--------|
| PyArrow | Parquet read/write | Not installed |
| Polars | DataFrame operations | Not installed |
| DuckDB | Analytical queries | Stub only |
| Celery/APScheduler | ETL scheduling | Not configured |
| MinIO buckets | Parquet storage | Images only |

---

## Success Criteria

The analytical plane is considered **implemented** when:

1. ✅ Parquet files exist in MinIO for core domains
2. ✅ ETL pipeline runs on schedule
3. ✅ DuckDB queries return results from Parquet
4. ✅ AI pipelines consume Arrow data
5. ✅ Frontend analytics use DuckDB-WASM
6. ✅ BrAPI responses can source from either plane

---

## Governance Alignment

This document:
- Is classified as **TARGET / ROADMAP**
- Does NOT describe current implementation
- Will be updated as phases complete
- Complies with GOVERNANCE.md evidence requirements

**Current state verification**: `DATA_ARCHITECTURE_CURRENT.md`

---

## AI-Era Workflow Principle

> **If data cannot flow in seconds, the workflow is broken.**

This platform is being built for:
- Agent-driven orchestration
- Cross-institution pipelines
- Real-time decision loops

The dual-plane architecture enables this vision while maintaining operational stability.

---

## Engineering Principle

> **Data architecture is system architecture.**

If this layer is wrong, AI will be wrong, analytics will be wrong, and decisions will be wrong.

This document exists to guide that future correctly.

---

*This document describes what WILL BE, not what IS.*
