# BijMantra Data Pipeline

## Overview

This repo-root pipeline discovers the BijMantra SQLAlchemy schema, maps each agricultural domain to public data sources, composes source-attributed crop intelligence, synthesizes missing measurements and relationships, validates output, and feeds backend seeders.

The first implementation is intentionally hybrid: it is ready to fetch public source metadata, but it can also produce deterministic seedable data without network access so local REEVU and demo workflows are not blocked.

## Usage

From the backend environment, run the repo-root package with:

```bash
cd backend
PYTHONPATH=.. uv run python -m data_pipeline run
```

Individual phases:

```bash
PYTHONPATH=.. uv run python -m data_pipeline discover
PYTHONPATH=.. uv run python -m data_pipeline fetch
PYTHONPATH=.. uv run python -m data_pipeline transform
PYTHONPATH=.. uv run python -m data_pipeline synthesize
PYTHONPATH=.. uv run python -m data_pipeline compose
PYTHONPATH=.. uv run python -m data_pipeline validate
```

Fetch controls:

```bash
PYTHONPATH=.. uv run python -m data_pipeline run --no-fetch
PYTHONPATH=.. uv run python -m data_pipeline fetch --force-fetch
PYTHONPATH=.. uv run python -m data_pipeline fetch --source gbif_taxonomy --source faostat
```

The root `.venv` is currently Python 3.15 alpha and does not carry backend HTTP/scientific dependencies. The backend `uv` environment is the supported execution environment for now.

## Outputs

- `schema_map.json` — discovered table, column, FK, enum, required-field, and domain map.
- `data_sources.json` — public source registry.
- `raw/` — raw fetch responses and errors.
- `transformed/` — crop intelligence records from repo crop lists plus public source attribution.
- `synthetic/` — deterministic synthetic observation payloads.
- `output/` — seedable JSON consumed by `backend/app/db/seeders/pipeline_*.py`.
- `validation_report.json` — schema, FK, and agronomic rule validation results.

## Data Sources

Current registry includes GENESYS PGR, USDA GRIN-Global, GBIF, Crop Ontology, BrAPI test server, CGIAR Dataverse/CIMMYT, FAOSTAT, NASA POWER, ISRIC SoilGrids, Ensembl Plants, NCBI Datasets, Gramene, QTARO, SoyBase, World Bank commodity data, Agmarknet, and cited knowledge resources.

## Synthetic Data

Synthetic records are explicitly marked with:

- `data_source`
- `synthetic_method`
- `pipeline_version`
- `generated_at`

Trait synthesis uses deterministic, crop-category-aware distributions across the 16 crop categories in the catalog. FAOSTAT yield baselines are used when cached raw data is present; otherwise the synthesizer falls back to bounded agronomic defaults. It is designed to fill sparse demo and benchmark tenants, not to masquerade as observed field data.

## Seeder Integration

Generate and validate output first:

```bash
cd backend
PYTHONPATH=.. uv run python -m data_pipeline run
```

Then run seeders in dependency order:

```bash
PYTHONPATH=.. uv run python -m app.db.seed --only=pipeline_trials --scope=system
PYTHONPATH=.. uv run python -m app.db.seed --only=pipeline_germplasm --scope=system
PYTHONPATH=.. uv run python -m app.db.seed --only=pipeline_phenotyping --scope=system
PYTHONPATH=.. uv run python -m app.db.seed --only=pipeline_observations --scope=system
PYTHONPATH=.. uv run python -m app.db.seed --only=pipeline_genotyping --scope=system
PYTHONPATH=.. uv run python -m app.db.seed --only=pipeline_gwas --scope=system
PYTHONPATH=.. uv run python -m app.db.seed --only=pipeline_qtls --scope=system
```

All seeders are non-production only, idempotent, and tenant-scoped.

## Known Limits

- Real-source downloads are intentionally conservative and metadata-first in this slice.
- Large bulk datasets should move through the existing analytical export lane before being treated as supported operational imports.
- The pipeline improves org 1 data readiness; it does not change REEVU trusted-surface classifications.
