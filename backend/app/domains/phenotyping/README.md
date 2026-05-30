# Phenotyping Domain

Phenotyping owns phenotyping, morphology, observations, and form/trait-analysis workflows.

This package is a boundary scaffold. Existing runtime routes remain under `/api/v2` while behavior is migrated one vertical slice at a time.

Target structure:

```text
phenotyping/
  domain/        # pure trait, observation, and morphology logic
  application/   # phenotyping use cases and orchestration
  ports/         # service protocols and domain-owned interfaces
  schemas/       # commands, queries, DTOs, and event schemas
  adapters/      # API, persistence, workers, external clients
```

Current migration rule: phenotyping decisions and validation rules should move toward Phenotyping domain/application layers instead of route-local logic.
