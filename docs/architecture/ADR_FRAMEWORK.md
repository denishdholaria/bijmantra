# BijMantra Architecture Decision Record (ADR) Framework

> **Status**: AUTHORITATIVE — Binding Architectural Memory System
> **Last Verified**: January 2026
> **Governance Basis**: GOVERNANCE.md §4.2
> **Applies To**: All architectural, data, domain, schema, agent, and infrastructure decisions

---

## 1. Purpose

This document defines the **Architecture Decision Record (ADR) framework** for BijMantra.

It exists to:
- Preserve architectural intent
- Prevent decision re-litigation
- Protect long-term coherence
- Provide historical traceability
- Enable honest audits

Without ADRs, platforms forget why they exist the way they do.

---

## 2. Core Principles (Non-Negotiable)

### 2.1 Decisions Are Assets

> **An undocumented decision is a liability.**

---

### 2.2 Memory Over Myth

> **We preserve rationale, not folklore.**

---

### 2.3 Evidence Over Opinion

> **Every decision must be backed by evidence.**

---

## 3. What Requires an ADR

An ADR is mandatory for any decision that:

- Affects system architecture
- Affects domain boundaries
- Affects schema design
- Affects interoperability strategy
- Affects AI agent capabilities
- Affects data architecture
- Introduces new infrastructure
- Deprecates major components

If the decision is structural, it requires an ADR.

---

## 4. What Does NOT Require an ADR

ADRs are NOT required for:

- Bug fixes
- Refactors without semantic change
- Cosmetic UI changes
- Documentation edits

Do not pollute the ADR log.

---

## 5. ADR Lifecycle

```
Proposed
   ↓
Reviewed
   ↓
Accepted
   ↓
Implemented
   ↓
Superseded (optional)
```

Every ADR must move through these states.

---

## 6. ADR Storage & Naming

### 6.1 Location (Authoritative)

All ADRs must be stored at:

```
docs/architecture/decisions/
```

No ADRs may exist outside this directory.

---

### 6.2 Naming Convention

```
ADR-YYYYMMDD-Short-Title.md
```

Example:

```
ADR-20260115-OLTP-vs-Analytical-Split.md
```

---

## 7. ADR Template (Authoritative)

Every ADR must follow this template exactly.

```
# ADR-YYYYMMDD-Short-Title

## Status
Proposed | Accepted | Superseded

## Context
What is the problem? What forces are at play?

## Decision
What was decided?

## Rationale
Why this option over others?

## Alternatives Considered
What else was evaluated and why rejected?

## Consequences
Positive and negative outcomes.

## Evidence
Links to code, benchmarks, audits, discussions.

## Related Documents
List relevant governance documents.

```

Deviations from this template are forbidden.

---

## 8. Evidence Requirements

Every ADR must include:

- Code references (if applicable)
- Benchmarks (if performance related)
- Audit notes (if governance related)
- Risk references (RISK_MITIGATION.md)

Opinion-only ADRs are invalid.

---

## 9. Review & Approval Process

### 9.1 Who Can Propose

- Any contributor
- Any domain owner
- AI agents (via PR only)

---

### 9.2 Who Must Review

- Domain Owner (if domain affected)
- Architect
- Governance Review

---

### 9.3 Acceptance Criteria

An ADR may be accepted only when:

- Rationale is sound
- Alternatives are documented
- Evidence is provided
- No governance conflicts exist

---

## 10. Superseding Decisions

When an ADR is superseded:

- The original ADR must be updated to `Superseded`
- A link to the new ADR must be added
- Rationale for change must be documented

History is preserved. Nothing is erased.

---

## 11. Relationship to Platform Law Stack

| Document | Role |
|----------|------|
| GOVERNANCE.md | Review authority |
| PLATFORM_LAW_INDEX.md | Canonical index |
| ARCHITECTURE.md | System shape |
| DOMAIN_OWNERSHIP.md | Domain boundaries |
| SCHEMA_GOVERNANCE.md | Schema law |
| AI_AGENT_GOVERNANCE.md | Agent law |
| RELEASE_PROCESS.md | Change control |

ADRs document why these exist.

---

## 12. Enforcement

Violations of the ADR framework are:

- Architectural defects
- Governance violations
- Subject to mandatory correction

No exceptions.

---

## 13. Final Statement

> **ADRs are the memory of the institution. Without memory, architecture decays.**

This framework exists to keep BijMantra coherent over time.

---

End of file.

