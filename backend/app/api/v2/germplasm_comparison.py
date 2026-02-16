"""
Germplasm Comparison API
Compare germplasm entries by traits and markers — queries Germplasm + related tables.

Refactored: Session 94 — migrated from in-memory demo data to DB queries.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.database import get_db
from app.api.deps import get_organization_id
from app.models.germplasm import Germplasm, GermplasmAttribute
from app.models.phenotyping import ObservationVariable

from app.api.deps import get_current_user

router = APIRouter(prefix="/germplasm-comparison", tags=["Germplasm Comparison"], dependencies=[Depends(get_current_user)])


# ============================================================================
# Schemas
# ============================================================================

class CompareRequest(BaseModel):
    ids: List[int] = Field(..., min_length=2, max_length=20)


# ============================================================================
# Helpers
# ============================================================================

def _germplasm_to_dict(g: Germplasm) -> dict:
    return {
        "id": str(g.id),
        "germplasmDbId": g.germplasm_db_id or str(g.id),
        "germplasmName": g.germplasm_name,
        "commonCropName": g.common_crop_name,
        "genus": g.genus,
        "species": g.species,
        "pedigree": g.pedigree,
    }


# ============================================================================
# Endpoints
# ============================================================================

@router.get("/germplasm")
async def list_germplasm(
    search: Optional[str] = Query(None),
    crop: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    organization_id: int = Depends(get_organization_id),
):
    """List germplasm entries available for comparison."""
    q = select(Germplasm).where(Germplasm.organization_id == organization_id)
    if search:
        q = q.where(Germplasm.germplasm_name.ilike(f"%{search}%"))
    if crop:
        q = q.where(Germplasm.common_crop_name.ilike(f"%{crop}%"))

    total = (await db.execute(
        select(func.count()).select_from(q.subquery())
    )).scalar() or 0

    q = q.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(q)
    items = result.scalars().all()

    return {
        "data": [_germplasm_to_dict(g) for g in items],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get("/germplasm/{germplasm_id}")
async def get_germplasm(
    germplasm_id: int,
    db: AsyncSession = Depends(get_db),
    organization_id: int = Depends(get_organization_id),
):
    """Get a single germplasm entry."""
    g = (await db.execute(
        select(Germplasm).where(
            Germplasm.id == germplasm_id,
            Germplasm.organization_id == organization_id,
        )
    )).scalar_one_or_none()
    if not g:
        raise HTTPException(status_code=404, detail="Germplasm not found")
    return _germplasm_to_dict(g)


@router.post("/compare")
async def compare_germplasm(
    req: CompareRequest,
    db: AsyncSession = Depends(get_db),
    organization_id: int = Depends(get_organization_id),
):
    """Compare two or more germplasm entries side-by-side."""
    result = await db.execute(
        select(Germplasm).where(
            Germplasm.id.in_(req.ids),
            Germplasm.organization_id == organization_id,
        )
    )
    entries = result.scalars().all()
    if len(entries) < 2:
        raise HTTPException(status_code=400, detail="Need at least 2 germplasm entries")

    comparison = []
    for g in entries:
        attrs = (await db.execute(
            select(GermplasmAttribute).where(GermplasmAttribute.germplasm_id == g.id)
        )).scalars().all()

        comparison.append({
            **_germplasm_to_dict(g),
            "attributes": {a.attribute_name: a.value for a in attrs},
        })

    return {"entries": comparison, "count": len(comparison)}


@router.get("/traits")
async def get_traits(
    crop: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    organization_id: int = Depends(get_organization_id),
):
    """Get observation variables (traits) available for comparison."""
    q = select(ObservationVariable).where(ObservationVariable.organization_id == organization_id)
    if crop:
        q = q.where(ObservationVariable.common_crop_name.ilike(f"%{crop}%"))
    q = q.limit(200)
    result = await db.execute(q)
    variables = result.scalars().all()
    return [
        {
            "id": str(v.id),
            "name": v.observation_variable_name,
            "trait": getattr(v, "trait_name", None),
        }
        for v in variables
    ]


@router.get("/markers")
async def get_markers(
    crop: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    organization_id: int = Depends(get_organization_id),
):
    """Get genetic markers for comparison. Markers table not yet created."""
    return []


@router.get("/statistics")
async def get_comparison_statistics(
    db: AsyncSession = Depends(get_db),
    organization_id: int = Depends(get_organization_id),
):
    """Get comparison statistics."""
    germplasm_count = (await db.execute(
        select(func.count(Germplasm.id)).where(Germplasm.organization_id == organization_id)
    )).scalar() or 0

    crop_count = (await db.execute(
        select(func.count(func.distinct(Germplasm.common_crop_name))).where(
            Germplasm.organization_id == organization_id,
            Germplasm.common_crop_name.isnot(None),
        )
    )).scalar() or 0

    return {
        "total_germplasm": germplasm_count,
        "total_crops": crop_count,
        "total_comparisons": 0,
    }
