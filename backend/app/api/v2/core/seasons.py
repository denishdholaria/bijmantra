"""
BrAPI Core - Seasons endpoints

Database-backed implementation for production use.
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
from app.models.core import Season as SeasonModel
from pydantic import BaseModel, Field, ConfigDict
from typing import Dict, Any, List

router = APIRouter()


# ============= Schemas =============

class SeasonBase(BaseModel):
    """Base season schema"""
    season_name: str = Field(..., alias="seasonName")
    year: Optional[int] = None
    additional_info: Optional[Dict[str, Any]] = Field(None, alias="additionalInfo")
    
    model_config = ConfigDict(populate_by_name=True)


class SeasonCreate(SeasonBase):
    """Schema for creating season"""
    pass


class SeasonUpdate(BaseModel):
    """Schema for updating season"""
    season_name: Optional[str] = Field(None, alias="seasonName")
    year: Optional[int] = None
    additional_info: Optional[Dict[str, Any]] = Field(None, alias="additionalInfo")
    
    model_config = ConfigDict(populate_by_name=True)


class SeasonResponse(BaseModel):
    """Season response schema (BrAPI compliant)"""
    season_db_id: str = Field(..., alias="seasonDbId")
    season_name: str = Field(..., alias="seasonName")
    year: Optional[int] = None
    additional_info: Optional[Dict[str, Any]] = Field(None, alias="additionalInfo")
    
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


def model_to_dict(season: SeasonModel) -> Dict[str, Any]:
    """Convert Season model to BrAPI response dict"""
    return {
        "seasonDbId": season.season_db_id,
        "seasonName": season.season_name,
        "year": season.year,
        "additionalInfo": season.additional_info or {},
    }


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
    
    # Build query
    query = select(SeasonModel).where(SeasonModel.organization_id == org_id)
    
    if year:
        query = query.where(SeasonModel.year == year)
    
    if season_db_id:
        query = query.where(SeasonModel.season_db_id == season_db_id)
    
    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total_count = total_result.scalar() or 0
    
    # Apply pagination and ordering
    query = query.order_by(SeasonModel.year.desc(), SeasonModel.season_name)
    query = query.offset(page * page_size).limit(page_size)
    
    result = await db.execute(query)
    seasons = result.scalars().all()
    
    # Convert to BrAPI format
    seasons_data = [model_to_dict(s) for s in seasons]
    
    return create_brapi_response(seasons_data, page, page_size, total_count)


@router.get("/seasons/{seasonDbId}", response_model=BrAPIResponse[dict])
async def get_season(
    seasonDbId: str,
    db: AsyncSession = Depends(get_db),
    org_id: int = Depends(get_organization_id)
):
    """Get a single season by DbId (BrAPI v2.1)"""
    
    query = select(SeasonModel).where(
        SeasonModel.season_db_id == seasonDbId,
        SeasonModel.organization_id == org_id
    )
    result = await db.execute(query)
    season = result.scalar_one_or_none()
    
    if not season:
        raise HTTPException(status_code=404, detail="Season not found")
    
    metadata = Metadata(
        pagination=Pagination(current_page=0, page_size=1, total_count=1, total_pages=1),
        status=[Status(message="Success", message_type="INFO")]
    )
    
    return BrAPIResponse(metadata=metadata, result=model_to_dict(season))


@router.post("/seasons", response_model=BrAPIResponse[dict], status_code=201)
async def create_season(
    season_in: SeasonCreate,
    db: AsyncSession = Depends(get_db),
    org_id: int = Depends(get_organization_id)
):
    """Create a new season (BrAPI v2.1)"""
    
    # Generate unique season_db_id
    season_db_id = f"season_{uuid.uuid4().hex[:12]}"
    
    season = SeasonModel(
        organization_id=org_id,
        season_db_id=season_db_id,
        season_name=season_in.season_name,
        year=season_in.year,
        additional_info=season_in.additional_info,
    )
    
    db.add(season)
    await db.commit()
    await db.refresh(season)
    
    metadata = Metadata(
        pagination=Pagination(current_page=0, page_size=1, total_count=1, total_pages=1),
        status=[Status(message="Season created successfully", message_type="INFO")]
    )
    
    return BrAPIResponse(metadata=metadata, result=model_to_dict(season))


@router.put("/seasons/{seasonDbId}", response_model=BrAPIResponse[dict])
async def update_season(
    seasonDbId: str,
    season_in: SeasonUpdate,
    db: AsyncSession = Depends(get_db),
    org_id: int = Depends(get_organization_id)
):
    """Update a season (BrAPI v2.1)"""
    
    query = select(SeasonModel).where(
        SeasonModel.season_db_id == seasonDbId,
        SeasonModel.organization_id == org_id
    )
    result = await db.execute(query)
    season = result.scalar_one_or_none()
    
    if not season:
        raise HTTPException(status_code=404, detail="Season not found")
    
    # Update fields
    if season_in.season_name is not None:
        season.season_name = season_in.season_name
    if season_in.year is not None:
        season.year = season_in.year
    if season_in.additional_info is not None:
        season.additional_info = season_in.additional_info
    
    await db.commit()
    await db.refresh(season)
    
    metadata = Metadata(
        pagination=Pagination(current_page=0, page_size=1, total_count=1, total_pages=1),
        status=[Status(message="Season updated successfully", message_type="INFO")]
    )
    
    return BrAPIResponse(metadata=metadata, result=model_to_dict(season))


@router.delete("/seasons/{seasonDbId}")
async def delete_season(
    seasonDbId: str,
    db: AsyncSession = Depends(get_db),
    org_id: int = Depends(get_organization_id)
):
    """Delete a season (BrAPI v2.1)"""
    
    query = select(SeasonModel).where(
        SeasonModel.season_db_id == seasonDbId,
        SeasonModel.organization_id == org_id
    )
    result = await db.execute(query)
    season = result.scalar_one_or_none()
    
    if not season:
        raise HTTPException(status_code=404, detail="Season not found")
    
    await db.delete(season)
    await db.commit()
    
    return {"message": "Season deleted successfully"}
