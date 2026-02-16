# BijMantra Platform Law Stack

> **Status**: AUTHORITATIVE — Master Index  
> **Last Updated**: January 2026  
> **Purpose**: Single entry point to all governance documents

---

## Overview

BijMantra is governed by a formal **Platform Law Stack** — a layered system of binding documents that define architecture, boundaries, standards, and operational rules.

This is **not advisory documentation**. This is **operational law**.

---

## Document Hierarchy

```
┌─────────────────────────────────────────────────────────────────┐
│                    LAYER 1: FOUNDATION                           │
│                      GOVERNANCE.md                               │
│         (Evidence-based review, anti-sycophancy)                │
└─────────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────────┐
│                    LAYER 2: ARCHITECTURE                         │
│  ARCHITECTURE.md │ DATA_ARCH_CURRENT │ DATA_LAKE_TARGET         │
│  (System shape, operational truth, analytical vision)           │
└─────────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────────┐
│                    LAYER 3: EXTERNAL LAW                         │
│                  INTEROPERABILITY_CONTRACT.md                    │
│         (BrAPI, MCPD, MIAPPE, ISA-Tab, standards)               │
└─────────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────────┐
│                    LAYER 4: INTERNAL LAW                         │
│  DOMAIN_OWNERSHIP │ SCHEMA_GOVERNANCE │ AI_AGENT_GOVERNANCE     │
│  (Boundaries, ownership, constraints)                           │
└─────────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────────┐
│                    LAYER 5: OPERATIONS & CHANGE CONTROL          │
│  MODULE_ACCEPTANCE │ OPERATIONAL_PLAYBOOK │ RELEASE_PROCESS     │
│  (Entry gate, operations manual, change governance)             │
└─────────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────────┐
│                    LAYER 6: RESILIENCE                           │
│              RISK_MITIGATION │ ADR_FRAMEWORK                     │
│         (Risk register, architectural memory)                   │
└─────────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────────┐
│                    LAYER 7: CULTURE                              │
│                  CONTRIBUTOR_ONBOARDING.md                       │
│         (Mindset, expectations, contribution rules)             │
└─────────────────────────────────────────────────────────────────┘
```

---

## Complete Document Index

### Layer 1: Foundation

| Document | Purpose | Status |
|----------|---------|--------|
| [GOVERNANCE.md](GOVERNANCE.md) | Evidence-based review, anti-sycophancy rules | ✅ Binding |

### Layer 2: Architecture

| Document | Purpose | Status |
|----------|---------|--------|
| [ARCHITECTURE.md](ARCHITECTURE.md) | System overview, tech stack, current state | ✅ Authoritative |
| [DATA_ARCHITECTURE_CURRENT.md](DATA_ARCHITECTURE_CURRENT.md) | PostgreSQL implementation (verified) | ✅ Authoritative |
| [DATA_LAKE_TARGET_ARCHITECTURE.md](DATA_LAKE_TARGET_ARCHITECTURE.md) | Parquet/Arrow analytical layer | 🔜 Roadmap |

### Layer 3: External Law

| Document | Purpose | Status |
|----------|---------|--------|
| [INTEROPERABILITY_CONTRACT.md](INTEROPERABILITY_CONTRACT.md) | BrAPI, MCPD, MIAPPE, ISA-Tab standards | ✅ Authoritative |

### Layer 4: Internal Law

| Document | Purpose | Status |
|----------|---------|--------|
| [DOMAIN_OWNERSHIP.md](DOMAIN_OWNERSHIP.md) | Domain boundaries, ownership model | ✅ Authoritative |
| [SCHEMA_GOVERNANCE.md](SCHEMA_GOVERNANCE.md) | Schema change control, versioning | ✅ Authoritative |
| [AI_AGENT_GOVERNANCE.md](AI_AGENT_GOVERNANCE.md) | Agent constraints, permissions, audit | ✅ Authoritative |

### Layer 5: Operations & Change Control

| Document | Purpose | Status |
|----------|---------|--------|
| [MODULE_ACCEPTANCE_CRITERIA.md](MODULE_ACCEPTANCE_CRITERIA.md) | Entry gate for new modules | ✅ Authoritative |
| [OPERATIONAL_PLAYBOOK.md](OPERATIONAL_PLAYBOOK.md) | Deployment, startup, backup, incident response | ✅ Authoritative |
| [RELEASE_PROCESS.md](RELEASE_PROCESS.md) | Change governance, release workflow | ✅ Authoritative |

### Layer 6: Resilience & Memory

| Document | Purpose | Status |
|----------|---------|--------|
| [RISK_MITIGATION.md](RISK_MITIGATION.md) | Risk register, detection, mitigation | ✅ Authoritative |
| [ADR_FRAMEWORK.md](ADR_FRAMEWORK.md) | Architecture Decision Records, institutional memory | ✅ Authoritative |

### Layer 7: Culture

| Document | Purpose | Status |
|----------|---------|--------|
| [CONTRIBUTOR_ONBOARDING.md](CONTRIBUTOR_ONBOARDING.md) | Onboarding, mindset, contribution rules | ✅ Authoritative |

---

## Reading Order for New Contributors

1. **GOVERNANCE.md** — Understand review rules
2. **ARCHITECTURE.md** — Understand system shape
3. **DOMAIN_OWNERSHIP.md** — Understand boundaries
4. **CONTRIBUTOR_ONBOARDING.md** — Understand expectations
5. **MODULE_ACCEPTANCE_CRITERIA.md** — Understand entry gate

Then, based on your role:
- **Data work** → DATA_ARCHITECTURE_CURRENT.md, SCHEMA_GOVERNANCE.md
- **Integration work** → INTEROPERABILITY_CONTRACT.md
- **AI/Agent work** → AI_AGENT_GOVERNANCE.md
- **Operations** → OPERATIONAL_PLAYBOOK.md, RELEASE_PROCESS.md
- **Risk/Resilience** → RISK_MITIGATION.md, ADR_FRAMEWORK.md

---

## Implementation Status

| Category | Implemented | Planned | Total |
|----------|-------------|---------|-------|
| Foundation | 1 | 0 | 1 |
| Architecture | 2 | 1 | 3 |
| External Law | 1 (partial) | 0 | 1 |
| Internal Law | 3 | 0 | 3 |
| Operations & Change | 3 | 0 | 3 |
| Resilience & Memory | 2 | 0 | 2 |
| Culture | 1 | 0 | 1 |
| **Total** | **13** | **1** | **14** |

---


## VAJRA Addendum (Feb 2026)

The following operational rules are now binding for tenant isolation work:

1. **No recursive RLS view chains**: all tenant-aware query stacks must follow `base table (RLS) -> sec_* security barrier view -> final API view`.
2. **Single owner-check primitive**: use `app_owner_or_admin(org_id)` instead of duplicating owner/admin checks in each policy.
3. **Tenant isolation verification target**: all tables with `organization_id` must have RLS enabled and a tenant isolation policy before release.
4. **Bypass controls**: any `SECURITY DEFINER` or bypass marker must be justified and tracked in RLS audit output.

## Enforcement

All documents in this stack are **binding**. Violations are:
- Architectural defects
- Governance violations
- Subject to mandatory correction

No exceptions.

---

## Updates

This index is updated when:
- New governance documents are added
- Document status changes
- Implementation status changes

---

*This is institutional architecture, not casual documentation.*
