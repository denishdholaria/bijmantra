"""
Field Planning API Router
Field and season planning endpoints
"""
from fastapi import APIRouter, Query
from typing import Optional

from app.services.field_planning import field_planning_service

router = APIRouter(prefix="/field-planning", tags=["Field Planning"])


@router.get("/plans")
async def get_field_plans(
    field_id: Optional[str] = Query(None),
    season: Optional[str] = Query(None),
    status: Optional[str] = Query(None)
):
    """Get field plans"""
    return await field_planning_service.get_field_plans(field_id, season, status)


@router.get("/plans/{plan_id}")
async def get_field_plan(plan_id: str):
    """Get single field plan"""
    return await field_planning_service.get_field_plan(plan_id)


@router.get("/seasons")
async def get_season_plans(
    year: Optional[int] = Query(None),
    season_type: Optional[str] = Query(None),
    status: Optional[str] = Query(None)
):
    """Get season plans"""
    return await field_planning_service.get_season_plans(year, season_type, status)


@router.get("/seasons/{plan_id}")
async def get_season_plan(plan_id: str):
    """Get single season plan"""
    return await field_planning_service.get_season_plan(plan_id)


@router.get("/resources/{plan_id}")
async def get_resource_allocation(plan_id: str):
    """Get resource allocation for a plan"""
    return await field_planning_service.get_resource_allocation(plan_id)


@router.get("/calendar")
async def get_calendar(
    year: int = Query(...),
    month: Optional[int] = Query(None)
):
    """Get planning calendar"""
    return await field_planning_service.get_calendar(year, month)


@router.get("/statistics")
async def get_statistics():
    """Get planning statistics"""
    return await field_planning_service.get_statistics()
