"""
Performance Ranking API
Rank breeding entries by performance metrics
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel
from typing import List, Optional
from app.services.performance_ranking import performance_ranking_service
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.api.deps import get_current_user

router = APIRouter(prefix="/performance-ranking", tags=["Performance Ranking"])


class CompareRequest(BaseModel):
    entry_ids: List[str]


@router.get("/rankings")
async def get_rankings(
    program_id: Optional[str] = Query(None, description="Filter by program"),
    trial_id: Optional[str] = Query(None, description="Filter by trial"),
    sort_by: str = Query("score", description="Sort by: score, yield, gebv, name"),
    limit: int = Query(50, description="Maximum number of entries"),
    search: Optional[str] = Query(None, description="Search by name, ID, or traits"),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Get ranked breeding entries
    Returns entries sorted by the specified metric
    """
    rankings =  await performance_ranking_service.get_rankings(db, current_user.organization_id,
        program_id=program_id,
        trial_id=trial_id,
        sort_by=sort_by,
        limit=limit,
        search=search,
    )
    return {
        "status": "success",
        "data": rankings,
        "count": len(rankings),
    }


@router.get("/top-performers")
async def get_top_performers(
    program_id: Optional[str] = Query(None, description="Filter by program"),
    trial_id: Optional[str] = Query(None, description="Filter by trial"),
    limit: int = Query(3, description="Number of top performers"),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get top performing entries (podium)"""
    top =  await performance_ranking_service.get_top_performers(db, current_user.organization_id,
        program_id=program_id,
        trial_id=trial_id,
        limit=limit,
    )
    return {
        "status": "success",
        "data": top,
        "count": len(top),
    }


@router.get("/statistics")
async def get_statistics(
    program_id: Optional[str] = Query(None, description="Filter by program"),
    trial_id: Optional[str] = Query(None, description="Filter by trial"),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get ranking statistics"""
    stats =  await performance_ranking_service.get_statistics(db, current_user.organization_id,
        program_id=program_id,
        trial_id=trial_id,
    )
    return {"status": "success", "data": stats}


@router.get("/entries/{entry_id}")
async def get_entry(
    entry_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get detailed information about an entry"""
    entry =  await performance_ranking_service.get_entry(db, current_user.organization_id, entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail=f"Entry {entry_id} not found")
    return {"status": "success", "data": entry}


@router.post("/compare")
async def compare_entries(
    data: CompareRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Compare multiple entries side by side"""
    result =  await performance_ranking_service.compare_entries(db, current_user.organization_id, data.entry_ids)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return {"status": "success", "data": result}


@router.get("/programs")
async def get_programs(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get list of programs with ranked entries"""
    programs =  await performance_ranking_service.get_programs(db, current_user.organization_id)
    return {"status": "success", "data": programs}


@router.get("/trials")
async def get_trials(
    program_id: Optional[str] = Query(None, description="Filter by program"),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get list of trials with ranked entries"""
    trials =  await performance_ranking_service.get_trials(db, current_user.organization_id, program_id=program_id)
    return {"status": "success", "data": trials}
