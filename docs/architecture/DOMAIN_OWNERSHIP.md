# BijMantra Domain Ownership & Boundaries

> **Status**: AUTHORITATIVE — Binding Governance Policy
> **Last Verified**: January 2026
> **Governance Basis**: GOVERNANCE.md §4.2 (Evidence-Based, Code-Referenced)
> **Applies To**: All domains, modules, schemas, agents, services, and integrations

---

## 1. Purpose

This document defines the **formal domain model, ownership rules, and boundary constraints** for BijMantra.

It specifies:
- What constitutes a domain
- Which domains exist
- Who owns each domain
- What each domain is allowed to own
- What each domain is forbidden to touch
- How cross-domain interactions are governed
- How AI agents are constrained by domain boundaries

This exists to prevent:
- Domain bleed
- Architectural erosion
- Schema entanglement
- Agent overreach
- Long-term platform decay

---

## 2. Core Principles (Non-Negotiable)

### 2.1 Domains Are Law

> **If ownership is unclear, the architecture is broken.**

Every piece of data, logic, and schema must belong to exactly one domain.

---

### 2.2 Single Ownership

> **Every domain has one owner. No committees. No ambiguity.**

Shared ownership is forbidden.

---

### 2.3 Boundary Integrity

> **Cross-domain access is a privilege, not a right.**

No domain may directly manipulate another domain’s internal structures.

---

## 3. What Is a Domain (Authoritative Definition)

A **domain** in BijMantra is:
- A coherent area of agricultural knowledge or platform responsibility
- With its own schemas, logic, invariants, and evolution path
- Owned by a single accountable authority

Domains are **not**:
- UI sections
- Database schemas
- Teams
- Convenience groupings

Domains are **architectural units**.

---

## 4. Canonical Domain List

The following domains are authoritative. No new domain may be created without governance approval.

| Domain | Description | Primary Module Path | Owner |
|--------|-------------|---------------------|-------|
| **Germplasm** | Accessions, seed lots, pedigree, passport data | `backend/app/modules/seed_bank/` | Seed Bank Lead |
| **Phenotype** | Traits, observations, methods, scales | `backend/app/modules/phenotype/` | Phenotype Lead |
| **Genotype** | Markers, variants, calls, maps | `backend/app/modules/genomics/` | Genomics Lead |
| **Trials & Studies** | Programs, trials, studies, designs | `backend/app/modules/trials/` | Trial Lead |
| **Environment & Climate** | Weather, soil, geospatial | `backend/app/modules/environment/` | Environment Lead |
| **Analytics & AI** | Models, features, inference | `backend/app/services/ai/` | AI Lead |
| **Interop & Standards** | BrAPI, MCPD, MIAPPE, ISA | `backend/app/api/brapi/` | Interop Lead |
| **Security & Identity** | Auth, RBAC, tenancy | `backend/app/core/auth/` | Security Lead |
| **Infrastructure** | Storage, queues, compute | `compose.yaml`, infra | Platform Lead |

**Rules:**
- Each domain must have exactly one owner
- Ownership must be documented
- Orphan domains are forbidden

---

## 5. Domain Ownership Rights & Duties

Each Domain Owner is responsible for:

- Schema design and evolution
- Business invariants
- Standards mapping
- Migration approval
- Cross-domain contract integrity

Each Domain Owner has authority to:

- Approve additive changes
- Reject incompatible changes
- Demand refactors for boundary violations

No Domain Owner may:

- Change another domain’s schema
- Bypass governance workflow
- Delegate ownership without approval

---

## 6. Allowed & Forbidden Actions Per Domain

### 6.1 Germplasm Domain

**Owns:**
- Accessions
- Seed lots
- Pedigree
- MCPD fields

**May NOT:**
- Define traits
- Store observations
- Infer phenotypes

---

### 6.2 Phenotype Domain

**Owns:**
- Traits
- Scales
- Methods
- Observations

**May NOT:**
- Redefine germplasm
- Modify pedigree
- Store genotypes

---

### 6.3 Genotype Domain

**Owns:**
- Markers
- Variants
- Calls
- Genetic maps

**May NOT:**
- Store phenotypes
- Define trials
- Modify germplasm identity

---

### 6.4 Trials & Studies Domain

**Owns:**
- Programs
- Trials
- Studies
- Designs

**May NOT:**
- Redefine traits
- Change genotypes
- Modify passport data

---

### 6.5 Environment & Climate Domain

**Owns:**
- Weather
- Soil
- Spatial layers

**May NOT:**
- Modify trials
- Define traits
- Alter germplasm

---

### 6.6 Analytics & AI Domain

**Owns:**
- Feature schemas
- Model outputs
- Predictions

**May NOT:**
- Redefine source domains
- Write back to operational domains without contract

---

### 6.7 Interop & Standards Domain

**Owns:**
- BrAPI mapping
- MCPD mapping
- MIAPPE mapping (planned)
- ISA mapping (planned)

**May NOT:**
- Invent domain semantics
- Change internal meaning

---

### 6.8 Security & Identity Domain

**Owns:**
- Users
- Roles
- Permissions
- Tenancy

**May NOT:**
- Access domain data without policy
- Modify business logic

---

### 6.9 Infrastructure Domain

**Owns:**
- Storage
- Queues
- Compute

**May NOT:**
- Define business schema
- Alter domain logic

---

## 7. Cross-Domain Interaction Rules

All cross-domain interaction must occur via:

- Explicit service interfaces
- Documented contracts
- Versioned schemas

**Direct table access across domains is forbidden.**

---

## 8. Cross-Domain Workflow Pattern (Authoritative)

```
Domain A
   ↓ (contract)
Domain B
   ↓ (projection)
Domain C
```

No domain may skip another domain’s contract.

---

## 9. Schema Boundary Enforcement

Schemas are domain-scoped.

- A schema belongs to exactly one domain
- Other domains may reference, never own
- Ownership is encoded in directory structure

Violations are governance defects.

---

## 10. AI Agent Domain Constraints

AI agents are subject to domain boundaries.

### 10.1 Agents May

- Read across domains
- Propose cross-domain workflows
- Trigger services

---

### 10.2 Agents May NOT

- Write across domains directly
- Invent cross-domain links
- Bypass domain contracts

---

### 10.3 Agent Enforcement

All agent actions must:
- Declare domain intent
- Use domain interfaces
- Be auditable

---

## 11. Domain Evolution Policy

### 11.1 Adding a Domain

Requires:
- Architectural justification
- Owner assignment
- Governance approval

---

### 11.2 Merging Domains

Allowed only when:
- Semantics are truly inseparable
- Both owners agree
- Migration path exists

---

### 11.3 Splitting Domains

Allowed when:
- Complexity demands
- Boundaries are clear
- Ownership is reassigned

---

## 12. Domain & LOKAS Alignment

Domains must align with the **LOKAS structure** and **Parashakti framework**.

No domain may violate:
- LOKAS boundary rules
- Parashakti module isolation

---

## 13. Compliance & Audit

Every domain must pass:

- Boundary audit
- Ownership audit
- Schema ownership check

Failure is a governance violation.

---

## 14. What Is Explicitly Forbidden

- Cross-domain table writes
- Shared schema ownership
- Implicit domain coupling
- Agent domain bypass
- Domain logic in UI

---

## 15. Relationship to Other Governance Documents

| Document | Role |
|----------|------|
| ARCHITECTURE.md | System shape |
| DATA_ARCHITECTURE_CURRENT.md | Operational truth |
| DATA_LAKE_TARGET_ARCHITECTURE.md | Analytical vision |
| INTEROPERABILITY_CONTRACT.md | External law |
| SCHEMA_GOVERNANCE.md | Schema law |
| GOVERNANCE.md | Review authority |

This document enforces domain integrity.

---

## 16. Enforcement

Violations of domain ownership are:
- Architectural defects
- Governance violations
- Subject to mandatory correction

No exceptions.

---

## 17. Final Statement

> **Domains are the skeleton of the platform. Break them, and the system collapses.**

This policy exists to prevent that.

---

End of file.
