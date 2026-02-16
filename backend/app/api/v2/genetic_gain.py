"""
Genetic Gain API
Track and analyze genetic progress over breeding cycles
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from app.services.genetic_gain import genetic_gain_service
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.api.deps import get_current_user

router = APIRouter(prefix="/genetic-gain", tags=["Genetic Gain"])


class ProgramCreation(BaseModel):
    program_name: str
    crop: str
    target_trait: str
    start_year: int
    organization: str


class CycleRecord(BaseModel):
    cycle: int
    year: int
    mean_value: float
    best_value: float
    n_entries: int
    check_value: Optional[float] = None
    std_dev: Optional[float] = None


class ReleaseRecord(BaseModel):
    variety_name: str
    year: int
    trait_value: float


@router.post("/programs")
async def create_program(
    data: ProgramCreation,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Create a new breeding program for tracking"""
    program =  await genetic_gain_service.create_program(db, current_user.organization_id, **data.model_dump())
    return {"status": "success", "data": program}


@router.get("/programs")
async def list_programs(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """List all breeding programs"""
    programs =  await genetic_gain_service.list_programs(db, current_user.organization_id)
    return {"status": "success", "data": programs, "count": len(programs)}


@router.get("/programs/{program_id}")
async def get_program_summary(
    program_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get comprehensive summary of breeding program progress"""
    summary =  await genetic_gain_service.get_program_summary(db, current_user.organization_id, program_id)
    if "error" in summary:
        raise HTTPException(status_code=404, detail=summary["error"])
    return {"status": "success", "data": summary}


@router.post("/programs/{program_id}/cycles")
async def record_cycle(
    program_id: str, data: CycleRecord,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Record data for a breeding cycle"""
    try:
        cycle =  await genetic_gain_service.record_cycle(db, current_user.organization_id,
            program_id=program_id,
            **data.model_dump(),
        )
        return {"status": "success", "data": cycle}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/programs/{program_id}/releases")
async def record_release(
    program_id: str, data: ReleaseRecord,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Record a variety release"""
    try:
        release =  await genetic_gain_service.record_release(db, current_user.organization_id,
            program_id=program_id,
            **data.model_dump(),
        )
        return {"status": "success", "data": release}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/programs/{program_id}/gain")
async def calculate_genetic_gain(
    program_id: str,
    use_mean: bool = Query(True, description="Use mean values (True) or best values (False)"),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Calculate genetic gain over breeding cycles
    Returns absolute gain, percent gain, and annual rate
    """
    result =  await genetic_gain_service.calculate_genetic_gain(db, current_user.organization_id,
        program_id=program_id,
        use_mean=use_mean,
    )
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return {"status": "success", "data": result}


@router.get("/programs/{program_id}/check-comparison")
async def compare_to_check(
    program_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Compare breeding progress to check variety"""
    result =  await genetic_gain_service.compare_to_check(db, current_user.organization_id, program_id)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return {"status": "success", "data": result}


@router.get("/programs/{program_id}/realized-heritability")
async def calculate_realized_heritability(
    program_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Estimate realized heritability from selection response
    h² = R / S (response / selection differential)
    """
    result =  await genetic_gain_service.calculate_realized_heritability(db, current_user.organization_id, program_id)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return {"status": "success", "data": result}


@router.get("/programs/{program_id}/projection")
async def project_future_gain(
    program_id: str,
    years_ahead: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Project future genetic gain based on historical trend"""
    result =  await genetic_gain_service.project_future_gain(db, current_user.organization_id,
        program_id=program_id,
        years_ahead=years_ahead,
    )
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return {"status": "success", "data": result}


@router.get("/statistics")
async def get_statistics(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get overall genetic gain statistics"""
    stats =  await genetic_gain_service.get_statistics(db, current_user.organization_id)
    return {"status": "success", "data": stats}
