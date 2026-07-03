# Breeding Domain

Breeding owns breeding, crosses, selection, and breeding-program creation workflows.

This package is a boundary scaffold. Existing runtime routes remain under `/api/v2` while behavior is migrated one vertical slice at a time.

Target structure:

```text
breeding/
  domain/        # pure breeding policies, entities, calculations
  application/   # breeding use cases and orchestration
  ports/         # service protocols and domain-owned interfaces
  schemas/       # commands, queries, DTOs, and event schemas
  adapters/      # API, persistence, workers, external clients
```

Current migration rule: do not add new breeding business logic to flat shared services when it can be owned here behind ports and schemas.
