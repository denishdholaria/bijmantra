# **BijMantra Project – Engineering, Review, and Anti-Sycophancy Governance**

> **Status**: SUPREME LAW — Foundation of Platform Law Stack  
> **Canonical Location**: `docs/architecture/GOVERNANCE.md`  
> **Last Updated**: January 2026

---

## 1. Purpose

This document defines the **binding governance framework** for all engineering decisions, architectural reviews, and code audits within the **BijMantra** project.

It exists to ensure that:

* Technical decisions are **evidence-based**
* Reviews are **honest, inspectable, and reproducible**
* Authority is derived from  **code inspection** , not tone or seniority
* Sycophancy (agreement without evidence) is structurally prevented
* AI and human reviewers are held to **identical standards**

This document is **mandatory** for all contributors, maintainers, reviewers, and AI systems involved in the project.

---

## 2. Scope

This governance applies to:

* Backend services
* Frontend applications
* Databases and migrations
* APIs and integrations
* Security, authentication, and authorization
* Infrastructure and configuration
* AI-assisted development and reviews
* External and internal audits

---

## 3. Core Principle (Non-Negotiable)

> **No code may be judged unless it has been directly read.**

Any review not based on **direct inspection of actual source code** must be explicitly labeled as *inferential* and is  **non-authoritative** .

Violations of this principle invalidate the review for implementation or decision-making.

---

## 4. Review Classification (Mandatory Declaration)

Every review  **must declare its type before it begins** .

### 4.1 Inferential / Pattern-Based Review

**Definition**
A review based on architectural experience, patterns, or descriptions  **without direct code access** .

**Mandatory Label**

> ⚠️ Inferential Review — Not Based on Direct Code Inspection

**Restrictions**

* No file-level or function-level claims
* No refactor, deletion, or blocking authority
* No implied correctness judgments

**Permitted Outputs**

* Risk identification
* Directional guidance
* Architectural trade-offs
* Scope warnings

---

### 4.2 Code-Referenced Audit (Authoritative)

**Definition**
A review based on  **direct inspection of repository files** , including paths, modules, and code structures.

This is the **default and authoritative** review type for BijMantra.

**Capabilities Required**

* Repository clone, ZIP archive, or equivalent file access
* Explicit scope declaration

Only this review type may:

* Require refactors
* Recommend deletions
* Approve or block merges
* Declare architectural faults



### 4.3 Architectural Invariants (Non-Negotiable)

### 4.3.1 Async & Concurrency Model

**Invariant (Hard Rule)**
Never mix async endpoints with blocking I/O. Either the entire request path is async-safe, or it is fully synchronous. There is no supported middle ground.

**Rationale**
Mixing async request handlers with blocking database or I/O operations causes event-loop starvation, hidden latency, and silent failures under load. Such architectures may appear to function in development but are not production-safe.

**Enforcement**

- Async endpoints MUST use only async-compatible libraries (DB drivers, ORMs, I/O).
- Synchronous libraries MUST NOT be called from async endpoints.
- Violations MUST block merge approval.

---

## 5. Preconditions for Code-Referenced Audits

A code-referenced audit **must not begin** unless all conditions are met.

### 5.1 Access Requirement

The reviewer must have:

* A local clone, or
* A repository archive, or
* Explicit file-by-file access

### 5.2 Scope Declaration

The reviewer must declare:

* In-scope modules
* Out-of-scope modules
* Review depth (overview or surgical)

---

## 6. Mandatory Review Structure (Per File)

Every reviewed file must follow this structure:

```
File: <exact repository path>

Declared responsibility:
Observed behavior:
Evidence (code-level observation):
Problems (if any):
Risk if unchanged:
Decision:
  - KEEP
  - MODIFY
  - FREEZE
  - DELETE
Exact instructions:
```

Rules:

* All claims must be traceable to code
* Decisions must be explicit
* "Future flexibility" is not a valid justification

---

## 7. Evidence Discipline and Code Review Requirements

### 7.1 Claim–Evidence Coupling

Every strong claim must reference:

* A concrete file path
* A specific observable behavior

**Invalid**

> "This module is well-architected."

**Valid**

> "`backend/app/api/*` contains duplicated CRUD logic across multiple routers, indicating premature abstraction."

---

### 7.2 No Assumptions Rule

Reviewers must not assume:

* Async/sync misuse without reading session code
* Over-normalization without inspecting models
* Security sprawl without tracing enforcement points

When evidence is insufficient, reviewers must state:

> "Insufficient evidence — requires inspection of X."



## 7.3 Code Review Requirements

### 7.3.1 Async Safety Review (Required)

Reviewers MUST verify compliance with the async concurrency model defined in §4.2.

Any usage of:

- `async def` endpoints
- synchronous ORM sessions
- blocking file, network, or subprocess calls

MUST be flagged unless the entire request path is explicitly synchronous.

---

## 8. Epistemic Boundaries

When evidence is missing or access is incomplete, reviewers  **must use explicit boundary language** , such as:

* "I cannot assess this without access to…"
* "This is a hypothesis, not a finding."
* "Out of scope for this review."

Confidence without evidence is a governance violation.

---

## 9. Authority Limitations

No reviewer — regardless of seniority — may:

* Override this governance
* Substitute experience for inspection
* Enforce changes without evidence
* Present speculation as fact

Experience informs  **questions** , not  **conclusions** .

---

## 10. AI-Assisted Review Policy

AI systems are treated as reviewers under this governance.

Requirements:

* AI must declare access limitations
* AI outputs must be classified as inferential or code-referenced
* AI reviews without code access are **non-blocking**

AI assistance is encouraged, but  **never authoritative without evidence** .

---

## 11. Audit Outcomes

Every audit must conclude with one of the following:

* ✅ Approved for iteration
* ⚠️ Approved with mandatory changes
* ❌ Blocked pending refactor
* 🧊 Frozen (no further expansion allowed)

Each outcome must reference specific files or decisions.

---

## 12. Reviewer Self-Check (Anti-Sycophancy Section)

Before submitting any review, the reviewer  **must answer all of the following** :

1. Have I personally read the code I am judging?
2. Can I cite exact file paths for every strong claim?
3. Am I agreeing because of evidence, or because it "feels right"?
4. Have I clearly labeled inferential statements as non-authoritative?
5. Did I explicitly say "I don't know" where evidence was missing?
6. Would this review still stand if the author were anonymous?
7. Am I optimizing for correctness, not harmony?
8. Would a third party be able to reproduce my conclusions?

If any answer is  **no** , the review must be revised or downgraded.

---

## 13. Anti-Sycophancy Enforcement Rule

> **Agreement without evidence is a governance violation.**

Praise and criticism are subject to the  **same evidence requirements** .

Reviews that:

* Over-affirm without citations
* Avoid disagreement without justification
* Use vague approval language

Are considered  **structurally invalid** .

---

## 14. Enforcement

Reviews violating this governance:

* Must be marked invalid
* Must not guide implementation
* Must be re-conducted if required

This applies equally to human and AI reviewers.

---

## 15. Governance Evolution

This document:

* Is version-controlled
* May evolve
* Must never weaken evidence requirements

---

## 16. Cultural Statement

> Precision over confidence
> Evidence over authority
> Humility over speed

BijMantra prioritizes **engineering truth and long-term trust** over short-term validation.

---

## 17. Closing Intent

This governance exists to protect:

* The project
* Contributors
* Future maintainers
* Decision integrity

It is not restrictive —
it is  **protective** .

---

## 18. Canonical Location

This document is the **Supreme Law** of the BijMantra Platform Law Stack.

**Authoritative location**: `docs/architecture/GOVERNANCE.md`

Any copies in other locations (e.g., `.kiro/steering/`) are **pointers only** and must not be treated as authoritative.

See [platform_law_index.md](platform_law_index.md) for the complete governance framework.

---

*End of file.*
