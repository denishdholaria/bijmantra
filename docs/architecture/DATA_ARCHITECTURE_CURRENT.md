# BijMantra Data Architecture — Current State

> **Status**: AUTHORITATIVE — Code-Referenced Documentation  
> **Last Verified**: January 2026  
> **Governance**: Per GOVERNANCE.md §4.2

---

## Purpose

This document describes the **actual, implemented** data architecture of BijMantra as verified through direct code inspection. It serves as the authoritative reference for the current system state.

For the target analytical architecture, see: `DATA_LAKE_TARGET_ARCHITECTURE.md`

---

## Architecture Classification

| Aspect | Current Implementation |
|--------|------------------------|
| **Primary Pattern** | OLTP (Online Transaction Processing) |
| **Storage Engine** | PostgreSQL 15+ with PostGIS, pgvector |
| **ORM** | SQLAlchemy 2.0+ (async) |
| **API Layer** | FastAPI with Pydantic v2 |
| **Caching** | Redis |
| **Object Storage** | MinIO (images only) |
| **Search** | Meilisearch |

---

## Data Storage Layer

### PostgreSQL — Primary Data Store

All operational data resides in PostgreSQL:

```
┌─────────────────────────────────────────────────┐
│                  PostgreSQL                      │
├─────────────────────────────────────────────────┤
│  137 tables (as of Session 81)                  │
│  103 tables with Row-Level Security             │
│  29 Alembic migrations                          │
│  Multi-tenant isolation via organization_id     │
└─────────────────────────────────────────────────┘
```

**Key characteristics:**
- Row-oriented storage (OLTP-optimized)
- ACID transactions
- Real-time CRUD operations
- BrAPI v2.1 compliant schema

### MinIO — Object Storage

Currently used for:
- Plant images
- Document attachments
- Report artifacts

**Not currently used for:**
- Parquet files
- Analytical datasets
- AI training data

### Redis — Caching Layer

- Session management
- Rate limiting
- Query result caching
- Real-time notifications

---

## Data Flow Architecture

### Current Flow (Implemented)

```
External Data (CSV/TSV/JSON)
         ↓
    FastAPI Endpoint
         ↓
    Pydantic Validation
         ↓
    SQLAlchemy ORM
         ↓
    PostgreSQL Tables
         ↓
    BrAPI JSON Response
```

### Export Flow (Implemented)

```
PostgreSQL Query
       ↓
SQLAlchemy Result
       ↓
DataExportService
       ↓
CSV / TSV / JSON
```

**Evidence**: `backend/app/services/data_export.py`
- Supports: CSV, TSV, JSON
- Does NOT support: Parquet, Arrow, Feather

---

## Schema Governance (Current)

### Implemented

| Mechanism | Implementation |
|-----------|----------------|
| Schema versioning | Alembic migrations |
| Type enforcement | Pydantic v2 models |
| Nullability | SQLAlchemy column definitions |
| Foreign keys | PostgreSQL constraints |
| Multi-tenancy | `organization_id` on all tables |
| Row-Level Security | PostgreSQL RLS policies |

### Not Yet Implemented

| Mechanism | Status |
|-----------|--------|
| Schema registry service | Not implemented |
| Data dictionaries | Partial (in code comments) |
| Lineage tracking | Not implemented |
| Unit metadata | Partial (in trait definitions) |

---

## BrAPI Integration (Current)

BrAPI v2.1 is fully implemented as the **API layer**:

```
PostgreSQL → SQLAlchemy → Pydantic → BrAPI JSON
```

**Key points:**
- BrAPI is the external interface
- PostgreSQL is the storage layer
- No intermediate Parquet layer exists

**Endpoints**: 201 BrAPI endpoints implemented  
**Compliance**: 100% BrAPI v2.1 core specification

---

## Analytics Capabilities (Current)

### Backend Analytics

- SQL-based aggregations via SQLAlchemy
- Statistical calculations in Python services
- Rust/WASM for compute-intensive operations (BLUP, GRM)

### Frontend Analytics

- `frontend/src/lib/duckdb-analytics.ts` — **Stub implementation**
- DuckDB-WASM initialized but not fully integrated
- Parquet loading: `throw new Error('Parquet export not yet implemented')`

---

## Data Export Formats (Current)

| Format | Status | Use Case |
|--------|--------|----------|
| CSV | ✅ Implemented | Human-readable export |
| TSV | ✅ Implemented | Spreadsheet compatibility |
| JSON | ✅ Implemented | API responses, BrAPI |
| Parquet | ❌ Not implemented | — |
| Arrow | ❌ Not implemented | — |
| Feather | ❌ Not implemented | — |

---

## Multi-Tenant Data Isolation

All tables include `organization_id` with:
- Foreign key to `organizations` table
- Index for query performance
- Row-Level Security policy

**RLS-enabled tables**: 103 of 137 (remaining are reference/system tables)

---

## What This Architecture Supports Well

✅ Real-time CRUD operations  
✅ BrAPI interoperability  
✅ Multi-tenant isolation  
✅ Transactional integrity  
✅ Complex relational queries  
✅ Full-text search (Meilisearch)  

---

## What This Architecture Does Not Support (Yet)

❌ Columnar analytics at scale  
❌ AI feature pipelines  
❌ Bulk data lake operations  
❌ Arrow-based data interchange  
❌ Parquet-native storage  

---

## Relationship to Target Architecture

This OLTP architecture will **coexist with** (not be replaced by) the analytical data lake described in `DATA_LAKE_TARGET_ARCHITECTURE.md`.

The hybrid model:

```
┌─────────────────────────────────────────────────────────┐
│                   BijMantra Hybrid                       │
├────────────────────────┬────────────────────────────────┤
│   Operational Plane    │      Analytical Plane          │
│   (Current - Active)   │      (Target - Planned)        │
├────────────────────────┼────────────────────────────────┤
│   PostgreSQL           │      Parquet in MinIO          │
│   SQLAlchemy           │      PyArrow / Polars          │
│   FastAPI              │      DuckDB                    │
│   Real-time CRUD       │      Batch analytics           │
│   BrAPI endpoints      │      AI pipelines              │
└────────────────────────┴────────────────────────────────┘
```

---

## Verification

This document was verified against:
- `backend/app/services/data_export.py` — Export formats
- `backend/app/models/` — SQLAlchemy models
- `backend/alembic/versions/` — 29 migrations
- `frontend/src/lib/duckdb-analytics.ts` — Analytics stub
- `compose.yaml` — Infrastructure services
- `metrics.json` — Current counts

---

*This document describes what IS, not what SHOULD BE.*
