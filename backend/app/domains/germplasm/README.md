# Germplasm Domain

Germplasm owns germplasm, accessions, seed bank, and seed-inventory workflows.

This package is a boundary scaffold. Existing runtime routes remain under `/api/v2` while behavior is migrated one vertical slice at a time.

Target structure:

```text
germplasm/
  domain/        # pure seed and germplasm policies/entities
  application/   # germplasm and seed-bank use cases
  ports/         # service protocols and domain-owned interfaces
  schemas/       # commands, queries, DTOs, and event schemas
  adapters/      # API, persistence, workers, external clients
```

Naming rule: `germplasm` is the canonical code key. Older forms such as `bijkosha`, `bija_kosha`, `bij_kosha`, or `bij-kosha` are legacy aliases only.
