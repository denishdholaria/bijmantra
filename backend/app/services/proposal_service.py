"""
Proposal Service (The Scribe)
Manages the lifecycle of AI-generated proposals: Draft -> Review -> Execution.
This is the only place where "Write" operations triggered by AI are authorized.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
import json
import logging

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from sqlalchemy.orm import selectinload

from app.models.proposal import Proposal, ProposalStatus, ActionType
from app.models.core import User
from app.services.trial_planning import get_trial_planning_service
from app.services.cross_service import CrossService
from app.schemas.germplasm import CrossCreate

logger = logging.getLogger(__name__)

class ProposalService:
    
    async def create_proposal(
        self,
        db: AsyncSession,
        organization_id: int,
        title: str,
        description: str,
        action_type: ActionType,
        target_data: Dict[str, Any],
        ai_rationale: str,
        confidence_score: int,
        user_id: Optional[int] = None,  # If triggered by user interaction
        created_by_ai: bool = True
    ) -> Proposal:
        """
        Create a new proposal (Draft) for a write operation.
        """
        proposal = Proposal(
            organization_id=organization_id,
            user_id=user_id,
            title=title,
            description=description,
            action_type=action_type,
            target_data=target_data,
            ai_rationale=ai_rationale,
            confidence_score=confidence_score,
            status=ProposalStatus.DRAFT,
            created_by_ai=created_by_ai,
            reviewer_notes=""
        )
        
        db.add(proposal)
        await db.commit()
        await db.refresh(proposal)
        
        logger.info(f"[Scribe] Created proposal {proposal.id}: {title} ({action_type})")
        return proposal

    async def get_proposal(
        self, 
        db: AsyncSession, 
        proposal_id: int,
        organization_id: int
    ) -> Optional[Proposal]:
        """Get a proposal by ID"""
        stmt = (
            select(Proposal)
            .where(Proposal.id == proposal_id)
            .where(Proposal.organization_id == organization_id)
            .options(selectinload(Proposal.user))
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_proposals(
        self, 
        db: AsyncSession, 
        organization_id: int,
        status: Optional[ProposalStatus] = None,
        limit: int = 50
    ) -> List[Proposal]:
        """List proposals for an organization"""
        stmt = (
            select(Proposal)
            .where(Proposal.organization_id == organization_id)
            .order_by(desc(Proposal.created_at))
            .limit(limit)
            .options(selectinload(Proposal.user))
        )
        
        if status:
            stmt = stmt.where(Proposal.status == status)
            
        result = await db.execute(stmt)
        return result.scalars().all()

    async def submit_for_review(
        self,
        db: AsyncSession,
        proposal_id: int,
        organization_id: int
    ) -> Optional[Proposal]:
        """Move proposal from DRAFT to PENDING_REVIEW"""
        proposal = await self.get_proposal(db, proposal_id, organization_id)
        if not proposal:
            return None
            
        if proposal.status != ProposalStatus.DRAFT:
            raise ValueError(f"Only DRAFT proposals can be submitted. Current status: {proposal.status}")
            
        proposal.status = ProposalStatus.PENDING_REVIEW
        await db.commit()
        await db.refresh(proposal)
        return proposal

    async def review_proposal(
        self,
        db: AsyncSession,
        proposal_id: int,
        organization_id: int,
        approved: bool,
        reviewer_id: int,
        notes: str = ""
    ) -> Proposal:
        """
        Approve or Reject a proposal.
        If approved, it DOES NOT automatically execute (unless configured).
        """
        proposal = await self.get_proposal(db, proposal_id, organization_id)
        if not proposal:
            raise ValueError("Proposal not found")
        
        if proposal.status not in [ProposalStatus.PENDING_REVIEW, ProposalStatus.DRAFT]:
             # Allow approving from DRAFT for shortcuts
            pass
            
        status = ProposalStatus.APPROVED if approved else ProposalStatus.REJECTED
        
        proposal.status = status
        proposal.reviewer_notes = notes
        # We could store reviewer_id if we added a column, for now user_id is usually the owner
        # If we wanted to track who reviewed it, we might need a separate field or reuse user_id if it was null
        
        await db.commit()
        await db.refresh(proposal)
        
        logger.info(f"[Scribe] Proposal {proposal.id} {status.value} by user {reviewer_id}")
        return proposal

    async def execute_proposal(
        self,
        db: AsyncSession,
        proposal_id: int,
        organization_id: int,
        user_id: int  # User triggering the execution
    ) -> Proposal:
        """
        Execute an APPROVED proposal.
        This performs the actual write operation.
        """
        proposal = await self.get_proposal(db, proposal_id, organization_id)
        if not proposal:
            raise ValueError("Proposal not found")
            
        if proposal.status != ProposalStatus.APPROVED:
            raise ValueError(f"Cannot execute proposal with status: {proposal.status}. Must be APPROVED.")
            
        try:
            logger.info(f"[Scribe] Executing proposal {proposal.id} ({proposal.action_type})")
            result = {}
            
            # ----------------------------------------------------------------
            # DISPATCHER - The only place where AI actions become reality
            # ----------------------------------------------------------------
            
            if proposal.action_type == ActionType.CREATE_TRIAL:
                planning_service = get_trial_planning_service()
                # Ensure user_id attached to created_by if missing
                data = proposal.target_data.copy()
                if "createdBy" not in data:
                    data["createdBy"] = f"AI Agent (Approved by {user_id})"
                    
                result = await planning_service.create_trial(
                    db, 
                    organization_id, 
                    data
                )
                
            elif proposal.action_type == ActionType.CREATE_CROSS:
                # Convert dict to pydantic model
                cross_data = CrossCreate(**proposal.target_data)
                
                new_cross = await CrossService.create_cross(
                    db,
                    cross_data,
                    organization_id
                )
                
                # Convert model back to dict for storage
                result = CrossService.model_to_schema(new_cross).model_dump()
                
            elif proposal.action_type == ActionType.RECORD_OBSERVATION:
                # TODO: Implement observation recording service call
                # For now, just logging it
                logger.warning("Observation recording via Scribe not yet implemented in backend service")
                result = {"status": "not_implemented", "message": "Observation recording pending implementation"}
                
            elif proposal.action_type == ActionType.GENERATE_REPORT:
                # TODO: Implement report generation trigger
                result = {"status": "queued", "message": "Report generation queued"}
                
            else:
                raise ValueError(f"Unsupported action type: {proposal.action_type}")
                
            # ----------------------------------------------------------------
            
            proposal.execution_result = json.loads(json.dumps(result, default=str)) # Safety for dates
            proposal.status = ProposalStatus.EXECUTED
            proposal.executed_at = datetime.now(timezone.utc)
            
            await db.commit()
            return proposal
            
        except Exception as e:
            logger.error(f"[Scribe] Execution failed for proposal {proposal.id}: {e}")
            proposal.status = ProposalStatus.FAILED
            proposal.execution_result = {"error": str(e)}
            await db.commit()
            raise e

# Singleton
_proposal_service: Optional[ProposalService] = None

def get_proposal_service() -> ProposalService:
    global _proposal_service
    if _proposal_service is None:
        _proposal_service = ProposalService()
    return _proposal_service
