"""Canonical re-export of the developer control-plane router.

This module provides the canonical import path for the composed router:

    from app.control_plane.api.developer_control_plane_router import router

The router is defined and composed (with ``include_router`` calls for lanes,
missions, telemetry, and verification sub-routers) in
``app.api.bijmantra.developer_control_plane``.  This thin re-export avoids
duplicating the composition logic while establishing the layered API package
as the long-term canonical location.

Route handlers delegate to the application and orchestration layers — each
handler in the thin sub-routers is kept under 20 lines.
"""

from app.api.bijmantra.developer.developer_control_plane import router

__all__ = ["router"]
