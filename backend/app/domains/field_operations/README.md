# Field Operations Domain

Field Operations owns field, trials, operations, agronomy execution, and irrigation workflows.

This package is a boundary scaffold. Existing runtime routes remain under `/api/v2` while behavior is migrated one vertical slice at a time.

Target structure:

```text
field_operations/
  domain/        # pure field/trial/operation policies and entities
  application/   # field execution use cases and orchestration
  ports/         # service protocols and domain-owned interfaces
  schemas/       # commands, queries, DTOs, and event schemas
  adapters/      # API, persistence, workers, external clients
```

Current capability packs:

- `capabilities/trial_analysis/`: scaffolded landing zone for BrAPI/MIAPPE trial analysis, field study context, phenotyping inputs, and analysis audit events. Existing runtime routes remain in legacy/API surfaces until a vertical slice is migrated.

Current migration rule: trial and field execution workflows belong here unless they are pure breeding strategy owned by Breeding.
