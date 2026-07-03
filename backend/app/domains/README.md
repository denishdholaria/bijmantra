# Backend Domains

This directory is the canonical business ownership surface for BijMantra's modular monolith.

Backend code uses industry-standard domain names. Older BijMantra documents may call these boundaries LOKAs or use Sanskrit labels; those names are legacy aliases only.

## Scale Rule

The domain folders are not meant to become large feature buckets. Use this hierarchy for new or migrated product behavior:

```text
domain
  -> capability
    -> hexagonal slice
```

Target shape for sizeable feature families:

```text
backend/app/domains/<domain>/
  domain/          # small shared vocabulary and policies
  application/     # small shared orchestration only
  ports/           # shared domain ports
  schemas/         # shared domain DTOs/events
  adapters/        # shared domain adapters
  capabilities/
    <capability>/
      capability.yaml
      domain/
      application/
      ports/
      schemas/
      adapters/
```

The current root layers remain valid and are required by existing architecture guards. Keep them small. If a workflow is more than a small shared policy, put it under a named capability.

Every sizeable capability pack must carry `capability.yaml`; the platform registry and tests use that manifest to connect code ownership, dominion/app ownership, routes, permissions, data scopes, standards, audit events, and install/uninstall behavior.

Current materialized capability packs:

- `intelligence/capabilities/knowledge_graph`: first Knowledge Graph capability pack; public `/api/v2/knowledge-graph/*` routes remain stable while implementation lives behind capability-owned schemas, ports, use cases, domain policy, and adapters.

## Canonical Domains

- `breeding`: breeding and creation workflows
- `germplasm`: germplasm, accessions, seed bank, and seed operations
- `phenotyping`: traits, phenotyping, morphology, and observations
- `field_operations`: field, trials, operations, environment, and agronomy execution
- `intelligence`: intelligence, analytics, AI, knowledge graph, and compute orchestration
- `commercial`: commercial, inventory, warehouse, and business workflows
- `knowledge`: knowledge, training, documentation intelligence, and learning

See `.github/docs/architecture/2026-05-26-capability-inventory-and-domain-scaling-map.md` before adding a new capability.

Legacy alias map:

- `sristi` -> `breeding`
- `bijkosha`, `bija_kosha`, `bij_kosha`, `bija-kosha`, `bij-kosha` -> `germplasm`
- `rupa` -> `phenotyping`
- `kshetra` -> `field_operations`
- `medha` -> `intelligence`
- `vani` -> `commercial`
- `vidya` -> `knowledge`
