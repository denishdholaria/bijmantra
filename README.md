<div align="center">

<img src="frontend/public/icons/icon-512x512.png" alt="BijMantra Logo" width="180"/>

# BijMantra

## (Under Development)

### Cross-domain agricultural intelligence platform for breeding, seed, research, and institutional workflows

</div>

---

## ⚠️ Important Notice — Official BijMantra Domain

A third-party website is operating under **bijmantra.com**, which is not affiliated with, operated by, or endorsed by the BijMantra project team.

**The official project is only available at:** https://bijmantra.org and the [official GitHub repository](https://github.com/denishdholaria/bijmantra.git).

While the license permits reuse and modification of the codebase, it does not permit representation as the official project or use of BijMantra branding in a way that creates confusion around origin or affiliation. Do not share data, credentials, or make payments on third-party deployments claiming association with BijMantra.

---

# **Status as of <!-- METRIC:LAST_UPDATED -->2026-05-28<!-- /METRIC -->:**

* BijMantra is currently undergoing significant backend refactoring and architectural improvements. These changes are foundational to the platform's long-term stability, scalability, and feature roadmap. 

* Development speed is constrained by personal funding — GitHub, Copilot, and AI tooling subscriptions are self-financed for a project of this scale. This limits the exploratory iteration that has historically shaped the product: trialing different approaches across UI, workflows, menu systems, and AI integrations — much like climbing a mountain, there is more than one path to the peak, and finding the right one takes deliberate experimentation.

* The repository is currently mid-refactor and in a fractured state — the app cannot be started from the latest commits. If you wish to run BijMantra locally, please use the last snapshot tag. We will update this notice once the refactor reaches a runnable state. We appreciate your patience and understanding during this phase.

* Every decision now has to count. We are building carefully, not quickly. We appreciate your patience and understanding during this phase.

🌐 **[bijmantra.org](https://bijmantra.org)**

---

[![Stars](https://img.shields.io/github/stars/denishdholaria/bijmantra?style=for-the-badge\&logo=github\&color=gold)](https://github.com/denishdholaria/bijmantra)

[**Get Started**](#quick-start) · [**Current Reality**](#current-reality) · [**Contributing**](#contributing) · [**Docs**](#key-documents)

---

## A Note on Documentation Accuracy

BijMantra is under active development across genomics, agronomy, AI, interoperability, and full-stack engineering. Exact totals move quickly.

For implementation counts and the latest repository snapshot, prefer [metrics.json](metrics.json).
If you find discrepancies, please open an issue.

---

## What BijMantra Is

BijMantra is a server-backed agricultural intelligence platform designed for:

* breeding programs
* seed organizations
* research institutions
* agricultural administrators

It connects workflows typically split across separate systems: plant breeding, germplasm, seed operations, environmental context, research knowledge, and institutional administration.

This is not a generic dashboard layer. The goal is to reduce fragmentation by keeping genetic, operational, environmental, and institutional context closer together.

At a broader level, BijMantra is being shaped as an advanced agricultural extension system—bridging scientific discovery, institutional validation, and field adoption.

---

## Why Institutions Care

Agricultural decisions rarely exist in isolation.

Breeding strategy, trials, seed operations, environment, and reporting often exist in separate systems, increasing coordination cost and slowing impact.

BijMantra is built for organizations that need:

* integrated breeding and genomics workflows
* seed system coordination
* cross-department research data linkage
* interoperable institutional infrastructure

The core thesis:
**Decisions improve when context is unified instead of manually reconciled.**

---

## Why This Is Hard

BijMantra sits at the intersection of:

* breeding, seed systems, field operations, and environment
* long validation cycles (5–15 years)
* inconsistent data quality and institutional variation
* need for provenance, assumptions, and uncertainty modeling
* hybrid compute and infrastructure complexity

The challenge is not just software—it is building systems that carry **trusted agricultural insight across domains**.

---

## Current Scope

BijMantra remains in preview.

The repository spans multiple domains but does not yet reflect uniform maturity across modules. Some areas are functional, others are being hardened, and some remain as structural placeholders.

---

## What Is Still In Progress

* Cross-module validation and consistency
* Provenance and evidence integrity
* Low-connectivity workflow support
* Clearer module boundaries
* Documentation alignment with evolving implementation

---

## Architectural Evolution

BijMantra combines:

* biological data systems
* AI-assisted workflows
* hybrid compute (Python, Rust/WASM, Fortran)

The architecture has evolved through multiple refactoring cycles driven by:

* scaling scientific complexity
* boundary definition requirements
* AI contract rigor
* hybrid execution constraints

Refactoring is treated as necessary system maturation.

---

## Quick Start

> Uses Podman (rootless, daemonless). Docker-compatible commands.

### Simple Setup

1. Install an AI-enabled IDE (VS Code, Kiro, Antigravity)
2. Open the repo and allow agent access
3. Use:

```text
Clone https://github.com/denishdholaria/bijmantra.git and start locally using Podman. Install dependencies and run backend + frontend.
```

4. Access:

* Frontend: http://localhost:5173
* API Docs: http://localhost:8000/docs

---

## Contributing

BijMantra welcomes contributors across engineering and agricultural science.

### Quick Wins

* Star the repo
* Report issues
* Fix documentation

### Developer Areas

* Frontend (React, TS)
* Backend (FastAPI, DB)
* Rust/WASM compute
* DevOps

### Scientists

Domain validation is critical—your input has high impact.

---

## Support and Collaboration

BijMantra is positioned as **research-grade agricultural infrastructure**.

Relevant collaborations include:

* institutional pilots
* interoperability work
* research validation
* licensing and deployment

See:

* FUNDING.md
* SPONSORS.md

---

## Working Principle

> **"Agricultural truth emerges at the intersection of disciplines. BijMantra makes that intersection computable."**

---

## Key Documents

* metrics.json
* CONTRIBUTING.md
* ETHICAL_USE_POLICY.md
* COMMERCIAL_LICENSE.md

---

## © Copyright and Branding

© 2026 BijMantra Project. All rights reserved.

BijMantra is released under the terms specified in the [LICENSE](LICENSE).
All code usage, modification, and redistribution must comply with that license.

**Name and Branding:**
"BijMantra" is the official project name and brand of the BijMantra Project.

* Use of the codebase is permitted under the license
* **Use of the name, branding, or identity in a way that implies official status, endorsement, or affiliation is not permitted without explicit authorization**

Third-party deployments or forks must clearly indicate their independent status and must not present themselves as the official BijMantra platform.

For official releases and project ownership, refer only to:

* https://bijmantra.org
* The official GitHub repository

---

<div align="center">

### Contact

📧 [hello@bijmantra.org](mailto:hello@bijmantra.org)
🌐 https://bijmantra.org

</div>
