"""
Selection Decisions API
Manage breeding candidate selection decisions (advance/reject/hold)
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List, Optional
from app.services.selection_decisions import selection_decisions_service

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
):
    """
    List selection candidates with optional filters
    Returns candidates sorted by GEBV (highest first)
    """
    candidates = selection_decisions_service.list_candidates(
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
async def get_candidate(candidate_id: str):
    """Get a single candidate with decision info"""
    candidate = selection_decisions_service.get_candidate(candidate_id)
    if not candidate:
        raise HTTPException(status_code=404, detail=f"Candidate {candidate_id} not found")
    return {"status": "success", "data": candidate}


@router.post("/candidates/{candidate_id}/decision")
async def record_decision(candidate_id: str, data: DecisionRequest):
    """
    Record a selection decision for a candidate
    Decision must be: advance, reject, or hold
    """
    result = selection_decisions_service.record_decision(
        candidate_id=candidate_id,
        decision=data.decision,
        notes=data.notes,
    )
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.post("/decisions/bulk")
async def record_bulk_decisions(data: BulkDecisionRequest):
    """Record multiple selection decisions at once"""
    result = selection_decisions_service.record_bulk_decisions(
        decisions=[d.model_dump() for d in data.decisions],
    )
    return result


@router.get("/statistics")
async def get_statistics(
    program_id: Optional[str] = Query(None, description="Filter by program"),
    trial_id: Optional[str] = Query(None, description="Filter by trial"),
):
    """Get selection decision statistics"""
    stats = selection_decisions_service.get_statistics(
        program_id=program_id,
        trial_id=trial_id,
    )
    return {"status": "success", "data": stats}


@router.get("/history")
async def get_decision_history(
    limit: int = Query(50, description="Maximum number of records"),
    candidate_id: Optional[str] = Query(None, description="Filter by candidate"),
):
    """Get decision history"""
    history = selection_decisions_service.get_decision_history(
        limit=limit,
        candidate_id=candidate_id,
    )
    return {
        "status": "success",
        "data": history,
        "count": len(history),
    }


@router.get("/programs")
async def get_programs():
    """Get list of breeding programs with candidates"""
    programs = selection_decisions_service.get_programs()
    return {"status": "success", "data": programs}


@router.get("/trials")
async def get_trials(
    program_id: Optional[str] = Query(None, description="Filter by program"),
):
    """Get list of trials with candidates"""
    trials = selection_decisions_service.get_trials(program_id=program_id)
    return {"status": "success", "data": trials}
