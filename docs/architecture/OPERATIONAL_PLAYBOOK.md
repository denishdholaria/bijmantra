# BijMantra Operational Playbook

> **Status**: AUTHORITATIVE — Binding Operations Manual
> **Last Verified**: January 2026
> **Governance Basis**: GOVERNANCE.md §4.2
> **Applies To**: All deployments, environments, operators, maintainers, and automation

---

## 1. Purpose

This document defines **how BijMantra is run in practice** under the Platform Law Stack.

It specifies:
- How the platform is deployed
- How it is started and stopped
- How it is migrated
- How it is backed up and restored
- How incidents are handled
- How audits are performed

This exists to prevent:
- Ad‑hoc operations
- Hero debugging
- Environment drift
- Data loss
- Unrecoverable incidents

This is not optional. This is how the platform survives.

---

## 2. Operational Principles (Non‑Negotiable)

### 2.1 Automation Over Heroics

> **If it requires a person to remember, it will eventually fail.**

All critical operations must be automated.

---

### 2.2 Reproducibility Over Convenience

> **If it cannot be reproduced, it is not understood.**

All environments must be reproducible from source.

---

### 2.3 Safety Over Speed

> **We prefer controlled recovery over fast failure.**

---

## 3. Environment Model

BijMantra operates in the following environments:

| Environment | Purpose |
|-------------|---------|
| **Local** | Developer machines |
| **Dev** | Integration testing |
| **Staging** | Pre‑production validation |
| **Prod** | Live platform |

**Rules:**
- No direct production testing
- No schema experiments in prod
- No unreviewed hotfixes

---

## 4. Deployment Model

### 4.1 Source of Truth

- Git repository is the single source of truth
- `main` branch is production‑eligible
- Feature branches only

---

### 4.2 Build

All builds must be:

- Deterministic
- Versioned
- Traceable to commit hash

No local builds are allowed in production.

---

### 4.3 Deploy

Deployments must:

- Be automated (CI/CD)
- Be idempotent
- Support rollback

Manual SSH deployment is forbidden.

---

## 5. Startup & Shutdown Procedures

### 5.1 Startup Order (Authoritative)

1. Infrastructure (network, storage)
2. Database (PostgreSQL)
3. Object storage (MinIO)
4. Backend services (FastAPI)
5. Frontend (PWA)
6. AI services (if enabled)

---

### 5.2 Shutdown Order

1. Frontend
2. AI services
3. Backend services
4. Object storage
5. Database
6. Infrastructure

Graceful shutdown is mandatory.

---

## 6. Database Operations

### 6.1 Migrations

- Only via Alembic
- No manual DDL
- Downgrade path required

Migrations must be tested in staging before prod.

---

### 6.2 Backups

- Automated daily backups
- Encrypted at rest
- Off‑site storage

---

### 6.3 Restore Procedure

1. Identify backup point
2. Provision clean DB instance
3. Restore snapshot
4. Run migrations
5. Validate integrity

No partial restores.

---

## 7. Object Storage (MinIO)

- Versioning enabled
- Lifecycle policies defined
- Access via service accounts only

No direct human writes.

---

## 8. Configuration Management

- All config in environment variables
- No secrets in code
- Secrets via secure vault

Config drift is forbidden.

---

## 9. Logging & Monitoring

### 9.1 Logging

- Structured logs
- Correlation IDs
- Agent actions logged

---

### 9.2 Monitoring

- Health checks
- Resource metrics
- Error rates

Silent failure is forbidden.

---

## 10. Incident Response

### 10.1 Definition of Incident

An incident is any event that:

- Violates data integrity
- Breaks interoperability
- Causes agent misbehavior
- Affects availability

---

### 10.2 Incident Protocol (Authoritative)

```
Detect
  ↓
Contain
  ↓
Assess
  ↓
Mitigate
  ↓
Recover
  ↓
Post‑mortem
```

---

### 10.3 Communication

- No public speculation
- Internal facts only
- Single incident lead

---

## 11. Rollback Policy

All deployments must support:

- Immediate rollback
- Data‑safe rollback

No forward‑only deployments.

---

## 12. Security Operations

### 12.1 Access Control

- RBAC enforced
- Least privilege
- No shared accounts

---

### 12.2 Audit

- Regular audits
- Agent action audits
- Access audits

---

## 13. AI Operations

### 13.1 Agent Enablement

- Explicit enable per environment
- Staging first
- Kill switch available

---

### 13.2 Agent Failure Handling

- Auto‑suspend on repeated error
- Human review required

---

## 14. Data Interoperability Operations

- BrAPI endpoints monitored
- Export jobs validated
- Standards compliance checked

Interop breakage is critical severity.

---

## 15. Change Management

All operational changes must:

- Be documented
- Be reviewed
- Be reversible

---

## 16. Disaster Recovery

### 16.1 Definition

Disaster includes:

- Total data loss
- Infrastructure compromise
- Security breach

---

### 16.2 Recovery Plan

1. Isolate
2. Restore from backup
3. Rebuild services
4. Validate
5. Resume

No shortcuts.

---

## 17. Audit & Compliance

Regular audits must cover:

- Domain boundaries
- Schema integrity
- Agent behavior
- Interoperability

---

## 18. Forbidden Practices

- Manual prod changes
- Untracked config edits
- Hotfix without review
- Data patching in prod
- Agent experimentation in prod

---

## 19. Relationship to Platform Law Stack

| Document | Role |
|----------|------|
| PLATFORM_LAW_INDEX.md | Canonical law index |
| GOVERNANCE.md | Supreme law |
| ARCHITECTURE.md | System shape |
| DOMAIN_OWNERSHIP.md | Domain boundaries |
| SCHEMA_GOVERNANCE.md | Schema law |
| AI_AGENT_GOVERNANCE.md | Agent law |
| RISK_MITIGATION.md | Risk register |

This playbook enforces them operationally.

---

## 20. Final Statement

> **Operations is where architecture is tested by reality.**

This playbook exists to ensure BijMantra survives contact with the real world.

---

End of file.

