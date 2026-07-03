"""Orchestration layer for the Control Plane Kernel — multi-service coordination.

This layer contains orchestrators that coordinate multiple application
services for complex workflows.  Each orchestrator manages a bounded
workflow that may span several application-layer operations, ensuring
all side effects are committed or rolled back together.

Modules
-------
queue_materializer : Board → queue derivation, SHA256 computation.
dispatch_planner   : Queue loading, job selection, dispatch decisions.
closeout_writer    : Closeout receipt production, mission updates.
"""

__all__: list[str] = []
