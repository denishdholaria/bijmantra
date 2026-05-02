"""
Field Domain Router Aggregator
Consolidates all field-related endpoints
"""

from fastapi import APIRouter

from app.api.bijmantra.field import (
    crop_calendar,
    field_book,
    field_environment,
    field_layout,
    field_map,
    field_planning,
    field_scanner,
    harvest,
    nursery,
    nursery_management,
    plot_history,
    spatial,
    yield_map,
    field_boundary,
    uav_webhook,
)

field_router = APIRouter()

# Field operations
field_router.include_router(field_book.router, tags=["Field Book"])
field_router.include_router(field_environment.router, tags=["Field Environment"])
field_router.include_router(field_layout.router, tags=["Field Layout"])
field_router.include_router(field_map.router, tags=["Field Map"])
field_router.include_router(field_planning.router, tags=["Field Planning"])
field_router.include_router(field_scanner.router, tags=["Field Scanner"])
field_router.include_router(plot_history.router, tags=["Plot History"])

# Nursery management
field_router.include_router(nursery.router, tags=["Nursery Management"])
field_router.include_router(nursery_management.router, tags=["Nursery Management"])

# Harvest operations
field_router.include_router(harvest.router, tags=["Harvest Management"])

# Crop calendar
field_router.include_router(crop_calendar.router, tags=["Crop Calendar"])

# Spatial and yield mapping
field_router.include_router(spatial.router, tags=["Spatial Analysis"])
field_router.include_router(yield_map.router, tags=["Yield Map"])

# Field boundary extraction
field_router.include_router(field_boundary.router, tags=["Field Boundary"])

# UAV webhook
field_router.include_router(uav_webhook.router, tags=["UAV Webhook"])
