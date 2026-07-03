<div align="center">

<img src="frontend/public/icons/icon-512x512.png" alt="BijMantra Logo" width="180"/>

# BijMantra

## (Under Development)

### Cross-domain agricultural intelligence platform for breeding, seed, research, and institutional workflows

</div>

---

## **Status as of <!-- METRIC:LAST_UPDATED -->2026-07-03<!-- /METRIC -->:**

* In the past eight weeks, the architectural challenges remains; However, development has very slowly advancing through focused backend hardening, capability-driven platform work, and documentation/architecture cleanup.

* Security improvements include tenant-isolated RLS, socket and API tenant guards, Keycloak SSO/realm contract work, and dependency patches to remediate high-risk CVEs.

* The WASM compute engine and Plant Vision ML pipeline were hardened, with better dataset enforcement, runtime fallback handling, and operational safeguards.

* Knowledge graph, FAIR metadata, and federated research asset capabilities received significant additions, while the capability access model and platform installation guards were refined for domain-aware access control.

* Germplasm and BrAPI work progressed toward a tighter Accession Passport capability, with BrAPI extraction, adapter consolidation, modular tests, and stronger domain gate enforcement.

* Rust API preview also made forward progress, with BrAPI read surface parity advances, route status alignment, milestone tracking, and seedlot inventory readiness support under active development.

* The project remains under active refactor and validation. The application still starts locally, but stabilization and careful capability hardening continue before broader production readiness.

🌐 **[bijmantra.org](https://bijmantra.org)**

---

## ⚠️ Important Notice — Official BijMantra Domain

**The official project is only available at:** https://bijmantra.org and the [official GitHub repository](https://github.com/denishdholaria/bijmantra.git).

---

## Licensing and Collaboration Policy

* Organizations are welcome to enter into legal licensing agreements with BijMantra. We remain open to collaboration and negotiation where appropriate.

* BijMantra does not grant rights to represent deployments as the official BijMantra project, nor to use the BijMantra name, logo, or branding in ways that may cause confusion regarding origin or affiliation.

### For security and clarity:

* Do not share data, credentials, or make payments on third-party deployments claiming association with BijMantra.

* Any authorized use must be clearly distinguished from the official BijMantra initiative.

---

[![Stars](https://img.shields.io/github/stars/denishdholaria/bijmantra?style=for-the-badge\&logo=github\&color=gold)](https://github.com/denishdholaria/bijmantra)

[**Get Started**](#quick-start) · [**Current Reality**](#current-reality) · [**Contributing**](#contributing) · [**Docs**](#key-documents)

---

# What BijMantra Is

BijMantra is a server-backed agricultural intelligence platform designed for:

* breeding programs
* seed organizations
* research institutions
* agricultural administrators

It connects workflows traditionally fragmented across separate systems:

* plant breeding
* germplasm management
* seed operations
* environmental context
* research knowledge
* institutional administration

The goal is not to create another generic dashboard layer, but to reduce fragmentation by keeping genetic, operational, environmental, and institutional context interconnected.

At a broader level, BijMantra is being shaped as an advanced agricultural extension and intelligence system — bridging scientific discovery, institutional validation, operational coordination, and field adoption.

---

# Why Institutions Care

Agricultural decisions rarely exist in isolation.

Breeding strategy, field trials, seed operations, environmental variability, reporting systems, and institutional coordination often operate across disconnected infrastructure stacks.

BijMantra is being built for organizations that require:

* integrated breeding and genomics workflows
* seed system coordination
* cross-department research linkage
* interoperable institutional infrastructure
* long-term scientific traceability

The core thesis:

> **Decisions improve when context is unified instead of manually reconciled.**

---

# Why This Is Hard

BijMantra exists at the intersection of:

* breeding systems
* seed systems
* field operations
* environmental intelligence
* AI-assisted workflows
* scientific infrastructure

The platform must also operate under constraints unique to agriculture:

* long validation cycles (5–15 years)
* inconsistent institutional infrastructure
* fragmented data quality
* provenance and evidence requirements
* hybrid compute complexity
* uncertainty modeling

The challenge is not simply building software — it is building systems capable of carrying trusted agricultural insight across domains, organizations, and time horizons.

---

# Current Scope

BijMantra remains in preview and active architectural evolution.

The repository spans multiple scientific and engineering domains but does not yet reflect uniform maturity across all modules. Some areas are functional, others are being hardened, and some remain structural placeholders pending future implementation.

---

# What Is Still In Progress

* Cross-module validation and consistency
* Provenance and evidence integrity
* Low-connectivity workflows
* AI workflow stabilization
* Documentation synchronization
* Institutional interoperability
* Scientific validation pipelines
* Clearer module boundaries

---

# Architectural Evolution

BijMantra combines:

* biological data systems
* AI-assisted workflows
* hybrid compute infrastructure
* Python, Rust/WASM, and Fortran execution paths

The architecture has evolved through multiple large-scale refactoring cycles driven by:

* scaling scientific complexity
* domain boundary refinement
* AI contract rigor
* hybrid execution constraints
* long-term maintainability concerns

Refactoring is treated as necessary system maturation rather than instability.

---

# Quick Start

> Uses Podman (rootless, daemonless). Docker-compatible commands are supported.

## Simple Setup

1. Install an AI-enabled IDE (VS Code, Kiro, Antigravity, etc.)
2. Open the repository and allow agent access
3. Use:

```text
Clone https://github.com/denishdholaria/bijmantra.git and start locally using Podman. Install dependencies and run backend + frontend.
```

4. Access:

* Frontend: http://localhost:5656
* API Docs: http://localhost:8000/docs

---

# NVIDIA NIM Setup

BijMantra ships with NVIDIA NIM support as an additional AI provider for REEVU.
NIM exposes an OpenAI-compatible endpoint so no extra SDK is needed.
**The NVIDIA API key is only read server-side and is never exposed to the browser.**

## 1. Get an API key

Sign up at [build.nvidia.com](https://build.nvidia.com) and create an API key
(format: `nvapi-…`). Free tier credits are available for most models.

## 2. Configure environment variables

Add these to your `.env` (copy from `.env.example`):

```bash
# Required
NVIDIA_API_KEY=nvapi-<your-key-here>

# Optional overrides (defaults are shown)
NIM_MODEL=meta/llama-3.1-70b-instruct
NIM_BASE_URL=https://integrate.api.nvidia.com/v1
```

Browse available models at [build.nvidia.com/explore/discover](https://build.nvidia.com/explore/discover).

## 3. Start the dev stack

```bash
bash bijdev.sh
```

The backend reads `NVIDIA_API_KEY` on startup and registers the `nvidia_nim`
provider in the REEVU routing table. If the key is present, REEVU will include
NIM in its automatic fallback chain (after Groq and Google, before HuggingFace).

## 4. Run smoke tests

**Python (standalone, no backend needed):**

```bash
uv run python -m scripts.nim_smoke_test
```

**Rust (requires the backend running on port 8000):**

```bash
cd rust
cargo build --features native-http --bin nim_smoke_test
BIJMANTRA_NIM_PROXY_URL=http://localhost:8000/api/v2/nim/chat \
  cargo run --features native-http --bin nim_smoke_test
```

## 5. Frontend usage

The frontend `services/nimApi.ts` module calls the backend proxy — never NIM directly:

```typescript
import { nimChat, nimStream } from '@/services/nimApi'

// Non-streaming
const result = await nimChat({
  messages: [{ role: 'user', content: 'What is genomic selection?' }],
})
console.log(result.content)

// Streaming
for await (const chunk of nimStream({
  messages: [{ role: 'user', content: 'What is genomic selection?' }],
})) {
  process.stdout.write(chunk)
}
```

## Security notes

- `NVIDIA_API_KEY` is loaded via `pydantic-settings` on the backend only.
- The pre-commit hook (`.git-hooks/pre-commit`) blocks commits that contain
  a staged `.env` file or a hardcoded `nvapi-…` string.
- Install the hooks with: `bash scripts/setup_git_hooks.sh`

---

# Contributing

BijMantra welcomes contributors across both engineering and agricultural science disciplines.

## Quick Wins

* Star the repository
* Report issues
* Improve documentation
* Submit bug fixes

## Engineering Areas

* Frontend (React, TypeScript)
* Backend (FastAPI, databases)
* Rust/WASM compute
* DevOps and infrastructure
* AI workflow systems
* Testing and validation

## Scientific and Domain Areas

Domain validation is critically important.

Contributions from breeders, agronomists, seed specialists, crop scientists, geneticists, and agricultural researchers can have extremely high impact on the long-term scientific quality of the platform.

---

# Support and Collaboration

BijMantra is positioned as research-grade agricultural intelligence infrastructure.

Relevant collaboration areas include:

* institutional pilots
* interoperability partnerships
* research validation
* deployment collaborations
* infrastructure sponsorship
* scientific partnerships

See:

* FUNDING.md
* SPONSORS.md

---

# Working Principle

> **"Agricultural truth emerges at the intersection of disciplines. BijMantra makes that intersection computable."**

---

# Key Documents

* metrics.json
* CONTRIBUTING.md
* ETHICAL_USE_POLICY.md
* COMMERCIAL_LICENSE.md

---

# © Copyright and Branding

© 2026 BijMantra Project. All rights reserved.

BijMantra is released under the terms specified in the [LICENSE](LICENSE).

All code usage, modification, and redistribution must comply with that license.

## Name and Branding

"BijMantra" is the official project name and brand of the BijMantra Project.

* Use of the codebase is permitted under the project license.
* Use of the name, branding, or identity in ways implying official status, endorsement, or affiliation is prohibited without explicit authorization.

Third-party deployments or forks must clearly indicate their independent status and must not present themselves as the official BijMantra platform.

Official project references:

* https://bijmantra.org
* https://github.com/denishdholaria/bijmantra

---

<div align="center">

## Contact

📧 [hello@bijmantra.org](mailto:hello@bijmantra.org)
🌐 https://bijmantra.org

</div>
