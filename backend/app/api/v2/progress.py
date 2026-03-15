"""
Progress Tracker API

Endpoints for tracking development progress across the platform.
"""


from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.modules.core.services.progress_tracker_service import progress_service


router = APIRouter(prefix="/progress", tags=["Progress Tracker"])


# ============ Request Schemas ============

class AddFeatureRequest(BaseModel):
    name: str = Field(..., description="Feature name")
    description: str = Field(..., description="Feature description")
    status: str = Field("planned", description="Status: completed, in-progress, planned, backlog")
    tags: list[str] = Field(default=[], description="Tags for categorization")
    endpoints: int = Field(0, description="Number of API endpoints")
    priority: str = Field("medium", description="Priority: high, medium, low")


class UpdateFeatureRequest(BaseModel):
    status: str = Field(..., description="New status")


class UpdateDivisionRequest(BaseModel):
    progress: int = Field(..., ge=0, le=100, description="Progress percentage")
    endpoints: int | None = Field(None, description="Number of endpoints")


class UpdateSummaryRequest(BaseModel):
    endpoints: int | None = Field(None, description="Total API endpoints")
    pages: int | None = Field(None, description="Total frontend pages")


# ============ Endpoints ============

@router.get("")
async def get_all_progress():
    """
    Get complete progress data including summary, divisions, features, and roadmap.

    This endpoint provides all data needed for the Progress Tracker dashboard.
    """
    return await progress_service.get_all_data()


@router.get("/summary")
async def get_progress_summary():
    """Get progress summary statistics"""
    return await progress_service.get_summary()


@router.get("/divisions")
async def get_divisions():
    """Get all divisions with their progress"""
    divisions = await progress_service.get_divisions()
    return {
        "divisions": divisions,
        "total": len(divisions),
    }


@router.get("/divisions/{division_id}")
async def get_division(division_id: str):
    """Get a specific division's progress"""
    division = await progress_service.get_division(division_id)
    if not division:
        raise HTTPException(status_code=404, detail="Division not found")
    return division


@router.patch("/divisions/{division_id}")
async def update_division(division_id: str, request: UpdateDivisionRequest):
    """Update a division's progress"""
    division = await progress_service.update_division_progress(
        division_id=division_id,
        progress=request.progress,
        endpoints=request.endpoints,
    )
    if not division:
        raise HTTPException(status_code=404, detail="Division not found")
    return {"message": "Division updated", "division": division}


@router.get("/features")
async def get_features(
    status: str | None = Query(None, description="Filter by status"),
    limit: int = Query(20, ge=1, le=100, description="Maximum items to return"),
):
    """Get recent features with optional status filter"""
    features = await progress_service.get_recent_features(limit=limit, status=status)
    return {
        "features": features,
        "total": len(features),
    }


@router.post("/features")
async def add_feature(request: AddFeatureRequest):
    """Add a new feature to tracking"""
    feature = await progress_service.add_feature(
        name=request.name,
        description=request.description,
        status=request.status,
        tags=request.tags,
        endpoints=request.endpoints,
        priority=request.priority,
    )
    return {"message": "Feature added", "feature": feature}


@router.patch("/features/{feature_id}")
async def update_feature(feature_id: str, request: UpdateFeatureRequest):
    """Update a feature's status"""
    feature = await progress_service.update_feature_status(feature_id, request.status)
    if not feature:
        raise HTTPException(status_code=404, detail="Feature not found")
    return {"message": "Feature updated", "feature": feature}


@router.get("/roadmap")
async def get_roadmap():
    """Get development roadmap by quarter"""
    return {
        "roadmap": await progress_service.get_roadmap(),
    }


@router.get("/api-stats")
async def get_api_stats():
    """Get API endpoint statistics"""
    return await progress_service.get_api_stats()


@router.get("/tech-stack")
async def get_tech_stack():
    """Get technology stack information"""
    return await progress_service.get_tech_stack()


@router.patch("/summary")
async def update_summary(request: UpdateSummaryRequest):
    """Update summary statistics"""
    summary = await progress_service.update_summary(
        endpoints=request.endpoints,
        pages=request.pages,
    )
    return {"message": "Summary updated", "summary": summary}
