# BijMantra Release Process

> **Status**: AUTHORITATIVE — Binding Change & Release Governance Policy
> **Last Verified**: January 2026
> **Governance Basis**: GOVERNANCE.md §4.2
> **Applies To**: All code, schemas, agents, modules, infrastructure, and integrations

---

## 1. Purpose

This document defines the **mandatory process by which any change is allowed to enter BijMantra**.

It exists to:
- Prevent uncontrolled change
- Enforce governance
- Protect domain boundaries
- Preserve schema integrity
- Prevent agent overreach
- Maintain platform stability

This is not bureaucracy. This is structural safety.

---

## 2. Core Principles (Non-Negotiable)

### 2.1 No Change Without Process

> **If it did not pass the release process, it does not exist.**

---

### 2.2 Structure Over Velocity

> **We move slower to avoid moving wrong.**

---

### 2.3 Reversibility Over Optimism

> **Every change must be reversible.**

---

## 3. What Constitutes a Change

A **change** includes:

- Code changes
- Schema changes
- Domain logic changes
- AI agent capability changes
- Interoperability changes
- Infrastructure changes
- Configuration changes

If it can affect behavior, it is a change.

---

## 4. Change Classification

All changes must be classified.

| Type | Definition | Examples |
|------|-----------|----------|
| **Patch** | Bug fix, no behavior change | Fix null check |
| **Minor** | Additive, backward compatible | New endpoint |
| **Major** | Breaking or semantic change | Schema rename |
| **Emergency** | Production outage/security | Hotfix |

Classification is mandatory.

---

## 5. Release Workflow (Authoritative)

```
Idea / Requirement
       ↓
Proposal
       ↓
Domain Owner Review
       ↓
Schema Review (if applicable)
       ↓
Interop Review (if applicable)
       ↓
Agent Review (if applicable)
       ↓
Architecture Review
       ↓
Governance Approval
       ↓
Implementation
       ↓
Testing (Unit + Integration + Boundary)
       ↓
Staging Deploy
       ↓
Validation
       ↓
Production Release
       ↓
Post-Release Audit
```

No step may be skipped.

---

## 6. Proposal Requirements

Every change must begin with a proposal containing:

1. **Purpose** — What problem is solved
2. **Domain fit** — Which domain owns this
3. **Schema impact** — Add/modify/break
4. **Interop impact** — Standards effect
5. **Agent impact** — New behaviors
6. **Risk assessment** — Reference RISK_MITIGATION.md
7. **Rollback plan** — How to undo

Incomplete proposals are rejected.

---

## 7. Domain Owner Review

The Domain Owner must explicitly approve:

- Domain correctness
- Boundary respect
- Semantic integrity

No owner approval → no progress.

---

## 8. Schema Review

If schemas are affected:

- Must comply with SCHEMA_GOVERNANCE.md
- Must include migrations
- Must include downgrade path

Schema violations → reject.

---

## 9. Interoperability Review

If standards are affected:

- Must comply with INTEROPERABILITY_CONTRACT.md
- Must preserve round-trip integrity
- Must not introduce proprietary lock-in

Interop violations → reject.

---

## 10. Agent Review

If agents are affected:

- Must comply with AI_AGENT_GOVERNANCE.md
- Must define allowed/forbidden actions
- Must be auditable

Agent overreach → reject.

---

## 11. Architecture Review

Architecture review checks:

- Domain boundaries
- Coupling
- Long-term impact
- Structural fit

Architecture violations → reject.

---

## 12. Governance Approval

Governance approval verifies:

- Process followed
- Evidence provided
- No sycophancy

No governance approval → no merge.

---

## 13. Implementation Rules

Implementation must:

- Follow approved design
- Not introduce hidden scope
- Not bypass review

Scope creep → reject.

---

## 14. Testing Requirements

Mandatory:

- Unit tests
- Integration tests
- Domain boundary tests
- Schema validation tests
- Agent constraint tests (if applicable)

Untested changes are forbidden.

---

## 15. Staging & Validation

All changes must:

- Deploy to staging
- Pass validation
- Be observed

No direct prod deploy.

---

## 16. Production Release

Production release must:

- Be automated
- Be versioned
- Be reversible

Manual prod changes are forbidden.

---

## 17. Post-Release Audit

Every release must include:

- Verification of behavior
- Check of logs
- Check of metrics
- Agent audit (if applicable)

Silent releases are forbidden.

---

## 18. Emergency Release Protocol

Emergency releases may bypass:

- Proposal formality
- Extended review

But may NOT bypass:

- Domain owner
- Schema law
- Agent law
- Governance sign-off

There are no lawless emergencies.

---

## 19. Rollback Policy

Every release must have:

- Clear rollback plan
- Tested rollback procedure

Unrollable releases are forbidden.

---

## 20. Versioning Rules

- Patch: x.y.Z
- Minor: x.Y.0
- Major: X.0.0

Semantic versioning is mandatory.

---

## 21. Release Notes

Every release must publish:

- What changed
- Why
- Impact
- Migration notes
- Rollback notes

No undocumented releases.

---

## 22. What Is Explicitly Forbidden

- Bypassing review
- Direct prod edits
- Schema hotfixes
- Agent experiments in prod
- Hidden changes

---

## 23. Relationship to Platform Law Stack

| Document | Role |
|----------|------|
| PLATFORM_LAW_INDEX.md | Canonical law index |
| GOVERNANCE.md | Supreme law |
| DOMAIN_OWNERSHIP.md | Domain law |
| SCHEMA_GOVERNANCE.md | Schema law |
| AI_AGENT_GOVERNANCE.md | Agent law |
| INTEROPERABILITY_CONTRACT.md | External law |
| RISK_MITIGATION.md | Risk register |
| OPERATIONAL_PLAYBOOK.md | Operations |

This process enforces them.

---

## 24. Enforcement

Violations of the release process are:

- Architectural defects
- Governance violations
- Subject to mandatory correction

No exceptions.

---

## 25. Final Statement

> **Release discipline is the difference between a platform and a liability.**

This process exists to keep BijMantra safe as it evolves.

---

End of file.
