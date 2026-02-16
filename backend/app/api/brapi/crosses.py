from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import get_current_user, get_optional_user
from app.services.cross_service import CrossService
from app.schemas.brapi import BrAPIResponse, Metadata, Pagination, Status
from app.schemas.germplasm import Cross, CrossCreate, CrossUpdate, CrossStats

router = APIRouter()

@router.get("/crosses/stats", response_model=BrAPIResponse[CrossStats])
async def get_cross_stats(
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_optional_user),
):
    """Get statistics about crosses."""
    org_id = current_user.organization_id if current_user else None
    stats = await CrossService.get_stats(db, org_id)

    return BrAPIResponse(
        metadata=Metadata(
            pagination=Pagination(
                currentPage=0,
                pageSize=1,
                totalCount=1,
                totalPages=1
            ),
            status=[Status(message="Success", message_type="INFO")]
        ),
        result=stats
    )

@router.get("/crosses", response_model=BrAPIResponse[List[Cross]])
async def list_crosses(
    page: int = Query(0, ge=0),
    pageSize: int = Query(20, ge=1, le=1000),
    crossingProjectDbId: Optional[str] = None,
    crossType: Optional[str] = None,
    crossDbId: Optional[str] = None,
    crossName: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_optional_user),
):
    """Get a list of crosses."""
    org_id = current_user.organization_id if current_user else None
    crosses, total = await CrossService.list_crosses(
        db, page, pageSize, crossingProjectDbId, crossType, crossDbId, crossName, org_id
    )

    return BrAPIResponse(
        metadata=Metadata(
            pagination=Pagination(
                currentPage=page,
                pageSize=pageSize,
                totalCount=total,
                totalPages=(total + pageSize - 1) // pageSize if total > 0 else 0
            ),
            status=[Status(message="Request successful", message_type="INFO")]
        ),
        result=[CrossService.model_to_schema(c) for c in crosses]
    )

@router.post("/crosses", response_model=BrAPIResponse[Cross])
async def create_cross(
    cross: CrossCreate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """Create a new cross."""
    # Assuming organization_id is 1 if not set (fallback)
    org_id = current_user.organization_id if current_user and current_user.organization_id else 1

    new_cross = await CrossService.create_cross(db, cross, org_id)

    return BrAPIResponse(
        metadata=Metadata(
            pagination=Pagination(
                currentPage=0,
                pageSize=1,
                totalCount=1,
                totalPages=1
            ),
            status=[Status(message="Cross created successfully", message_type="INFO")]
        ),
        result=CrossService.model_to_schema(new_cross)
    )

@router.get("/crosses/{crossDbId}", response_model=BrAPIResponse[Cross])
async def get_cross(
    crossDbId: str,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_optional_user)
):
    """Get a cross by its database ID."""
    org_id = current_user.organization_id if current_user else None
    cross = await CrossService.get_cross(db, crossDbId, org_id)

    if not cross:
        raise HTTPException(status_code=404, detail="Cross not found")

    return BrAPIResponse(
        metadata=Metadata(
            pagination=Pagination(
                currentPage=0,
                pageSize=1,
                totalCount=1,
                totalPages=1
            ),
            status=[Status(message="Success", message_type="INFO")]
        ),
        result=CrossService.model_to_schema(cross)
    )

@router.put("/crosses", response_model=BrAPIResponse[List[Cross]])
async def update_crosses(
    crosses: List[CrossUpdate],
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """Update existing crosses in bulk."""
    org_id = current_user.organization_id if current_user else None
    updated = await CrossService.update_crosses(db, crosses, org_id)

    return BrAPIResponse(
        metadata=Metadata(
            pagination=Pagination(
                currentPage=0,
                pageSize=len(updated),
                totalCount=len(updated),
                totalPages=1
            ),
            status=[Status(message=f"Updated {len(updated)} crosses", message_type="INFO")]
        ),
        result=[CrossService.model_to_schema(c) for c in updated]
    )
