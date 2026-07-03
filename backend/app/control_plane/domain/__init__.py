"""Domain layer for the Control Plane Kernel — pure business logic.

This layer contains entities, value objects, and domain services that
encapsulate the core business rules of the developer control-plane.
All modules in this package are **infrastructure-free**: no database,
filesystem, or HTTP imports are permitted.

Modules
-------
board       : Board entity, lane containment, version management.
lane        : Lane entity, status, review gates, closure evidence.
mission     : Mission entity, verification runs, blocker tracking.
validation  : Pure validation functions (ASCII, queue shape, completion).
"""

__all__: list[str] = []
