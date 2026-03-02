"""
Field Boundary Extraction API Router

Exposes GEE-based field boundary extraction service.
"""

from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.services.infra.gee_field_boundary_extractor import (
    GEEFieldBoundaryExtractor,
    get_boundary_extractor,
)

router = APIRouter(prefix="/field-boundary", tags=["field-boundary"])


class BoundaryRequest(BaseModel):
    """Request schema for field boundary extraction."""

    latitude: float = Field(..., ge=-90, le=90, description="Center latitude")
    longitude: float = Field(..., ge=-180, le=180, description="Center longitude")
    date: datetime = Field(..., description="Target date for imagery")
    buffer_meters: int = Field(
        1000, ge=100, le=5000, description="Search radius in meters"
    )


@router.post("/extract", response_model=dict[str, Any])
async def extract_field_boundaries(
    request: BoundaryRequest,
    extractor: GEEFieldBoundaryExtractor = Depends(get_boundary_extractor),
) -> dict[str, Any]:
    """
    Extract field boundaries from satellite imagery.

    Uses Google Earth Engine SNIC segmentation to identify potential
    field boundaries within the specified buffer radius.
    """
    result = await extractor.extract_boundaries(
        request.latitude,
        request.longitude,
        request.date,
        request.buffer_meters,
    )

    if result is None:
        raise HTTPException(
            status_code=500,
            detail="Failed to extract boundaries. Check GEE credentials or try another date/location.",
        )

    return result
