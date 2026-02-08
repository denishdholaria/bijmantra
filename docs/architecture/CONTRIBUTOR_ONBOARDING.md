# BijMantra Contributor Onboarding Guide

> **Status**: AUTHORITATIVE — Binding Onboarding & Culture Document
> **Last Verified**: January 2026
> **Governance Basis**: GOVERNANCE.md §4.2
> **Applies To**: All contributors (human and AI), maintainers, reviewers, and integrators

---

## 1. Purpose

This document defines the **mandatory onboarding process, cultural expectations, and operational rules** for contributing to BijMantra.

It exists to ensure that every contributor:
- Understands the architecture
- Respects governance
- Protects domain boundaries
- Preserves interoperability
- Does not introduce entropy

BijMantra is **not a casual open-source project**. It is an institutional platform.

---

## 2. First Principle (Non-Negotiable)

> **If you have not read the architecture, you are not ready to code.**

No contribution is accepted from anyone who has not read and acknowledged:

- ARCHITECTURE.md
- DATA_ARCHITECTURE_CURRENT.md
- DATA_LAKE_TARGET_ARCHITECTURE.md
- INTEROPERABILITY_CONTRACT.md
- SCHEMA_GOVERNANCE.md
- DOMAIN_OWNERSHIP.md
- AI_AGENT_GOVERNANCE.md
- MODULE_ACCEPTANCE_CRITERIA.md

This is mandatory.

---

## 3. Who Can Contribute

Contributors may be:

- Core maintainers
- Domain specialists
- AI/ML engineers
- Frontend engineers
- Infrastructure engineers
- Research collaborators
- External integrators

All are subject to the same governance rules.

---

## 4. Required Mindset

### 4.1 Architecture Over Ego

> **You are not here to be clever. You are here to be correct.**

Personal style, preferences, or habits do not override architecture.

---

### 4.2 Evidence Over Opinion

> **If you cannot point to code, it does not count.**

Design claims must be supported by implementation.

---

### 4.3 Discipline Over Speed

> **We move slowly to avoid moving wrongly.**

Fast wrong work is more expensive than slow correct work.

---

## 5. Onboarding Steps (Authoritative)

### Step 1 — Read the Law

Read all governance documents listed in §2.

---

### Step 2 — Domain Declaration

Declare which domain you intend to work in:

- Germplasm
- Phenotype
- Genotype
- Trials & Studies
- Environment & Climate
- Analytics & AI
- Interop & Standards
- Security & Identity
- Infrastructure

No multi-domain ownership without approval.

---

### Step 3 — Owner Contact

Contact the Domain Owner before writing code.

No unilateral work.

---

### Step 4 — Proposal

Before coding, submit:

- Purpose
- Domain fit
- Schema impact
- Interop impact
- Agent impact (if any)

Unproposed work will be rejected.

---

## 6. What You Are Allowed to Do

- Fix bugs in your declared domain
- Improve tests
- Improve documentation
- Propose schema changes via workflow
- Propose new modules via MODULE_ACCEPTANCE_CRITERIA.md

---

## 7. What You Are NOT Allowed to Do

- Change schemas without approval
- Cross domain boundaries
- Add proprietary formats
- Bypass standards
- Add hidden fields
- Bypass RBAC
- Introduce side effects

Any of the above will result in rejection.

---

## 8. Code Contribution Rules

### 8.1 No Drive-By PRs

> **If you cannot explain why this belongs in BijMantra, do not submit it.**

---

### 8.2 No Feature Creep

> **New features require architectural justification.**

---

### 8.3 No Schema Drift

> **Schemas are governed. Treat them as law.**

---

## 9. Review Expectations

Every PR will be reviewed for:

- Domain compliance
- Schema compliance
- Interoperability compliance
- Agent safety
- Architectural fit

Style is secondary. Structure is primary.

---

## 10. Testing Expectations

Mandatory:

- Unit tests
- Integration tests
- Boundary tests

Untested code is not merged.

---

## 11. Interaction with AI Agents

If your code interacts with Veena or any agent:

- You must read AI_AGENT_GOVERNANCE.md
- You must define allowed actions
- You must define forbidden actions
- You must ensure auditability

---

## 12. External Contributors & Integrators

External systems must:

- Use BrAPI v2.1
- Respect MCPD where applicable
- Follow INTEROPERABILITY_CONTRACT.md

No vendor-specific shortcuts.

---

## 13. Communication Rules

- Be precise
- Be respectful
- Be evidence-based
- Be concise

No architectural debate without code evidence.

---

## 14. Rejection Is Normal

> **Rejection is not punishment. It is quality control.**

Do not take it personally.

---

## 15. Escalation Path

If you disagree with a decision:

1. Domain Owner
2. Architecture Review
3. Governance Review

No public arguments. No side channels.

---

## 16. Removal & Ban Policy

Contributors may be removed for:

- Repeated governance violations
- Domain boundary violations
- Schema abuse
- Agent misuse
- Standards bypass

This is rare but non-negotiable.

---

## 17. Relationship to Other Documents

| Document | Role |
|----------|------|
| ARCHITECTURE.md | System overview |
| DOMAIN_OWNERSHIP.md | Domain law |
| SCHEMA_GOVERNANCE.md | Schema law |
| INTEROPERABILITY_CONTRACT.md | External law |
| AI_AGENT_GOVERNANCE.md | Agent law |
| MODULE_ACCEPTANCE_CRITERIA.md | Entry gate |
| GOVERNANCE.md | Review authority |

This document transmits culture.

---

## 18. Final Statement

> **BijMantra is not a sandbox. It is a long-term platform.**

Contribute accordingly.

---

End of file.

