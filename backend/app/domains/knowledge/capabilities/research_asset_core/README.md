# Federated ResearchAsset Core

**Status:** target extraction scaffold
**Authority:** `.ai/decisions/ADR-036-federated-research-asset-core-inside-modular-monolith.md`

This capability pack is the target home for the FAIR/federated asset spine.
It now owns pure policy rules, public Pydantic contracts, application facades,
planning helpers, FastAPI adapters, persistence ports, and SQLAlchemy adapters
while the current `app/schemas/*`, `app/services/*`, and legacy
`app/api/bijmantra/data/*` files remain stable compatibility shims for existing
imports and route aggregation.

Current compatibility surfaces:

- `backend/app/services/fair_metadata_service.py`
- `backend/app/services/federated_asset_registry_service.py`
- `backend/app/api/bijmantra/data/fair_metadata.py`
- `backend/app/api/bijmantra/data/federated_assets.py`

Migration rule: wrap, extract, and drain. Move pure validation, identifiers,
schemas, ports, application orchestration, and adapter seams here one slice at
a time while keeping `/api/v2/fair-metadata/*` and
`/api/v2/federated-assets/*` stable.
