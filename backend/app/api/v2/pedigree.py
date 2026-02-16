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
from fastapi import APIRouter, HTTPException, Query, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.core import User
from pydantic import BaseModel, Field, ConfigDict

from app.services.pedigree_service import PedigreeService

router = APIRouter(prefix="/pedigree", tags=["Pedigree Analysis"], dependencies=[Depends(get_current_user)])


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
async def load_pedigree(
    request: PedigreeLoadRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Load pedigree data and calculate statistics
    """
    service = PedigreeService(db)

    try:
        pedigree_data = [r.model_dump() for r in request.pedigree]
        # organization_id hardcoded for now or fetched from auth if available
        stats = await service.load_pedigree(pedigree_data)

        return {
            "success": True,
            **stats,
        }
    except Exception as e:
        raise HTTPException(500, f"Failed to load pedigree: {str(e)}")


@router.get("/individual/{individual_id}")
async def get_individual(
    individual_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get details for a specific individual
    """
    service = PedigreeService(db)

    result = await service.get_individual(individual_id)
    if result is None:
        raise HTTPException(404, f"Individual {individual_id} not found")

    return {
        "success": True,
        **result,
    }


@router.get("/individuals")
async def list_individuals(
    generation: Optional[int] = Query(None, description="Filter by generation"),
    db: AsyncSession = Depends(get_db)
):
    """
    List all individuals in the pedigree
    """
    service = PedigreeService(db)

    individuals, count = await service.get_individuals(generation=generation)

    return {
        "success": True,
        "count": count,
        "generation_filter": generation,
        "individuals": individuals,
    }


@router.post("/relationship-matrix")
async def get_relationship_matrix(
    request: RelationshipMatrixRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Get additive relationship matrix (A-matrix)
    NOTE: Currently returns placeholder from DB service
    """
    service = PedigreeService(db)

    # DB service doesn't implement full A-Matrix yet, so we warn or return placeholder
    # Ideally we'd implement it there too, but for now we follow the service signature
    try:
        # Assuming we might want to use the in-memory calc for small datasets?
        # For now, let's just return success=False or partial
        return {
            "success": False,
            "message": "Full A-Matrix calculation not yet migrated to DB service."
        }
    except Exception as e:
        raise HTTPException(500, f"Failed to calculate matrix: {str(e)}")


@router.get("/ancestors/{individual_id}")
async def get_ancestors(
    individual_id: str,
    max_generations: int = Query(5, ge=1, le=10, description="Max generations to trace"),
    db: AsyncSession = Depends(get_db)
):
    """
    Trace ancestors of an individual using Recursive CTE
    """
    service = PedigreeService(db)

    result = await service.get_ancestors(individual_id, max_generations)

    if "error" in result:
        raise HTTPException(404, result["error"])

    return {
        "success": True,
        **result,
    }


@router.get("/descendants/{individual_id}")
async def get_descendants(
    individual_id: str,
    max_generations: int = Query(3, ge=1, le=10, description="Max generations to trace"),
    db: AsyncSession = Depends(get_db)
):
    """
    Find descendants of an individual
    """
    service = PedigreeService(db)

    result = await service.get_descendants(individual_id, max_generations)

    if "error" in result:
        raise HTTPException(404, result["error"])

    return {
        "success": True,
        **result,
    }


@router.post("/coancestry")
async def calculate_coancestry(
    request: CoancestryRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Calculate coefficient of coancestry between two individuals
    """
    service = PedigreeService(db)

    result = await service.calculate_coancestry(request.individual_1, request.individual_2)

    if "error" in result:
        raise HTTPException(404, result["error"])

    return {
        "success": True,
        **result,
    }


@router.get("/stats")
async def get_pedigree_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get current pedigree statistics
    """
    service = PedigreeService(db)

    stats = await service.get_stats(organization_id=current_user.organization_id)

    return {
        "success": True,
        **stats
    }
