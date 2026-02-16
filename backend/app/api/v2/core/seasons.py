"""
BrAPI Core - Seasons endpoints

Database-backed implementation for production use.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.core.database import get_db
from app.api.deps import get_organization_id
from app.schemas.brapi import BrAPIResponse, Metadata, Pagination, Status
from app.core.config import settings
from app.schemas.core import Season, SeasonCreate, SeasonUpdate
from app.services.core.seasons_service import season_service

router = APIRouter()


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

    seasons, total_count = await season_service.list_seasons(
        db=db,
        org_id=org_id,
        page=page,
        page_size=page_size,
        year=year,
        season_db_id=season_db_id
    )

    # Convert to BrAPI format using Schema
    seasons_data = [Season.model_validate(s).model_dump(by_alias=True) for s in seasons]

    return create_brapi_response(seasons_data, page, page_size, total_count)


@router.get("/seasons/{seasonDbId}", response_model=BrAPIResponse[dict])
async def get_season(
    seasonDbId: str,
    db: AsyncSession = Depends(get_db),
    org_id: int = Depends(get_organization_id)
):
    """Get a single season by DbId (BrAPI v2.1)"""

    season = await season_service.get_season(db, org_id, seasonDbId)

    if not season:
        raise HTTPException(status_code=404, detail="Season not found")

    metadata = Metadata(
        pagination=Pagination(current_page=0, page_size=1, total_count=1, total_pages=1),
        status=[Status(message="Success", message_type="INFO")]
    )

    season_data = Season.model_validate(season).model_dump(by_alias=True)

    return BrAPIResponse(metadata=metadata, result=season_data)


@router.post("/seasons", response_model=BrAPIResponse[dict], status_code=201)
async def create_season(
    season_in: SeasonCreate,
    db: AsyncSession = Depends(get_db),
    org_id: int = Depends(get_organization_id)
):
    """Create a new season (BrAPI v2.1)"""

    season = await season_service.create_season(db, org_id, season_in)

    metadata = Metadata(
        pagination=Pagination(current_page=0, page_size=1, total_count=1, total_pages=1),
        status=[Status(message="Season created successfully", message_type="INFO")]
    )

    season_data = Season.model_validate(season).model_dump(by_alias=True)

    return BrAPIResponse(metadata=metadata, result=season_data)


@router.put("/seasons/{seasonDbId}", response_model=BrAPIResponse[dict])
async def update_season(
    seasonDbId: str,
    season_in: SeasonUpdate,
    db: AsyncSession = Depends(get_db),
    org_id: int = Depends(get_organization_id)
):
    """Update a season (BrAPI v2.1)"""

    season = await season_service.update_season(db, org_id, seasonDbId, season_in)

    if not season:
        raise HTTPException(status_code=404, detail="Season not found")

    metadata = Metadata(
        pagination=Pagination(current_page=0, page_size=1, total_count=1, total_pages=1),
        status=[Status(message="Season updated successfully", message_type="INFO")]
    )

    season_data = Season.model_validate(season).model_dump(by_alias=True)

    return BrAPIResponse(metadata=metadata, result=season_data)


@router.delete("/seasons/{seasonDbId}")
async def delete_season(
    seasonDbId: str,
    db: AsyncSession = Depends(get_db),
    org_id: int = Depends(get_organization_id)
):
    """Delete a season (BrAPI v2.1)"""

    success = await season_service.delete_season(db, org_id, seasonDbId)

    if not success:
        raise HTTPException(status_code=404, detail="Season not found")

    return {"message": "Season deleted successfully"}
