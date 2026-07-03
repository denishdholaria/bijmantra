# Commercial Domain

Commercial owns commercial, inventory, and business workflow behavior.

This package is a boundary scaffold. Existing runtime routes remain under `/api/v2` while behavior is migrated one vertical slice at a time.

Target structure:

```text
commercial/
  domain/        # pure commercial policies and entities
  application/   # business workflow use cases and orchestration
  ports/         # service protocols and domain-owned interfaces
  schemas/       # commands, queries, DTOs, and event schemas
  adapters/      # API, persistence, workers, external clients
```

Current migration rule: commercial and inventory workflow decisions should move here, with seed-lot truth coordinated through Germplasm ports and schemas.
