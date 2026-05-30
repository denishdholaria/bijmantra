# Intelligence Domain

Intelligence owns AI, analytics, retrieval, knowledge graph, reasoning, decision support, and compute-orchestration product behavior.

This package is the canonical Intelligence ownership boundary. Existing `/api/v2` API contracts remain stable while Intelligence behavior is migrated one capability at a time.

## Canonical Shape

```text
intelligence/
  domain/        # shared pure domain vocabulary only
  application/   # shared orchestration only
  ports/         # shared protocols only
  schemas/       # shared commands, queries, DTOs, event schemas
  adapters/      # shared adapters only
  capabilities/
    <capability>/
      domain/
      application/
      ports/
      schemas/
      adapters/
```

Large feature families must live under `capabilities/<capability>/` so the Intelligence domain does not become a god bucket.

## Current Capability Packs

```text
capabilities/knowledge_graph/
  capability.yaml
  domain/knowledge_graph_retrieval.py
  application/knowledge_graph.py
  ports/knowledge_graph.py
  schemas/knowledge_graph.py
  adapters/knowledge_graph.py
  adapters/knowledge_graph_legacy.py
  adapters/knowledge_graph_persistence.py
```

Root-level Knowledge Graph files in `domain/`, `application/`, `ports/`, `schemas/`, and `adapters/` are temporary compatibility shims. New code must import from:

```text
app.domains.intelligence.capabilities.knowledge_graph
```

## Knowledge Graph Bridge

The public route surface remains stable:

```text
/api/v2/knowledge-graph/*
```

The route adapter now crosses the Intelligence capability boundary:

```text
api/bijmantra/data/knowledge_graph.py
  -> capabilities/knowledge_graph/schemas/knowledge_graph.py
  -> capabilities/knowledge_graph/application/knowledge_graph.py
  -> capabilities/knowledge_graph/adapters/knowledge_graph.py
  -> services/knowledge_graph_service.py   # transitional delegator
```

The transitional service keeps legacy callers working while SQLAlchemy queries, retrieval grouping, evidence search, and evidence-pack assembly drain into the capability pack.

## Ownership Rules

- Product Knowledge Graph behavior belongs to `intelligence/capabilities/knowledge_graph`, not the developer control plane.
- Pure scoring and readiness rules belong in capability `domain/`.
- Use cases and response assembly belong in capability `application/`.
- Protocols belong in capability `ports/`.
- Commands, queries, DTOs, and capability errors belong in capability `schemas/`.
- SQLAlchemy, legacy service bridges, workers, and external clients belong in capability `adapters/`.
- Public API paths stay stable unless a separate API compatibility decision is made.
