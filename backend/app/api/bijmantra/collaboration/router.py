"""
Collaboration domain router aggregator.

Composes all collaboration-related routers into a single mountable router.
"""

from fastapi import APIRouter

from app.api.bijmantra.collaboration import (
    activity,
    collaboration,
    collaboration_hub,
    forums,
    notifications,
    team_management,
    workflows,
)

collaboration_router = APIRouter()

# Include all collaboration domain routers
collaboration_router.include_router(collaboration.router, tags=["Collaboration"])
collaboration_router.include_router(collaboration_hub.router, tags=["Collaboration Hub"])
collaboration_router.include_router(forums.router, tags=["Forums"])
collaboration_router.include_router(team_management.router, tags=["Team Management"])
collaboration_router.include_router(activity.router, tags=["Activity"])
collaboration_router.include_router(notifications.router, tags=["Notifications"])
collaboration_router.include_router(workflows.router, tags=["Workflows"])
