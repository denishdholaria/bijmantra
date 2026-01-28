# BijMantra Interoperability Contract

> **Status**: AUTHORITATIVE — Binding Contract  
> **Last Verified**: January 2026  
> **Scope**: External Systems, Standards, Agents, Integrations  
> **Governance**: Per GOVERNANCE.md §4.2 (Evidence-Based, Code-Referenced)  
> **Applies To**: All contributors, services, agents, and integrations

---

## Implementation Status Summary

| Standard | Status | Evidence |
|----------|--------|----------|
| BrAPI v2.1 | ✅ Implemented (201 endpoints) | `backend/app/api/brapi/` |
| MCPD v2.1 | ✅ Implemented | `backend/app/modules/seed_bank/mcpd.py` |
| MIAPPE | 🔜 Planned | — |
| ISA-Tab | 🔜 Planned | — |

---

## 1. Purpose

This document defines the **binding interoperability contract** for BijMantra.

It specifies:
- Which standards are supported
- What "compatibility" means in measurable terms
- How data is allowed to move in and out of the system
- How AI agents may orchestrate external workflows
- How extensions are introduced without breaking standards

This contract exists to ensure:
- **Ecosystem compatibility**
- **Vendor neutrality**
- **AI-era workflow readiness**
- **Long-term institutional trust**

---

## 2. Non-Negotiable Principles

### 2.1 Interoperability First

> **If a dataset cannot leave BijMantra cleanly, the architecture is defective.**

All core datasets must be exportable through open standards.

---

### 2.2 Standards Over Convenience

> **We adopt standards even when they are inconvenient.**

Short-term developer convenience is never allowed to override long-term interoperability.

---

### 2.3 Separation of Concerns

> **Standards define how data moves. Internal architecture defines how data lives.**

No external standard is treated as an internal storage model.

---

## 3. Supported Standards (Authoritative List)

### 3.1 BrAPI v2.1 — Primary Interface Standard

**Status**: Mandatory

BrAPI v2.1 is the **primary external contract** for breeding data.

**Coverage**:
- Trials, Studies, Programs, Locations
- Germplasm, Seed Lots, Pedigree, Crosses
- Observations, Traits, Scales, Methods
- Genotyping: Variants, Calls, Maps, Plates

**Rules**:
- 100% compliance with core BrAPI v2.1 specification
- No breaking deviations
- Optional fields may be extended only via `additionalInfo`

---

### 3.2 MIAPPE — Phenotyping Metadata Standard

**Status**: 🔜 Planned (Not Yet Implemented)

MIAPPE fields will be:
- Mapped internally
- Preserved on import
- Exportable without loss

*Note: BrAPI endpoints include MIAPPE field references in ontology structures (e.g., `taxonomyOntologyReference`), but dedicated MIAPPE import/export services are not yet implemented.*

---

### 3.3 MCPD — Germplasm Passport Data

**Status**: ✅ Implemented

**Evidence**: `backend/app/modules/seed_bank/mcpd.py`, `backend/app/modules/seed_bank/router.py`

MCPD v2.1 is fully supported:
- Import from CSV (`POST /api/v2/seed-bank/mcpd/import`)
- Export to CSV/JSON (`GET /api/v2/seed-bank/mcpd/export/csv`, `/json`)
- Template download (`GET /api/v2/seed-bank/mcpd/template`)
- Validation with FAO/Bioversity code mappings
- Reference data endpoints for SAMPSTAT, COLLSRC, STORAGE, country codes

---

### 3.4 ISA-Tab — Experiment Structure

**Status**: 🔜 Planned (Not Yet Implemented)

ISA-Tab structures will be:
- Parsable
- Mappable to internal study + observation model
- Reconstructible on export

*Implementation pending. See `docs/gupt/REFERENCE_APPS_ANALYSIS.md` for integration candidates (e.g., `plant-brapi-to-isa`).*

---

### 3.5 Custom Extensions

**Status**: Allowed under strict rules (see §7)

---

### 3.6 Future Standards (Under Evaluation)

The following standards are being evaluated for future integration:

| Standard | Domain | Rationale |
|----------|--------|-----------|
| **CG Core** | Crop Ontology extensions | Semantic interoperability with CGIAR centers |
| **AgroVOC** | FAO agricultural vocabulary | Multilingual term alignment |
| **GA4GH** | Genomics (VCF, SAM/BAM) | Future high-throughput genotyping interoperability |
| **FAIR Digital Objects** | Research data | Institutional repository integration |

*These are directional — no implementation commitment until formally adopted.*

---

## 4. Interoperability Scope

This contract applies to:

- API endpoints (REST, BrAPI)
- Bulk import/export
- ETL pipelines
- AI agent workflows
- External system integrations
- Institutional data exchange

---

## 5. Inbound Data Contract

### 5.1 Accepted Formats

| Format | Purpose | Status |
|--------|---------|--------|
| JSON | APIs, BrAPI | ✅ Mandatory |
| CSV | Bulk import | ✅ Supported |
| TSV | Bulk import | ✅ Supported |
| MCPD CSV | Germplasm | ✅ Implemented |
| ISA-Tab | Experiments | 🔜 Planned |
| MIAPPE | Phenotyping metadata | 🔜 Planned |

---

### 5.2 Inbound Flow (Authoritative)

```
External System
     ↓
Standards Validation (BrAPI/MCPD)
     ↓
Schema Mapping Layer
     ↓
Pydantic Validation
     ↓
Operational Storage (PostgreSQL)
     ↓
ETL (if analytical)
     ↓
Analytical Storage (Parquet – Target State)
```

---

### 5.3 Hard Rules

- No schema-less data passes validation
- No silent field drops
- No implicit type coercion
- Unknown fields must be captured in `additionalInfo`

---

## 6. Outbound Data Contract

### 6.1 Export Formats

| Format | Use Case | Status |
|--------|----------|--------|
| BrAPI JSON | Ecosystem integration | ✅ Mandatory |
| CSV | Human export | ✅ Supported |
| TSV | Spreadsheet | ✅ Supported |
| MCPD CSV/JSON | Germplasm exchange | ✅ Implemented |
| ISA-Tab | Institutional exchange | 🔜 Planned |
| MIAPPE | Phenotyping metadata | 🔜 Planned |

---

### 6.2 Outbound Flow (Authoritative)

```
Operational Query (PostgreSQL)
        or
Analytical Query (Parquet/DuckDB – Target)
            ↓
Domain Projection
            ↓
Standards Mapping
            ↓
Serialization (JSON/CSV/TSV)
            ↓
External System
```

---

## 7. Extension Policy (Critical Section)

This section governs **how BijMantra innovates without breaking standards**.

### 7.1 Extension Mechanism

All extensions must:
- Use `additionalInfo` (BrAPI)
- Or namespaced fields: `x_bijmantra_*`

---

### 7.2 Rules

- No core standard field may be overloaded
- No standard semantics may be changed
- No extension may break round-trip export

---

### 7.3 Example

```json
{
  "germplasmDbId": "G123",
  "germplasmName": "ICRISAT-45",
  "additionalInfo": {
    "x_bijmantra_predicted_yield": 4.2,
    "x_bijmantra_stress_score": 0.18
  }
}
```

---

## 8. AI Agent Interoperability Rules

AI agents (e.g., Veena) are subject to **the same interoperability constraints** as human developers.

### 8.1 Agents May

- Read via BrAPI endpoints
- Trigger exports
- Orchestrate multi-system workflows
- Map data between standards

---

### 8.2 Agents May NOT

- Bypass standards
- Write proprietary-only structures
- Create hidden fields
- Break schema contracts

---

### 8.3 Agent Workflow Contract

```
Agent Intent
     ↓
Standards Discovery
     ↓
Schema Mapping
     ↓
External Call (BrAPI/ISA/MCPD)
     ↓
Response Validation
     ↓
Internal Projection
```

---

## 9. Versioning Guarantees

### 9.1 Standard Versions

- BrAPI version must be explicit
- MIAPPE version must be documented
- MCPD version must be tracked

---

### 9.2 Backward Compatibility

- No breaking changes without major version bump
- Deprecations must be documented
- Sunset timelines must be published

---

## 10. Compliance Requirements

Every integration must satisfy:

- Standards validation
- Round-trip export test
- Schema conformance test
- Governance review

No integration is considered complete without passing all four.

---

## 11. What Is Explicitly Forbidden

- Proprietary-only export formats
- Silent field drops
- Hard-coded partner mappings
- Closed schemas
- Vendor-specific lock-in

---

## 12. Relationship to Other Architecture Documents

| Document | Role |
|----------|------|
| ARCHITECTURE.md | System overview |
| DATA_ARCHITECTURE_CURRENT.md | Current OLTP reality |
| DATA_LAKE_TARGET_ARCHITECTURE.md | Analytical roadmap |
| GOVERNANCE.md | Review and authority model |

This contract binds them together.

---

## 13. AI-Era Interoperability Principle

> **Interoperability is no longer about files. It is about workflows.**

This system is designed for:
- Agent-to-agent pipelines
- Cross-institution orchestration
- Real-time decision loops

Any design that blocks this is architecturally invalid.

---

## 14. Enforcement

Violations of this contract are:
- Architectural defects
- Governance violations
- Subject to mandatory correction

No exceptions.

---

## 15. Final Statement

> **BijMantra will not become another closed platform.**

Interoperability is not a feature. It is the foundation.

This document exists to make that non-negotiable.

---

End of file.

