"""
BrAPI Core - Seasons endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional
import uuid

from app.core.database import get_db
from app.api.deps import get_organization_id
from app.schemas.brapi import BrAPIResponse, Metadata, Pagination, Status
from app.core.config import settings
from pydantic import BaseModel, Field
from typing import Dict, Any, List

router = APIRouter()


# ============= Schemas =============

class SeasonBase(BaseModel):
    """Base season schema"""
    season_name: str = Field(..., alias="seasonName")
    year: Optional[int] = None
    additional_info: Optional[Dict[str, Any]] = Field(None, alias="additionalInfo")
    
    class Config:
        populate_by_name = True


class SeasonCreate(SeasonBase):
    """Schema for creating season"""
    pass


class SeasonUpdate(BaseModel):
    """Schema for updating season"""
    season_name: Optional[str] = Field(None, alias="seasonName")
    year: Optional[int] = None
    additional_info: Optional[Dict[str, Any]] = Field(None, alias="additionalInfo")
    
    class Config:
        populate_by_name = True


class Season(SeasonBase):
    """Season response schema (BrAPI compliant)"""
    season_db_id: str = Field(..., alias="seasonDbId")
    
    class Config:
        from_attributes = True
        populate_by_name = True


# ============= In-Memory Storage (Demo) =============
# In production, this would be a database table

_seasons_store: Dict[str, Dict[str, Any]] = {}


def _init_demo_seasons():
    """Initialize demo seasons if empty"""
    if not _seasons_store:
        demo_seasons = [
            {"seasonDbId": "season_spring2024", "seasonName": "Spring 2024", "year": 2024},
            {"seasonDbId": "season_summer2024", "seasonName": "Summer 2024", "year": 2024},
            {"seasonDbId": "season_fall2024", "seasonName": "Fall 2024", "year": 2024},
            {"seasonDbId": "season_winter2024", "seasonName": "Winter 2024", "year": 2024},
            {"seasonDbId": "season_kharif2024", "seasonName": "Kharif 2024", "year": 2024},
            {"seasonDbId": "season_rabi2024", "seasonName": "Rabi 2024-25", "year": 2024},
            {"seasonDbId": "season_spring2025", "seasonName": "Spring 2025", "year": 2025},
            {"seasonDbId": "season_wet2025", "seasonName": "Wet Season 2025", "year": 2025},
            {"seasonDbId": "season_dry2025", "seasonName": "Dry Season 2025", "year": 2025},
        ]
        for s in demo_seasons:
            _seasons_store[s["seasonDbId"]] = s


def create_brapi_response(data: any, page: int, page_size: int, total_count: int):
    """Helper to create BrAPI response with metadata"""
    total_pages = max(1, (total_count + page_size - 1) // page_size)
    
    metadata = Metadata(
        pagination=Pagination(
            current_page=page,
            page_size=page_size,
            total_count=total_count,
            total_pages=total_pages
        ),
        status=[Status(message="Success", message_type="INFO")]
    )
    
    return BrAPIResponse(metadata=metadata, result={"data": data})


# ============= Endpoints =============

@router.get("/seasons", response_model=BrAPIResponse[dict])
async def list_seasons(
    page: int = Query(0, ge=0),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE),
    year: Optional[int] = Query(None),
    season_db_id: Optional[str] = Query(None, alias="seasonDbId"),
    db: AsyncSession = Depends(get_db),
    org_id: int = Depends(get_organization_id)
):
    """List seasons with pagination (BrAPI v2.1)"""
    _init_demo_seasons()
    
    # Filter seasons
    seasons = list(_seasons_store.values())
    
    if year:
        seasons = [s for s in seasons if s.get("year") == year]
    
    if season_db_id:
        seasons = [s for s in seasons if s.get("seasonDbId") == season_db_id]
    
    # Sort by year descending, then name
    seasons.sort(key=lambda x: (-x.get("year", 0), x.get("seasonName", "")))
    
    total_count = len(seasons)
    skip = page * page_size
    seasons_page = seasons[skip:skip + page_size]
    
    return create_brapi_response(seasons_page, page, page_size, total_count)


@router.get("/seasons/{seasonDbId}", response_model=BrAPIResponse[dict])
async def get_season(
    seasonDbId: str,
    db: AsyncSession = Depends(get_db),
    org_id: int = Depends(get_organization_id)
):
    """Get a single season by DbId (BrAPI v2.1)"""
    _init_demo_seasons()
    
    season = _seasons_store.get(seasonDbId)
    
    if not season:
        raise HTTPException(status_code=404, detail="Season not found")
    
    metadata = Metadata(
        pagination=Pagination(current_page=0, page_size=1, total_count=1, total_pages=1),
        status=[Status(message="Success", message_type="INFO")]
    )
    
    return BrAPIResponse(metadata=metadata, result=season)


@router.post("/seasons", response_model=BrAPIResponse[dict], status_code=201)
async def create_season(
    season_in: SeasonCreate,
    db: AsyncSession = Depends(get_db),
    org_id: int = Depends(get_organization_id)
):
    """Create a new season (BrAPI v2.1)"""
    _init_demo_seasons()
    
    # Generate unique season_db_id
    season_db_id = f"season_{uuid.uuid4().hex[:12]}"
    
    season_data = {
        "seasonDbId": season_db_id,
        "seasonName": season_in.season_name,
        "year": season_in.year,
    }
    
    if season_in.additional_info:
        season_data["additionalInfo"] = season_in.additional_info
    
    _seasons_store[season_db_id] = season_data
    
    metadata = Metadata(
        pagination=Pagination(current_page=0, page_size=1, total_count=1, total_pages=1),
        status=[Status(message="Season created successfully", message_type="INFO")]
    )
    
    return BrAPIResponse(metadata=metadata, result=season_data)


@router.put("/seasons/{seasonDbId}", response_model=BrAPIResponse[dict])
async def update_season(
    seasonDbId: str,
    season_in: SeasonUpdate,
    db: AsyncSession = Depends(get_db),
    org_id: int = Depends(get_organization_id)
):
    """Update a season (BrAPI v2.1)"""
    _init_demo_seasons()
    
    season = _seasons_store.get(seasonDbId)
    
    if not season:
        raise HTTPException(status_code=404, detail="Season not found")
    
    # Update fields
    if season_in.season_name is not None:
        season["seasonName"] = season_in.season_name
    if season_in.year is not None:
        season["year"] = season_in.year
    if season_in.additional_info is not None:
        season["additionalInfo"] = season_in.additional_info
    
    _seasons_store[seasonDbId] = season
    
    metadata = Metadata(
        pagination=Pagination(current_page=0, page_size=1, total_count=1, total_pages=1),
        status=[Status(message="Season updated successfully", message_type="INFO")]
    )
    
    return BrAPIResponse(metadata=metadata, result=season)


@router.delete("/seasons/{seasonDbId}")
async def delete_season(
    seasonDbId: str,
    db: AsyncSession = Depends(get_db),
    org_id: int = Depends(get_organization_id)
):
    """Delete a season (BrAPI v2.1)"""
    _init_demo_seasons()
    
    if seasonDbId not in _seasons_store:
        raise HTTPException(status_code=404, detail="Season not found")
    
    del _seasons_store[seasonDbId]
    
    return {"message": "Season deleted successfully"}
