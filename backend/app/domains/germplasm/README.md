# Germplasm Domain

Germplasm owns germplasm, accessions, seed bank, and seed-inventory workflows.

This package is a boundary scaffold. Existing runtime routes remain under `/api/v2` while behavior is migrated one vertical slice at a time.

Current transitional persistence bridge:

- `adapters/legacy_seed_bank.py` is the only Germplasm-domain bridge to the legacy Seed Bank accession ORM model. Capability adapters should depend on this bridge while the canonical Germplasm persistence model is migrated.

Target structure:

```text
germplasm/
  domain/        # pure seed and germplasm policies/entities
  application/   # germplasm and seed-bank use cases
  ports/         # service protocols and domain-owned interfaces
  schemas/       # commands, queries, DTOs, and event schemas
  adapters/      # API, persistence, workers, external clients
```

Current capability packs:

- `capabilities/accession_passport/`: active MCPD reference/import/export slice for accession identity, MCPD passport exchange, DTOs, code tables, CSV templates, import planning, import use-case execution, import/export repository ports, import persistence, export records, SQLAlchemy export/import adapters, export shaping, capability access enforcement, MCPD import/export audit events, legacy `/api/v2/passport/*` MCPD compatibility shaping, access enforcement, organization-scoped in-memory isolation, BrAPI germplasm DTO/envelope ownership, BrAPI germplasm response port records, BrAPI germplasm read/mutation access enforcement, standard and specialized BrAPI germplasm read/write repository ports, SQLAlchemy BrAPI germplasm read/write adapters, tenant-scoped BrAPI germplasm update/delete persistence, `/seed-bank/mcpd/*` route ownership, and `/brapi/v2/germplasm*` route ownership. Public MCPD routes are mounted through the canonical `/api/v2` apex router directly into this capability adapter; public BrAPI germplasm routes are mounted by the BrAPI v2 router through a compatibility shim at `backend/app/api/brapi/v2/germplasm.py`. The legacy Seed Bank router no longer imports or mounts MCPD routes. MCPD adapters use the Germplasm-domain legacy Seed Bank persistence bridge instead of importing `app.modules.seed_bank` directly. FAIR metadata links and seed-registry audit contracts remain transitional until migrated one vertical slice at a time.

Naming rule: `germplasm` is the canonical code key. Older forms such as `bijkosha`, `bija_kosha`, `bij_kosha`, or `bij-kosha` are legacy aliases only.
