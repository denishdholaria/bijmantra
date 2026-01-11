"""
Pedigree Analysis API for Plant Breeding
Relationship matrices, inbreeding coefficients, and pedigree visualization

Endpoints:
- POST /api/v2/pedigree/load - Load pedigree data
- GET /api/v2/pedigree/individual/{id} - Get individual details
- GET /api/v2/pedigree/individuals - List all individuals
- POST /api/v2/pedigree/relationship-matrix - Get A-matrix
- GET /api/v2/pedigree/ancestors/{id} - Trace ancestors
- GET /api/v2/pedigree/descendants/{id} - Find descendants
- POST /api/v2/pedigree/coancestry - Calculate coancestry
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field, ConfigDict

from app.services.pedigree import get_pedigree_service

router = APIRouter(prefix="/pedigree", tags=["Pedigree Analysis"])


# ============================================
# SCHEMAS
# ============================================

class PedigreeRecord(BaseModel):
    """Single pedigree record"""
    id: str = Field(..., description="Individual ID")
    sire_id: Optional[str] = Field(None, description="Sire (father) ID")
    dam_id: Optional[str] = Field(None, description="Dam (mother) ID")


class PedigreeLoadRequest(BaseModel):
    """Request to load pedigree data"""
    pedigree: List[PedigreeRecord] = Field(..., description="List of pedigree records")
    
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "pedigree": [
                {"id": "F1", "sire_id": None, "dam_id": None},
                {"id": "F2", "sire_id": None, "dam_id": None},
                {"id": "F3", "sire_id": None, "dam_id": None},
                {"id": "G1", "sire_id": "F1", "dam_id": "F2"},
                {"id": "G2", "sire_id": "F1", "dam_id": "F3"},
                {"id": "G3", "sire_id": "G1", "dam_id": "G2"},
            ]
        }
    })


class RelationshipMatrixRequest(BaseModel):
    """Request for relationship matrix"""
    individual_ids: Optional[List[str]] = Field(None, description="Subset of individuals (None = all)")


class CoancestryRequest(BaseModel):
    """Request for coancestry calculation"""
    individual_1: str = Field(..., description="First individual ID")
    individual_2: str = Field(..., description="Second individual ID")


# ============================================
# ENDPOINTS
# ============================================

@router.post("/load")
async def load_pedigree(request: PedigreeLoadRequest):
    """
    Load pedigree data and calculate statistics
    
    Automatically calculates:
    - Generation numbers
    - Inbreeding coefficients (F)
    - Additive relationship matrix (A)
    - Pedigree completeness index
    
    Founders (unknown parents) are automatically detected.
    """
    service = get_pedigree_service()
    
    try:
        pedigree_data = [r.model_dump() for r in request.pedigree]
        stats = service.load_pedigree(pedigree_data)
        
        return {
            "success": True,
            "message": f"Loaded {stats.n_individuals} individuals",
            **stats.to_dict(),
        }
    except Exception as e:
        raise HTTPException(500, f"Failed to load pedigree: {str(e)}")


@router.get("/individual/{individual_id}")
async def get_individual(individual_id: str):
    """
    Get details for a specific individual
    
    Returns:
    - ID, sire, dam
    - Generation number
    - Inbreeding coefficient
    """
    service = get_pedigree_service()
    
    result = service.get_individual(individual_id)
    if result is None:
        raise HTTPException(404, f"Individual {individual_id} not found")
    
    return {
        "success": True,
        **result,
    }


@router.get("/individuals")
async def list_individuals(
    generation: Optional[int] = Query(None, description="Filter by generation")
):
    """
    List all individuals in the pedigree
    
    Optionally filter by generation number.
    """
    service = get_pedigree_service()
    
    individuals = service.list_individuals(generation=generation)
    
    return {
        "success": True,
        "count": len(individuals),
        "generation_filter": generation,
        "individuals": individuals,
    }


@router.post("/relationship-matrix")
async def get_relationship_matrix(request: RelationshipMatrixRequest):
    """
    Get additive relationship matrix (A-matrix)
    
    The A-matrix contains:
    - Diagonal: 1 + F (inbreeding coefficient)
    - Off-diagonal: Additive genetic relationship
    
    Values interpretation:
    - 1.0: Self (non-inbred)
    - 0.5: Parent-offspring or full siblings
    - 0.25: Half siblings or grandparent-grandchild
    - 0.125: First cousins
    """
    service = get_pedigree_service()
    
    try:
        result = service.get_relationship_matrix(request.individual_ids)
        return {
            "success": True,
            **result,
        }
    except Exception as e:
        raise HTTPException(500, f"Failed to calculate matrix: {str(e)}")


@router.get("/ancestors/{individual_id}")
async def get_ancestors(
    individual_id: str,
    max_generations: int = Query(5, ge=1, le=10, description="Max generations to trace")
):
    """
    Trace ancestors of an individual
    
    Returns a tree structure with:
    - Sire and dam at each generation
    - Inbreeding coefficient for each ancestor
    """
    service = get_pedigree_service()
    
    result = service.get_ancestors(individual_id, max_generations)
    
    if "error" in result:
        raise HTTPException(404, result["error"])
    
    return {
        "success": True,
        **result,
    }


@router.get("/descendants/{individual_id}")
async def get_descendants(
    individual_id: str,
    max_generations: int = Query(3, ge=1, le=10, description="Max generations to trace")
):
    """
    Find descendants of an individual
    
    Returns descendants grouped by generation.
    """
    service = get_pedigree_service()
    
    result = service.get_descendants(individual_id, max_generations)
    
    if "error" in result:
        raise HTTPException(404, result["error"])
    
    return {
        "success": True,
        **result,
    }


@router.post("/coancestry")
async def calculate_coancestry(request: CoancestryRequest):
    """
    Calculate coefficient of coancestry between two individuals
    
    Coancestry (θ) = 0.5 × A(i,j)
    
    This equals the expected inbreeding coefficient of their offspring.
    
    Interpretation:
    - θ = 0.5: Same individual
    - θ = 0.25: Full siblings or parent-offspring
    - θ = 0.125: Half siblings
    - θ = 0.0625: First cousins
    """
    service = get_pedigree_service()
    
    result = service.calculate_coancestry(request.individual_1, request.individual_2)
    
    if "error" in result:
        raise HTTPException(404, result["error"])
    
    return {
        "success": True,
        **result,
    }


@router.get("/stats")
async def get_pedigree_stats():
    """
    Get current pedigree statistics
    
    Returns summary of loaded pedigree data.
    """
    service = get_pedigree_service()
    
    if not service.individuals:
        return {
            "success": False,
            "message": "No pedigree data loaded. Use POST /pedigree/load first.",
        }
    
    founders = [i for i in service.individuals.values() 
               if i.sire_id is None and i.dam_id is None]
    
    inbreeding_values = [i.inbreeding for i in service.individuals.values()]
    
    return {
        "success": True,
        "n_individuals": len(service.individuals),
        "n_founders": len(founders),
        "n_generations": max(i.generation for i in service.individuals.values()) + 1,
        "avg_inbreeding": round(sum(inbreeding_values) / len(inbreeding_values), 4) if inbreeding_values else 0,
        "max_inbreeding": round(max(inbreeding_values), 4) if inbreeding_values else 0,
        "completeness_index": round(service._calculate_completeness(), 2),
    }
