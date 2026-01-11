"""
Parentage Analysis API

Endpoints for DNA-based parentage verification and analysis.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List
from pydantic import BaseModel, Field

from app.services.parentage_analysis import parentage_service


router = APIRouter(prefix="/parentage", tags=["Parentage Analysis"])


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
async def get_marker_panel():
    """
    Get the marker panel used for parentage analysis
    
    Returns the list of SSR/SNP markers with their properties.
    """
    markers = parentage_service.get_marker_panel()
    return {
        "success": True,
        "count": len(markers),
        "markers": markers,
    }


@router.get("/individuals", summary="List individuals")
async def list_individuals():
    """
    Get list of individuals with genotype data available
    
    Returns individuals that can be used in parentage analysis.
    """
    individuals = parentage_service.get_individuals()
    return {
        "success": True,
        "count": len(individuals),
        "individuals": individuals,
    }


@router.get("/individuals/{individual_id}", summary="Get individual genotype")
async def get_individual_genotype(individual_id: str):
    """
    Get genotype data for a specific individual
    
    Returns marker genotypes for the individual.
    """
    genotype = parentage_service.get_genotype(individual_id)
    if not genotype:
        raise HTTPException(404, f"Individual {individual_id} not found")
    
    return {
        "success": True,
        "data": genotype,
    }


@router.post("/verify", summary="Verify parentage")
async def verify_parentage(request: VerifyParentageRequest):
    """
    Verify parentage of an offspring against claimed parents
    
    Performs marker-based exclusion analysis and calculates likelihood ratios.
    
    Returns:
    - Marker-by-marker comparison
    - Exclusion counts
    - Likelihood ratio
    - Conclusion (CONFIRMED, EXCLUDED, INCONCLUSIVE)
    """
    result = parentage_service.verify_parentage(
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
async def find_parents(request: FindParentsRequest):
    """
    Find potential parents for an offspring from a pool of candidates
    
    Scores each candidate based on marker compatibility.
    
    Returns:
    - Ranked list of candidates
    - Compatibility scores
    - Likely parents (no exclusions)
    """
    result = parentage_service.find_parents(
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
async def get_analysis_history():
    """
    Get history of parentage analyses performed
    
    Returns summary of all analyses with conclusions.
    """
    history = parentage_service.get_analysis_history()
    return {
        "success": True,
        "count": len(history),
        "analyses": history,
    }


@router.get("/statistics", summary="Get statistics")
async def get_statistics():
    """
    Get parentage analysis statistics
    
    Returns counts and rates for confirmed, excluded, and inconclusive analyses.
    """
    stats = parentage_service.get_statistics()
    return {
        "success": True,
        "data": stats,
    }


@router.get("/demo", summary="Get demo data")
async def get_demo_data():
    """
    Get demo data for testing the parentage analysis UI
    
    Returns sample individuals and suggested test cases.
    """
    individuals = parentage_service.get_individuals()
    markers = parentage_service.get_marker_panel()
    
    return {
        "success": True,
        "individuals": individuals,
        "markers": markers,
        "test_cases": [
            {
                "name": "True Progeny Test",
                "description": "Verify Progeny-001 against IR64 (female) and Swarna (male) - should CONFIRM",
                "offspring_id": "Progeny-001",
                "claimed_female_id": "IR64",
                "claimed_male_id": "Swarna",
            },
            {
                "name": "Partial Match Test",
                "description": "Verify Progeny-002 against IR64 and Swarna - may show some exclusions",
                "offspring_id": "Progeny-002",
                "claimed_female_id": "IR64",
                "claimed_male_id": "Swarna",
            },
            {
                "name": "Unknown Parentage Test",
                "description": "Verify Progeny-003 against IR64 only - unknown male",
                "offspring_id": "Progeny-003",
                "claimed_female_id": "IR64",
                "claimed_male_id": None,
            },
            {
                "name": "Find Parents Test",
                "description": "Find potential parents for Unknown-001 from all candidates",
                "offspring_id": "Unknown-001",
            },
        ],
    }
