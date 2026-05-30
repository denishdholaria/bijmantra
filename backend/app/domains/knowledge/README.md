# Knowledge Domain

Knowledge owns knowledge, training, documentation intelligence, and learning workflows when those surfaces become product behavior.

This package is a boundary scaffold. Existing runtime routes remain under `/api/v2` while behavior is migrated one vertical slice at a time.

Target structure:

```text
knowledge/
  domain/        # pure knowledge and learning policies/entities
  application/   # training and documentation-intelligence use cases
  ports/         # service protocols and domain-owned interfaces
  schemas/       # commands, queries, DTOs, and event schemas
  adapters/      # API, persistence, workers, external clients
```

Current migration rule: repository-process documentation remains in `.github/docs` and `.ai`; productized knowledge or training behavior belongs here.
