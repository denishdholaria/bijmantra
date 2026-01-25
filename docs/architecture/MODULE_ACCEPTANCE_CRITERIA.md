# BijMantra Module Acceptance Criteria

> **Status**: AUTHORITATIVE — Binding Governance Policy
> **Last Verified**: January 2026
> **Governance Basis**: GOVERNANCE.md §4.2 (Evidence-Based, Code-Referenced)
> **Applies To**: All current and future modules, features, plugins, and extensions

---

## 1. Purpose

This document defines the **mandatory acceptance criteria** for any module to be admitted into the BijMantra platform.

It exists to prevent:
- Feature creep
- Architectural dilution
- Domain leakage
- Quality collapse
- Governance bypass

No module is allowed to enter the codebase without satisfying **all** criteria in this document.

---

## 2. Core Principles (Non-Negotiable)

### 2.1 Structure Before Features

> **A feature without structure is technical debt in disguise.**

Modules must fit the architecture, not bend it.

---

### 2.2 Domain Purity

> **If a module violates domain boundaries, it is rejected.**

All modules must comply with DOMAIN_OWNERSHIP.md.

---

### 2.3 Schema Discipline

> **If a module invents fields, it is rejected.**

All data must comply with SCHEMA_GOVERNANCE.md.

---

### 2.4 Interoperability First

> **If a module traps data, it is rejected.**

All data must be exportable per INTEROPERABILITY_CONTRACT.md.

---

## 3. What Qualifies as a Module

A **module** is any self-contained unit that introduces:
- New domain logic
- New schemas
- New workflows
- New compute pipelines
- New user-facing capabilities

This includes:
- Backend domain modules
- Frontend divisions
- AI pipelines
- WASM engines
- Integrations

---

## 4. Mandatory Preconditions

Before review, the module must provide:

1. **Domain Declaration**
   - Which domain it belongs to
   - Owner identified

2. **Purpose Statement**
   - What problem it solves
   - Why it belongs in BijMantra

3. **Non-Goals**
   - What it explicitly does NOT attempt

4. **Standards Impact Analysis**
   - BrAPI impact
   - MCPD impact
   - MIAPPE/ISA impact (if relevant)

5. **Schema Impact Analysis**
   - New fields
   - Modified fields
   - Breaking changes (if any)

6. **Agent Impact Analysis**
   - Whether agents will interact with it
   - How agents are constrained

Modules missing any of the above are **automatically rejected**.

---

## 5. Architectural Fit Checklist (Hard Gate)

The following must be **explicitly answered and verified**:

| Check | Requirement |
|------|-------------|
| Domain fit | Does it belong to exactly one domain? |
| Boundary respect | Does it avoid cross-domain writes? |
| Schema compliance | Does it use governed schemas only? |
| Interop compliance | Is data exportable via standards? |
| Agent safety | Are agent actions constrained? |
| LOKAS alignment | Does it respect LOKAS boundaries? |
| Parashakti alignment | Does it fit module isolation rules? |

Any **No** → **Reject**.

---

## 6. Technical Quality Gates

### 6.1 Code Quality

- Typed interfaces
- Clear separation of concerns
- No dead code
- No TODOs in critical paths

---

### 6.2 Testing

Mandatory:
- Unit tests
- Integration tests
- Domain boundary tests
- Schema validation tests

Coverage must be meaningful, not cosmetic.

---

### 6.3 Performance

- No N+1 queries
- No blocking I/O in async paths
- No unbounded memory usage

---

### 6.4 Security

- RBAC enforced
- No privilege escalation
- No direct DB access from frontend

---

## 7. Data Discipline Requirements

Modules must:

- Use existing schemas or propose new ones via SCHEMA_GOVERNANCE workflow
- Respect domain ownership
- Avoid duplicating data
- Avoid shadow schemas

Any shadow schema → **Reject**.

---

## 8. Interoperability Requirements

Modules must:

- Use BrAPI endpoints where applicable
- Respect MCPD mappings (for germplasm)
- Preserve standards fields
- Not introduce proprietary-only formats

Any proprietary lock-in → **Reject**.

---

## 9. AI & Agent Compatibility

If the module interacts with AI agents:

- Must define agent interface
- Must define allowed actions
- Must define forbidden actions
- Must be auditable

Undeclared agent interaction → **Reject**.

---

## 10. Compute & WASM Integration (If Applicable)

If the module introduces compute engines:

- Must define language boundary (Fortran/Rust/WASM/Python)
- Must define data interchange format
- Must define memory ownership
- Must define error handling

Unspecified compute boundaries → **Reject**.

---

## 11. Documentation Requirements

Each module must include:

- README.md
- Architecture diagram
- Data flow diagram
- API contract
- Example usage

No documentation → **Reject**.

---

## 12. Review Workflow (Authoritative)

```
Proposal
   ↓
Domain Owner Review
   ↓
Schema Review
   ↓
Interop Review
   ↓
Agent Review (if applicable)
   ↓
Architecture Review
   ↓
Governance Approval
   ↓
Merge
```

No step may be skipped.

---

## 13. Rejection Criteria (Immediate Fail)

A module is immediately rejected if:

- It violates domain boundaries
- It invents schemas
- It traps data
- It bypasses standards
- It bypasses governance
- It introduces hidden coupling

No exceptions.

---

## 14. Sunset & Removal Policy

Modules may be removed when:

- Obsolete
- Superseded
- Architecturally harmful

Removal requires:

- Impact analysis
- Migration plan
- Governance approval

---

## 15. Relationship to Other Governance Documents

| Document | Role |
|----------|------|
| ARCHITECTURE.md | System shape |
| DOMAIN_OWNERSHIP.md | Domain law |
| SCHEMA_GOVERNANCE.md | Schema law |
| INTEROPERABILITY_CONTRACT.md | External law |
| AI_AGENT_GOVERNANCE.md | Agent law |
| GOVERNANCE.md | Review authority |

This document enforces entry control.

---

## 16. Enforcement

Violations of module acceptance criteria are:
- Architectural defects
- Governance violations
- Subject to mandatory correction

No exceptions.

---

## 17. Final Statement

> **BijMantra is not a feature playground. It is an institutional platform.**

This policy exists to protect it from dilution.

---

End of file.
