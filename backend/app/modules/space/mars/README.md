# MARS Module — Extreme Environment Agriculture Engine

**Status:** Phase 1 (Python Orchestration)

## Purpose
The MARS module evaluates plant germplasm performance under extreme, synthetic, closed-loop environments.

## Architecture
- **Orchestration**: Python (FastAPI + SQLAlchemy)
- **Compute**: Deterministic Python heuristics (Phase 1)
- **Data Model**: Postgres (UUIDs, JSON profiles)

## Files
- `router.py`: FastAPI endpoints.
- `service.py`: Business logic and orchestration.
- `optimizer.py`: Mathematical simulation (deterministic).
- `schemas.py`: Pydantic models.
