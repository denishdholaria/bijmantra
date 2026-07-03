"""Control Plane API layer — thin routers for the developer control-plane.

This package provides the canonical import path for the developer control-plane
router.  The actual route handlers live in the thin router modules under
``app.api.bijmantra.control_plane`` (lanes, missions, telemetry, verification), and
the router composition (``include_router`` calls) remains in
``app.api.bijmantra.developer_control_plane`` which is the entry point that FastAPI
uses via ``apex_router``.
"""
