# BijMantra Schema Governance

> **Status**: AUTHORITATIVE — Binding Governance Policy
> **Last Verified**: January 2026
> **Governance Basis**: GOVERNANCE.md §4.2 (Evidence-Based, Code-Referenced)
> **Applies To**: All schemas, migrations, agents, services, and integrations

---

## 1. Purpose

This document defines the **binding schema governance model** for BijMantra.

It specifies:
- Who owns schemas
- How schemas may change
- How breaking changes are handled
- How standards mapping is governed
- How AI agents are constrained by schema

This exists to prevent:
- Silent data corruption
- Schema drift
- Agent-induced breakage
- Standards incompatibility
- Long-term maintainability failures

---

## 2. Core Principles (Non-Negotiable)

### 2.1 Schema Is Law

> **If it is not in the schema, it does not exist.**

No field may be stored, transmitted, or inferred without schema definition.

---

### 2.2 Evidence Over Authority

> **No schema change is valid without code evidence.**

Design documents, opinions, or convenience do not override implementation reality.

---

### 2.3 Forward Compatibility First

> **We prefer additive change over modification, and modification over removal.**

Breaking changes are a last resort.

---

## 3. Scope of Governance

This policy governs:

- PostgreSQL schemas (tables, columns, constraints)
- Pydantic models
- BrAPI response models
- MCPD models
- MIAPPE / ISA-Tab mappings (planned)
- Parquet schemas (target state)
- Arrow schemas (target state)
- AI feature schemas
- Agent input/output contracts

---

## 4. Schema Ownership Model

Every schema has **exactly one owner**.

| Domain | Owner | Models | Schemas | Services |
|--------|-------|--------|---------|----------|
| Germplasm | Seed Bank Lead | `backend/app/models/germplasm.py` | `backend/app/schemas/` | `backend/app/modules/seed_bank/` |
| Phenotyping | Phenotype Lead | `backend/app/models/phenotyping.py`, `brapi_phenotyping.py` | `backend/app/schemas/` | `backend/app/services/` |
| Genotyping | Genomics Lead | `backend/app/models/genotyping.py` | `backend/app/schemas/` | `backend/app/services/` |
| Trials/Studies | Trial Lead | `backend/app/models/core.py` (Trial, Study) | `backend/app/schemas/` | `backend/app/services/` |
| AI Features | AI Lead | — | — | `backend/app/services/` |
| Stress Resistance | Breeding Lead | `backend/app/models/stress_resistance.py` | `backend/app/schemas/` | `backend/app/services/` |
| Field Operations | Operations Lead | `backend/app/models/field_operations.py` | `backend/app/schemas/` | `backend/app/services/` |

**Actual Directory Structure** (verified January 2026):
```
backend/app/
├── models/           # SQLAlchemy models (16 files)
│   ├── germplasm.py
│   ├── phenotyping.py
│   ├── genotyping.py
│   ├── core.py       # Trial, Study, Program, Location
│   └── ...
├── schemas/          # Pydantic schemas
├── modules/          # Domain-specific logic
│   ├── seed_bank/    # MCPD, germplasm services
│   └── plant_sciences/
└── services/         # Business logic services
```

**Rules:**
- Only the owner may approve breaking changes
- Ownership is explicit, not implicit
- Orphaned schemas are prohibited

---

## 5. Schema Types

### 5.1 Operational Schemas (Current)

- PostgreSQL tables
- SQLAlchemy models
- Pydantic schemas

These are **source of truth** for operational data.

---

### 5.2 Interoperability Schemas

- BrAPI response/request models
- MCPD import/export models
- MIAPPE mappings (planned)
- ISA-Tab mappings (planned)

These govern **external compatibility**.

---

### 5.3 Analytical Schemas (Target)

- Parquet schemas
- Arrow schemas
- AI feature schemas

These govern **AI and analytics pipelines**.

---

## 6. Change Classification

All schema changes must be classified before implementation.

| Type | Definition | Examples |
|------|-----------|----------|
| Additive | New field, no impact | Add `stress_score` column |
| Modifying | Type/constraint change | `int` → `float` |
| Breaking | Removal/semantic change | Drop column, rename field |

---

## 7. Change Rules

### 7.1 Additive Changes

Allowed when:
- Field is nullable or has default
- Backward compatibility is preserved

**Approval:** Domain Owner

---

### 7.2 Modifying Changes

Allowed when:
- Migration is provided
- Data backfill is defined
- Impact analysis is documented

**Approval:** Domain Owner + Architecture Review

---

### 7.3 Breaking Changes

Allowed only when:
- No additive alternative exists
- Migration path is defined
- External standards are not violated
- Version bump is applied

**Approval:**
- Domain Owner
- Lead Architect
- Governance Review

Breaking changes without all three approvals are **forbidden**.

---

## 8. Schema Change Workflow (Authoritative)

```
Proposal
   ↓
Domain Owner Review
   ↓
Impact Analysis
   ↓
Migration Design
   ↓
Code Implementation
   ↓
Tests (Unit + Integration)
   ↓
Governance Review (§4.2)
   ↓
Merge
```

No step may be skipped.

---

## 9. Migration Policy

### 9.1 Alembic (Operational)

- Every change requires an Alembic migration
- No manual DB changes allowed
- Downgrade path must exist

---

### 9.2 Parquet (Target State)

- No in-place mutation
- New version directories only
- Old versions retained

---

## 10. Versioning Rules

### 10.1 Operational Schemas

- Tracked via Alembic revision IDs
- Semantic meaning changes require documentation

---

### 10.2 Interoperability Schemas

- Versioned with standard versions (BrAPI, MCPD, etc.)
- Backward compatibility guaranteed within major version

---

### 10.3 Analytical Schemas

- Versioned in directory structure
- Immutable once published

---

## 11. Standards Mapping Governance

### 11.1 BrAPI

- No deviation from core spec
- Extensions only via `additionalInfo`
- Field mappings documented

---

### 11.2 MCPD

- Must follow FAO/Bioversity codes
- No custom semantics

---

### 11.3 MIAPPE (Planned)

- Will map 1:1 where possible
- Gaps documented
- No field loss

---

### 11.4 ISA-Tab (Planned)

- Structural fidelity preserved
- Round-trip export required

---

## 12. AI Agent Schema Constraints

AI agents are **not exempt** from schema governance.

### 12.1 Agents May

- Read schema metadata
- Use documented fields
- Propose schema changes via PR

---

### 12.2 Agents May NOT

- Invent fields
- Write undeclared attributes
- Bypass validation
- Change schemas directly

---

### 12.3 Agent Output Contract

All agent-generated data must:
- Validate against schema
- Include provenance
- Be auditable

---

## 13. Schema Registry (Current + Target)

### 13.1 Current State

- SQLAlchemy models
- Pydantic schemas
- Code comments

---

### 13.2 Target State

- Dedicated schema registry service
- Versioned definitions
- Domain ownership metadata

---

## 14. Validation Requirements

Every schema must define:

- Type
- Nullability
- Units (where applicable)
- Domain meaning
- External mapping (if any)

Schemas without this metadata are **invalid**.

---

## 15. Compliance Checks

Every schema change must pass:

- Unit tests
- Integration tests
- Standards conformance
- Governance review

No exceptions.

---

## 16. What Is Explicitly Forbidden

- Undocumented fields
- Implicit schema changes
- Runtime schema mutation
- Agent-driven schema writes
- Hard-coded partner fields
- Closed schemas

---

## 17. Relationship to Other Documents

| Document | Role |
|----------|------|
| ARCHITECTURE.md | System overview |
| DATA_ARCHITECTURE_CURRENT.md | Current schema reality |
| DATA_LAKE_TARGET_ARCHITECTURE.md | Analytical schema vision |
| INTEROPERABILITY_CONTRACT.md | External contract |
| GOVERNANCE.md | Review authority |

This document enforces them.

---

## 18. Enforcement

Violations of schema governance are:
- Architectural defects
- Governance violations
- Subject to mandatory correction

No exceptions.

---

## 19. Final Statement

> **Schemas are not implementation details. They are institutional memory.**

This policy exists to protect BijMantra from silent decay.

---

End of file.

