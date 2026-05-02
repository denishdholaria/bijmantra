"""Contracts layer — stable API schemas and internal event payloads.

Models in this package define:

* **api_schema** — the HTTP request/response contract that the
  BeingBijMantra VS Code extension (autonomy bridge) depends on.
  Changes to these schemas require explicit versioning and consumer
  coordination.

* **event_schema** — internal pub/sub event payloads used for
  coordination between control-plane layers.  These are NOT part of
  the external API contract.
"""
