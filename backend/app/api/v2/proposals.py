"""
Proposal API Endpoints (The Scribe)
"""


from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.core import User
from app.models.proposal import ProposalStatus
from app.schemas.proposal import ProposalResponse, ProposalReview
from app.modules.breeding.services.proposal_service import get_proposal_service


router = APIRouter(prefix="/proposals", tags=["Proposals"], dependencies=[Depends(get_current_user)])

@router.get("/", response_model=list[ProposalResponse])
async def list_proposals(
    status: ProposalStatus | None = None,
    limit: int = 50,
    skip: int = 0,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    List proposals.
    """
    service = get_proposal_service()
    return await service.list_proposals(
        db,
        organization_id=current_user.organization_id,
        status=status,
        limit=limit
    )

@router.get("/{proposal_id}", response_model=ProposalResponse)
async def get_proposal(
    proposal_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get a specific proposal by ID.
    """
    service = get_proposal_service()
    proposal = await service.get_proposal(db, proposal_id, current_user.organization_id)
    if not proposal:
        raise HTTPException(status_code=404, detail="Proposal not found")
    return proposal

@router.post("/{proposal_id}/review", response_model=ProposalResponse)
async def review_proposal(
    proposal_id: int,
    review: ProposalReview,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Review a proposal (Approve or Reject).
    """
    service = get_proposal_service()
    try:
        return await service.review_proposal(
            db,
            proposal_id=proposal_id,
            organization_id=current_user.organization_id,
            approved=review.approved,
            reviewer_id=current_user.id,
            notes=review.notes or ""
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{proposal_id}/execute", response_model=ProposalResponse)
async def execute_proposal(
    proposal_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Execute an APPROVED proposal.
    """
    service = get_proposal_service()
    try:
        return await service.execute_proposal(
            db, proposal_id, current_user.organization_id, current_user.id
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
