# BijMantra Project Memory

This document contains my synthesized understanding of the BijMantra project. I will use it as a guide for all future work in this repository to ensure my contributions align with the project's goals, standards, and conventions.

## 1. Core Mission & Vision

- **Primary Goal:** To create a cross-domain agricultural intelligence platform that unifies fragmented agricultural knowledge.
- **Vision:** To transform how agricultural research is conducted globally by enabling AI-assisted reasoning *across* scientific domains, not just within them. The key is to make the intersection of disciplines computable.
- **Core Philosophy:** "Cross-Domain by Default." Contributions must be designed for integration and interaction with other modules. Isolated, single-domain features are considered incomplete.

## 2. Current Project Status

- **Version:** `preview-1` ("Prathama"). This is an early-access version for evaluation.
- **Immediate Priority:** The highest priority is eliminating demo data. According to `metrics.json` and `README.md`, 37 pages are still using demo data, and the core task is to connect them to the real backend and database.
- **CALF Assessment:** The project uses a "Computational Analysis and Functionality Level" (CALF) system to track page status. The focus is on moving pages from CALF-2 (Demo Data) to CALF-3 (Real Computation).

## 3. Technical Stack & Architecture

- **Containerization:** The project uses **Podman** instead of Docker for its rootless, daemonless architecture. All `docker` commands should be replaced with `podman`.
- **Backend:** Python 3.13 with FastAPI, SQLAlchemy 2.0, and Pydantic 2. It follows a modular architecture.
- **Frontend:** React 18 with TypeScript 5, Vite, and Tailwind CSS.
- **Database:** PostgreSQL 17 with PostGIS and pgvector.
- **High-Performance Compute:** Fortran and Rust/WASM are used for numerically intensive tasks like genomic calculations, which can run in the browser.
- **Governance:** The project is governed by a strict "Platform Law Stack" of 14 documents. `ARCHITECTURE.md` is the source of truth over the `README.md`.

## 4. Development Workflow & Standards

- **Getting Started:**
  - `git clone ...`
  - `make dev` (starts infrastructure)
  - `make dev-backend` (runs backend on `localhost:8000`)
  - `make dev-frontend` (runs frontend on `localhost:5173`)
- **Testing:**
  - `make test` runs the entire test suite.
  - Backend: `cd backend && pytest`
  - Frontend: `cd frontend && npm run test`
- **Linting:**
  - `make lint`
- **Branching:**
  - `feature/description`
  - `bugfix/description`
  - `docs/description`
- **Commits:** Conventional Commits standard is required (e.g., `feat:`, `fix:`, `docs:`).
- **Core Principle:** Contributions must be research-grade, scientifically interpretable, and expose uncertainty. Black-box logic is not acceptable. PRs that introduce mock data will be rejected.

## 5. My Role (Jules)

- My primary task is to assist in completing pending development tasks, with a focus on addressing the demo data violations identified in the CALF assessment.
- I must adhere to the cross-domain philosophy in all my work.
- I will follow the established development workflow, including using Podman, running tests, and formatting my commits correctly.
- I will consult this memory file at the beginning of each session to ensure my work remains aligned with the project's high standards.
