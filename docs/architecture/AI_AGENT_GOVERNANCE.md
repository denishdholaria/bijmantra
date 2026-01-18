# BijMantra AI Agent Governance

> **Status**: AUTHORITATIVE — Binding Governance Policy
> **Last Verified**: January 2026
> **Governance Basis**: GOVERNANCE.md §4.2 (Evidence-Based, Code-Referenced)
> **Applies To**: Veena, all current and future AI agents, tools, and orchestrators

---

## 1. Purpose

This document defines the **binding governance model for all AI agents** operating within BijMantra.

It specifies:
- What agents are
- What agents may and may not do
- How agents interact with schemas, domains, and standards
- How agent actions are audited
- How agent capabilities are introduced safely

This exists to prevent:
- Agent overreach
- Silent data corruption
- Domain violations
- Schema drift
- Uncontrolled automation

---

## 2. Core Principles (Non-Negotiable)

### 2.1 Agents Are Operators, Not Authorities

> **Agents execute intent. They do not define truth.**

Agents may act, but they do not own data, schemas, or domains.

---

### 2.2 No Privileged Access

> **Agents have no rights that humans do not have.**

All permissions are inherited from the calling identity and RBAC policy.

---

### 2.3 Determinism Over Autonomy

> **We prefer predictable behavior over clever behavior.**

Agents must be inspectable, reproducible, and bounded.

---

## 3. Definition of an AI Agent

An **AI agent** in BijMantra is any system that:
- Interprets natural language or high-level intent
- Plans actions
- Invokes tools, services, or workflows
- Operates across one or more domains

Examples:
- Veena (assistant)
- Background orchestration agents
- ETL automation agents
- External agent integrations via MCP

---

## 4. Agent Classification

| Class | Description | Examples |
|-------|-------------|----------|
| **Advisory** | Read-only, recommendation | Veena Q&A mode |
| **Operational** | Executes workflows | Data import agent |
| **Orchestrator** | Multi-system coordination | Cross-institution pipeline |
| **Analytical** | Feature extraction, modeling | AI feature builder |

Each agent must declare its class.

---

## 5. Agent Registration & Identity

All agents must be:
- Registered
- Identified
- Versioned

### 5.1 Required Metadata

```yaml
agent:
  name: veena
  version: 1.3.0
  class: advisory
  owner: AI Lead
  domains: [phenotype, genotype, trials]
  permissions: r/o
```

Unregistered agents are forbidden.

---

## 6. Domain Constraints (Authoritative)

Agents are subject to **DOMAIN_OWNERSHIP.md**.

### 6.1 Agents May

- Read across domains
- Propose cross-domain workflows
- Trigger domain services via contracts

---

### 6.2 Agents May NOT

- Write across domains directly
- Modify domain schemas
- Bypass domain interfaces
- Invent domain semantics

Violations are governance defects.

---

## 7. Schema Constraints

Agents are subject to **SCHEMA_GOVERNANCE.md**.

### 7.1 Agents May

- Read schema metadata
- Validate outputs against schema
- Propose schema changes via PR

---

### 7.2 Agents May NOT

- Invent fields
- Write undeclared attributes
- Perform runtime schema mutation

---

## 8. Interoperability Constraints

Agents are subject to **INTEROPERABILITY_CONTRACT.md**.

### 8.1 Agents May

- Use BrAPI endpoints
- Trigger MCPD export/import
- Orchestrate standards-compliant workflows

---

### 8.2 Agents May NOT

- Bypass standards
- Emit proprietary-only formats
- Break round-trip compatibility

---

## 9. Permission & RBAC Model

### 9.1 Inheritance

Agents inherit permissions from:
- User context (if interactive)
- Service account (if autonomous)

No agent has implicit admin rights.

---

### 9.2 Least Privilege

> **Agents operate under the minimum permissions required.**

Over-scoped permissions are forbidden.

---

## 10. Tool Invocation Rules

All agent tool calls must be:
- Explicit
- Logged
- Auditable

### 10.1 Allowed

- API calls
- Service calls
- ETL triggers

---

### 10.2 Forbidden

- Direct database access
- Shell execution
- File system mutation

---

## 11. Workflow Orchestration Rules

Agents may orchestrate workflows only when:

- Each step is standards-compliant
- Domain contracts are respected
- Failure paths are defined
- Rollback is possible

---

## 12. Audit & Traceability (Mandatory)

Every agent action must record:

```yaml
action_id: uuid
timestamp: ISO-8601
agent: veena@1.3.0
intent: "export trial observations"
domains: [trials, phenotype]
tools: [brapi.export]
status: success|failure
```

No silent actions.

---

## 13. Explainability Requirements

Agents must be able to:

- Explain why an action was taken
- Cite data sources
- Reference schemas and standards

Opaque reasoning is forbidden.

---

## 14. Safety & Kill Switch

### 14.1 Emergency Disable

All agents must support:

- Immediate disable
- Session termination
- Workflow abort

---

### 14.2 Auto-Suspend

Agents must auto-suspend on:

- Repeated failures
- Schema violations
- Domain boundary violations

---

## 15. Capability Expansion Policy

New agent capabilities require:

- Architectural justification
- Domain owner review
- Schema impact analysis
- Governance approval

No capability creep.

---

## 16. Testing Requirements

All agents must have:

- Unit tests
- Integration tests
- Boundary tests (domain + schema)
- Interop tests

Untested agents are forbidden.

---

## 17. What Is Explicitly Forbidden

- Self-modifying agents
- Autonomous schema changes
- Hidden actions
- Non-auditable workflows
- Privileged bypass
- Cross-domain writes

---

## 18. Relationship to Other Governance Documents

| Document | Role |
|----------|------|
| ARCHITECTURE.md | System shape |
| DOMAIN_OWNERSHIP.md | Domain law |
| SCHEMA_GOVERNANCE.md | Schema law |
| INTEROPERABILITY_CONTRACT.md | External law |
| DATA_ARCHITECTURE_CURRENT.md | Operational truth |
| DATA_LAKE_TARGET_ARCHITECTURE.md | Analytical vision |
| GOVERNANCE.md | Review authority |

This document governs all agents.

---

## 19. Enforcement

Violations of AI agent governance are:
- Architectural defects
- Governance violations
- Subject to mandatory correction

No exceptions.

---

## 20. Final Statement

> **Agents are force multipliers. Ungoverned, they become force amplifiers of error.**

This policy exists to ensure BijMantra gains intelligence without losing control.

---

End of file.

