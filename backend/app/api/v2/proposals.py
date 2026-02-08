"""
Proposal API Endpoints (The Scribe)
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.core.database import get_db
from app.services.proposal_service import get_proposal_service
from app.schemas.proposal import ProposalResponse, ProposalReview
from app.models.proposal import ProposalStatus
from app.api.deps import get_current_user

router = APIRouter(prefix="/proposals", tags=["Proposals"], dependencies=[Depends(get_current_user)])

@router.get("/", response_model=List[ProposalResponse])
async def list_proposals(
    status: Optional[ProposalStatus] = None,
    organization_id: int = 1, # Default to 1 for now
    limit: int = 50,
    skip: int = 0,
    db: AsyncSession = Depends(get_db)
):
    """
    List proposals.
    """
    service = get_proposal_service()
    return await service.list_proposals(
        db, 
        organization_id=organization_id, 
        status=status, 
        limit=limit
    )

@router.get("/{proposal_id}", response_model=ProposalResponse)
async def get_proposal(
    proposal_id: int,
    organization_id: int = 1,
    db: AsyncSession = Depends(get_db)
):
    """
    Get a specific proposal by ID.
    """
    service = get_proposal_service()
    proposal = await service.get_proposal(db, proposal_id, organization_id)
    if not proposal:
        raise HTTPException(status_code=404, detail="Proposal not found")
    return proposal

@router.post("/{proposal_id}/review", response_model=ProposalResponse)
async def review_proposal(
    proposal_id: int,
    review: ProposalReview,
    organization_id: int = 1,
    user_id: int = 1, # Mock user ID for now
    db: AsyncSession = Depends(get_db)
):
    """
    Review a proposal (Approve or Reject).
    """
    service = get_proposal_service()
    try:
        return await service.review_proposal(
            db, 
            proposal_id=proposal_id, 
            organization_id=organization_id, 
            approved=review.approved, 
            reviewer_id=user_id,
            notes=review.notes or ""
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{proposal_id}/execute", response_model=ProposalResponse)
async def execute_proposal(
    proposal_id: int,
    organization_id: int = 1,
    user_id: int = 1, # Mock user ID
    db: AsyncSession = Depends(get_db)
):
    """
    Execute an APPROVED proposal.
    """
    service = get_proposal_service()
    try:
        return await service.execute_proposal(
            db, proposal_id, organization_id, user_id
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
