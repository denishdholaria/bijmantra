"""
Germplasm Comparison API
Compare germplasm entries by traits and markers — queries Germplasm + related tables.

Refactored: Session 94 — migrated from in-memory demo data to DB queries.
Refactored: Architecture Stabilization — migrated business logic to comparison_service.
"""


from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_organization_id
from app.core.database import get_db
from app.modules.germplasm.services.comparison_service import germplasm_comparison_service


router = APIRouter(
    prefix="/germplasm-comparison",
    tags=["Germplasm Comparison"],
    dependencies=[Depends(get_current_user)],
)


# ============================================================================
# Schemas
# ============================================================================


class CompareRequest(BaseModel):
    ids: list[int] = Field(..., min_length=2, max_length=20)


# ============================================================================
# Endpoints
# ============================================================================


@router.get("/germplasm")
async def list_germplasm(
    search: str | None = Query(None),
    crop: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    organization_id: int = Depends(get_organization_id),
):
    """List germplasm entries available for comparison."""
    return await germplasm_comparison_service.list_germplasm(
        db, organization_id, search, crop, page, page_size
    )


@router.get("/germplasm/{germplasm_id}")
async def get_germplasm(
    germplasm_id: int,
    db: AsyncSession = Depends(get_db),
    organization_id: int = Depends(get_organization_id),
):
    """Get a single germplasm entry."""
    result = await germplasm_comparison_service.get_germplasm(db, organization_id, germplasm_id)
    if not result:
        raise HTTPException(status_code=404, detail="Germplasm not found")
    return result


@router.post("/compare")
async def compare_germplasm(
    req: CompareRequest,
    db: AsyncSession = Depends(get_db),
    organization_id: int = Depends(get_organization_id),
):
    """Compare two or more germplasm entries side-by-side."""
    try:
        return await germplasm_comparison_service.compare_germplasm(db, organization_id, req.ids)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/traits")
async def get_traits(
    crop: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    organization_id: int = Depends(get_organization_id),
):
    """Get observation variables (traits) available for comparison."""
    return await germplasm_comparison_service.get_traits(db, organization_id, crop)


@router.get("/markers")
async def get_markers(
    crop: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    organization_id: int = Depends(get_organization_id),
):
    """Get genetic markers for comparison. Markers table not yet created."""
    return await germplasm_comparison_service.get_markers(db, organization_id, crop)


@router.get("/statistics")
async def get_comparison_statistics(
    db: AsyncSession = Depends(get_db),
    organization_id: int = Depends(get_organization_id),
):
    """Get comparison statistics."""
    return await germplasm_comparison_service.get_statistics(db, organization_id)
