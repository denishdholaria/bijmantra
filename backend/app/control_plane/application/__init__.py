"""Application layer for the Control Plane Kernel — use case orchestration.

This layer contains application services that orchestrate domain logic
with infrastructure dependencies (database sessions, filesystem access)
injected via constructor parameters.  Each service coordinates a bounded
set of use cases and returns response models suitable for HTTP
serialization.

Modules
-------
board_service      : Board CRUD with database persistence.
lane_service       : Lane completion workflow, approval receipts.
mission_service    : Mission state queries, bootstrap from closeout.
execution_service  : Queue job execution tracking, closeout production.
"""

__all__: list[str] = []
