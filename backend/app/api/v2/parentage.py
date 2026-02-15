"""
Parentage Analysis API

Endpoints for DNA-based parentage verification and analysis.

Converted to database queries per Zero Mock Data Policy (Session 77).
Uses parentage_service which queries Sample table for real data.
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Optional, List
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import get_organization_id
from app.services.parentage_analysis import parentage_service


from app.api.deps import get_current_user

router = APIRouter(prefix="/parentage", tags=["Parentage Analysis"], dependencies=[Depends(get_current_user)])


class VerifyParentageRequest(BaseModel):
    """Request to verify parentage"""
    offspring_id: str = Field(..., description="ID of the offspring to verify")
    claimed_female_id: str = Field(..., description="ID of the claimed female parent")
    claimed_male_id: Optional[str] = Field(None, description="ID of the claimed male parent (optional)")


class FindParentsRequest(BaseModel):
    """Request to find potential parents"""
    offspring_id: str = Field(..., description="ID of the offspring")
    candidate_ids: Optional[List[str]] = Field(None, description="List of candidate parent IDs (optional, uses all if not specified)")


@router.get("/markers", summary="Get marker panel")
async def get_marker_panel(
    db: AsyncSession = Depends(get_db),
    organization_id: int = Depends(get_organization_id),
):
    """
    Get the marker panel used for parentage analysis
    
    Returns the list of SSR/SNP markers with their properties.
    Returns empty list when no marker data exists.
    """
    markers = await parentage_service.get_marker_panel(db, organization_id)
    return {
        "success": True,
        "count": len(markers),
        "markers": markers,
    }


@router.get("/individuals", summary="List individuals")
async def list_individuals(
    db: AsyncSession = Depends(get_db),
    organization_id: int = Depends(get_organization_id),
):
    """
    Get list of individuals with genotype data available
    
    Returns individuals that can be used in parentage analysis.
    Returns empty list when no genotype data exists.
    """
    individuals = await parentage_service.get_individuals(db, organization_id)
    return {
        "success": True,
        "count": len(individuals),
        "individuals": individuals,
    }


@router.get("/individuals/{individual_id}", summary="Get individual genotype")
async def get_individual_genotype(
    individual_id: str,
    db: AsyncSession = Depends(get_db),
    organization_id: int = Depends(get_organization_id),
):
    """
    Get genotype data for a specific individual
    
    Returns marker genotypes for the individual.
    Returns 404 when individual not found.
    """
    genotype = await parentage_service.get_genotype(db, organization_id, individual_id)
    if not genotype:
        raise HTTPException(404, f"Individual {individual_id} not found")
    
    return {
        "success": True,
        "data": genotype,
    }


@router.post("/verify", summary="Verify parentage")
async def verify_parentage(
    request: VerifyParentageRequest,
    db: AsyncSession = Depends(get_db),
    organization_id: int = Depends(get_organization_id),
):
    """
    Verify parentage of an offspring against claimed parents
    
    Parentage Verification Method:
    Uses marker-based exclusion analysis and likelihood ratios.
    
    Exclusion Principle:
    If offspring has an allele that cannot be inherited from either
    claimed parent, that parent is excluded.
    
    Likelihood Ratio (LR):
    LR = P(genotypes | H1) / P(genotypes | H2)
    Where H1 = claimed parents are true parents
          H2 = random individuals from population
    
    Interpretation:
    - LR > 100: Strong support for parentage
    - LR 10-100: Moderate support
    - LR < 10: Weak support
    - Exclusions > 2: Parentage excluded
    
    Returns:
    - Marker-by-marker comparison
    - Exclusion counts
    - Likelihood ratio
    - Conclusion (CONFIRMED, EXCLUDED, INCONCLUSIVE)
    """
    result = await parentage_service.verify_parentage(
        db=db,
        organization_id=organization_id,
        offspring_id=request.offspring_id,
        claimed_female_id=request.claimed_female_id,
        claimed_male_id=request.claimed_male_id,
    )
    
    if "error" in result:
        raise HTTPException(400, result["error"])
    
    return {
        "success": True,
        "data": result,
    }


@router.post("/find-parents", summary="Find potential parents")
async def find_parents(
    request: FindParentsRequest,
    db: AsyncSession = Depends(get_db),
    organization_id: int = Depends(get_organization_id),
):
    """
    Find potential parents for an offspring from a pool of candidates
    
    Scores each candidate based on marker compatibility.
    
    Returns:
    - Ranked list of candidates
    - Compatibility scores
    - Likely parents (no exclusions)
    """
    result = await parentage_service.find_parents(
        db=db,
        organization_id=organization_id,
        offspring_id=request.offspring_id,
        candidate_ids=request.candidate_ids,
    )
    
    if "error" in result:
        raise HTTPException(400, result["error"])
    
    return {
        "success": True,
        "data": result,
    }


@router.get("/history", summary="Get analysis history")
async def get_analysis_history(
    db: AsyncSession = Depends(get_db),
    organization_id: int = Depends(get_organization_id),
):
    """
    Get history of parentage analyses performed
    
    Returns summary of all analyses with conclusions.
    Returns empty list when no analyses have been performed.
    """
    history = await parentage_service.get_analysis_history(db, organization_id)
    return {
        "success": True,
        "count": len(history),
        "analyses": history,
    }


@router.get("/statistics", summary="Get statistics")
async def get_statistics(
    db: AsyncSession = Depends(get_db),
    organization_id: int = Depends(get_organization_id),
):
    """
    Get parentage analysis statistics
    
    Returns counts and rates for confirmed, excluded, and inconclusive analyses.
    Returns zeros when no analyses have been performed.
    """
    stats = await parentage_service.get_statistics(db, organization_id)
    return {
        "success": True,
        "data": stats,
    }
