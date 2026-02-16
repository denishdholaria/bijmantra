"""
Molecular Breeding API

Endpoints for molecular breeding workflows.
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Optional

from app.services.molecular_breeding import molecular_breeding_service
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.api.deps import get_current_user


router = APIRouter(prefix="/molecular-breeding", tags=["Molecular Breeding"])


@router.get("/schemes", summary="List breeding schemes")
async def list_schemes(
    scheme_type: Optional[str] = Query(None, description="Filter by type (MABC, MARS, GS, Speed)"),
    status: Optional[str] = Query(None, description="Filter by status"),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get list of molecular breeding schemes."""
    schemes =  await molecular_breeding_service.get_schemes(db, current_user.organization_id, scheme_type=scheme_type, status=status)
    return {"success": True, "count": len(schemes), "schemes": schemes}


@router.get("/schemes/{scheme_id}", summary="Get breeding scheme")
async def get_scheme(
    scheme_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get details of a specific breeding scheme."""
    scheme =  await molecular_breeding_service.get_scheme(db, current_user.organization_id, scheme_id)
    if not scheme:
        raise HTTPException(404, f"Scheme {scheme_id} not found")
    return {"success": True, "data": scheme}


@router.get("/lines", summary="List introgression lines")
async def list_lines(
    scheme_id: Optional[str] = Query(None, description="Filter by scheme"),
    foreground_status: Optional[str] = Query(None, description="Filter by foreground status"),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get list of introgression lines."""
    lines =  await molecular_breeding_service.get_introgression_lines(db, current_user.organization_id,
        scheme_id=scheme_id, foreground_status=foreground_status
    )
    return {"success": True, "count": len(lines), "lines": lines}


@router.get("/statistics", summary="Get statistics")
async def get_statistics(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get molecular breeding statistics."""
    stats =  await molecular_breeding_service.get_statistics(db, current_user.organization_id)
    return {"success": True, "data": stats}


@router.get("/pyramiding/{scheme_id}", summary="Get pyramiding matrix")
async def get_pyramiding_matrix(
    scheme_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get gene pyramiding matrix for a scheme."""
    matrix =  await molecular_breeding_service.get_pyramiding_matrix(db, current_user.organization_id, scheme_id)
    return {"success": True, "data": matrix}
