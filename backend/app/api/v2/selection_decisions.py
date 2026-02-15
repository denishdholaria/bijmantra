"""
Selection Decisions API
Manage breeding candidate selection decisions (advance/reject/hold)
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel, Field
from typing import List, Optional
from app.services.selection_decisions import selection_decisions_service
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.api.deps import get_current_user

router = APIRouter(prefix="/selection-decisions", tags=["Selection Decisions"])


class DecisionRequest(BaseModel):
    decision: str = Field(..., description="Decision: advance, reject, or hold")
    notes: Optional[str] = Field(None, description="Optional notes for the decision")


class BulkDecisionItem(BaseModel):
    candidate_id: str
    decision: str
    notes: Optional[str] = None


class BulkDecisionRequest(BaseModel):
    decisions: List[BulkDecisionItem]


@router.get("/candidates")
async def list_candidates(
    program_id: Optional[str] = Query(None, description="Filter by program"),
    trial_id: Optional[str] = Query(None, description="Filter by trial"),
    generation: Optional[str] = Query(None, description="Filter by generation"),
    decision_status: Optional[str] = Query(None, description="Filter by decision status: advance, reject, hold, pending"),
    min_gebv: Optional[float] = Query(None, description="Minimum GEBV threshold"),
    search: Optional[str] = Query(None, description="Search by name, pedigree, or traits"),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    List selection candidates with optional filters
    Returns candidates sorted by GEBV (highest first)
    """
    candidates =  await selection_decisions_service.list_candidates(db, current_user.organization_id, 
        program_id=program_id,
        trial_id=trial_id,
        generation=generation,
        decision_status=decision_status,
        min_gebv=min_gebv,
        search=search,
    )
    return {
        "status": "success",
        "data": candidates,
        "count": len(candidates),
    }


@router.get("/candidates/{candidate_id}")
async def get_candidate(
    candidate_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get a single candidate with decision info"""
    candidate =  await selection_decisions_service.get_candidate(db, current_user.organization_id, candidate_id)
    if not candidate:
        raise HTTPException(status_code=404, detail=f"Candidate {candidate_id} not found")
    return {"status": "success", "data": candidate}


@router.post("/candidates/{candidate_id}/decision")
async def record_decision(
    candidate_id: str, data: DecisionRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Record a selection decision for a candidate
    Decision must be: advance, reject, or hold
    """
    result =  await selection_decisions_service.record_decision(db, current_user.organization_id, 
        candidate_id=candidate_id,
        decision=data.decision,
        notes=data.notes,
    )
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.post("/decisions/bulk")
async def record_bulk_decisions(
    data: BulkDecisionRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Record multiple selection decisions at once"""
    result =  await selection_decisions_service.record_bulk_decisions(db, current_user.organization_id, 
        decisions=[d.model_dump() for d in data.decisions],
    )
    return result


@router.get("/statistics")
async def get_statistics(
    program_id: Optional[str] = Query(None, description="Filter by program"),
    trial_id: Optional[str] = Query(None, description="Filter by trial"),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get selection decision statistics"""
    stats =  await selection_decisions_service.get_statistics(db, current_user.organization_id, 
        program_id=program_id,
        trial_id=trial_id,
    )
    return {"status": "success", "data": stats}


@router.get("/history")
async def get_decision_history(
    limit: int = Query(50, description="Maximum number of records"),
    candidate_id: Optional[str] = Query(None, description="Filter by candidate"),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get decision history"""
    history =  await selection_decisions_service.get_decision_history(db, current_user.organization_id, 
        limit=limit,
        candidate_id=candidate_id,
    )
    return {
        "status": "success",
        "data": history,
        "count": len(history),
    }


@router.get("/programs")
async def get_programs(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get list of breeding programs with candidates"""
    programs =  await selection_decisions_service.get_programs(db, current_user.organization_id)
    return {"status": "success", "data": programs}


@router.get("/trials")
async def get_trials(
    program_id: Optional[str] = Query(None, description="Filter by program"),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get list of trials with candidates"""
    trials =  await selection_decisions_service.get_trials(db, current_user.organization_id, program_id=program_id)
    return {"status": "success", "data": trials}
