"""
BrAPI Core - Pedigree endpoints
GET/POST/PUT /pedigree - Pedigree information
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Query, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from app.api import deps
from app.services.pedigree_service import PedigreeService

router = APIRouter()

# --- Pydantic Models for Pedigree Analysis ---

class PedigreeRecord(BaseModel):
    id: str
    sire_id: Optional[str] = None
    dam_id: Optional[str] = None

class PedigreeIndividual(BaseModel):
    id: str
    sire_id: Optional[str] = None
    dam_id: Optional[str] = None
    generation: int
    inbreeding: float

class PedigreeStats(BaseModel):
    n_individuals: int
    n_founders: int
    n_generations: int
    avg_inbreeding: float
    max_inbreeding: float
    completeness_index: float

class LoadPedigreeResponse(BaseModel):
    success: bool
    message: str
    n_individuals: int
    n_founders: int
    n_generations: int
    avg_inbreeding: float
    max_inbreeding: float
    completeness_index: float

class IndividualResponse(BaseModel):
    success: bool
    id: str
    sire_id: Optional[str] = None
    dam_id: Optional[str] = None
    generation: int
    inbreeding: float

class IndividualsResponse(BaseModel):
    success: bool
    count: int
    individuals: List[PedigreeIndividual]

class AncestorResult(BaseModel):
    individual_id: str
    sire_id: Optional[str] = None
    dam_id: Optional[str] = None
    n_ancestors: int
    ancestors: Optional[List[str]] = None

class AncestorResponse(BaseModel):
    success: bool
    individual_id: str
    sire_id: Optional[str] = None
    dam_id: Optional[str] = None
    n_ancestors: int
    ancestors: Optional[List[str]] = None

class DescendantResult(BaseModel):
    individual_id: str
    n_descendants: int
    descendants: Optional[List[str]] = None

class DescendantResponse(BaseModel):
    success: bool
    individual_id: str
    n_descendants: int
    descendants: Optional[List[str]] = None

class CoancestryRequest(BaseModel):
    individual_1: str
    individual_2: str

class CoancestryResult(BaseModel):
    coancestry: float
    relationship: str
    individual_1: str
    individual_2: str

class CoancestryResponse(BaseModel):
    success: bool
    coancestry: float
    relationship: str
    individual_1: str
    individual_2: str

class RelationshipMatrixRequest(BaseModel):
    individual_ids: Optional[List[str]] = None

class RelationshipMatrixResponse(BaseModel):
    success: bool
    individuals: List[str]
    matrix: List[List[float]]

# --- BrAPI Models ---

class PedigreeCreate(BaseModel):
    germplasmDbId: str
    germplasmName: Optional[str] = None
    parents: List[Dict[str, Any]] = [] # {germplasmDbId, parentType}

# --- Endpoints ---

@router.post("/pedigree/load", response_model=LoadPedigreeResponse)
async def load_pedigree(
    payload: dict, # Expecting { "pedigree": [...] }
    db: AsyncSession = Depends(deps.get_db),
    organization_id: int = Depends(deps.get_organization_id)
):
    """
    Load pedigree data.
    Input: { pedigree: [ { id, sire_id, dam_id } ] }
    """
    pedigree_data = payload.get("pedigree", [])
    service = PedigreeService(db)
    result = await service.load_pedigree(pedigree_data, organization_id)
    return result

@router.get("/pedigree/stats", response_model=LoadPedigreeResponse)
async def get_stats(
    db: AsyncSession = Depends(deps.get_db),
    organization_id: int = Depends(deps.get_organization_id)
):
    service = PedigreeService(db)
    stats = await service.get_stats(organization_id)
    return {
        "success": True,
        "message": "Stats retrieved",
        **stats
    }

@router.get("/pedigree/individual/{individual_id}", response_model=IndividualResponse)
async def get_individual(
    individual_id: str,
    db: AsyncSession = Depends(deps.get_db),
    organization_id: int = Depends(deps.get_organization_id)
):
    service = PedigreeService(db)
    data = await service.get_individual(individual_id, organization_id)
    if not data:
        raise HTTPException(status_code=404, detail="Individual not found")
    return {
        "success": True,
        **data
    }

@router.get("/pedigree/individuals", response_model=IndividualsResponse)
async def get_individuals(
    generation: Optional[int] = None,
    db: AsyncSession = Depends(deps.get_db),
    organization_id: int = Depends(deps.get_organization_id)
):
    service = PedigreeService(db)
    # Default to high limit for analysis tool
    individuals, count = await service.get_individuals(generation, page=0, page_size=10000, organization_id=organization_id)
    return {
        "success": True,
        "count": count,
        "individuals": individuals
    }

@router.get("/pedigree/ancestors/{individual_id}", response_model=AncestorResponse)
async def get_ancestors(
    individual_id: str,
    max_generations: int = 5,
    db: AsyncSession = Depends(deps.get_db),
    organization_id: int = Depends(deps.get_organization_id)
):
    service = PedigreeService(db)
    result = await service.get_ancestors(individual_id, max_generations, organization_id)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return {
        "success": True,
        **result
    }

@router.get("/pedigree/descendants/{individual_id}", response_model=DescendantResponse)
async def get_descendants(
    individual_id: str,
    max_generations: int = 3,
    db: AsyncSession = Depends(deps.get_db),
    organization_id: int = Depends(deps.get_organization_id)
):
    service = PedigreeService(db)
    result = await service.get_descendants(individual_id, max_generations, organization_id)
    return {
        "success": True,
        **result
    }

@router.post("/pedigree/coancestry", response_model=CoancestryResponse)
async def calculate_coancestry(
    payload: CoancestryRequest,
    db: AsyncSession = Depends(deps.get_db),
    organization_id: int = Depends(deps.get_organization_id)
):
    service = PedigreeService(db)
    result = await service.calculate_coancestry(payload.individual_1, payload.individual_2, organization_id)
    return {
        "success": True,
        **result
    }

@router.post("/pedigree/relationship-matrix", response_model=RelationshipMatrixResponse)
async def get_relationship_matrix(
    payload: RelationshipMatrixRequest,
    db: AsyncSession = Depends(deps.get_db),
    organization_id: int = Depends(deps.get_organization_id)
):
    # Placeholder
    return {
        "success": True,
        "individuals": payload.individual_ids or [],
        "matrix": []
    }

# --- Standard BrAPI (Partial Implementation with Real Data) ---

def create_brapi_response(data, page, page_size, total_count):
    total_pages = max(1, (total_count + page_size - 1) // page_size)
    return {
        "metadata": {
            "datafiles": [],
            "pagination": {
                "currentPage": page,
                "pageSize": page_size,
                "totalCount": total_count,
                "totalPages": total_pages
            },
            "status": [{"message": "Success", "messageType": "INFO"}]
        },
        "result": {"data": data}
    }

@router.get("/pedigree")
async def get_pedigree_brapi(
    page: int = Query(0, ge=0),
    pageSize: int = Query(1000, ge=1, le=2000),
    germplasmDbId: Optional[str] = Query(None, description="Filter by germplasm DbId"),
    db: AsyncSession = Depends(deps.get_db),
    organization_id: int = Depends(deps.get_organization_id)
):
    """
    Get pedigree information (BrAPI format)
    """
    service = PedigreeService(db)

    # Use service pagination and filtering
    individuals, total_count = await service.get_individuals(
        page=page,
        page_size=pageSize,
        organization_id=organization_id,
        germplasm_db_id=germplasmDbId
    )

    # Transform to BrAPI format (PedigreeNode)
    data = []
    for ind in individuals:
        node = {
            "germplasmDbId": ind["id"],
            "germplasmName": ind["id"],
            "parents": []
        }
        if ind["sire_id"]:
            node["parents"].append({"germplasmDbId": ind["sire_id"], "parentType": "MALE"})
        if ind["dam_id"]:
            node["parents"].append({"germplasmDbId": ind["dam_id"], "parentType": "FEMALE"})
        data.append(node)

    return create_brapi_response(data, page, pageSize, total_count)

@router.post("/pedigree")
async def create_pedigree_brapi(
    pedigrees: List[PedigreeCreate],
    db: AsyncSession = Depends(deps.get_db),
    organization_id: int = Depends(deps.get_organization_id)
):
    """
    Create new pedigree entries (BrAPI format)
    """
    service = PedigreeService(db)

    # Convert to load format
    load_data = []
    for ped in pedigrees:
        sire = None
        dam = None
        for p in ped.parents:
            if p.get("parentType") == "MALE":
                sire = p.get("germplasmDbId")
            elif p.get("parentType") == "FEMALE":
                dam = p.get("germplasmDbId")

        load_data.append({
            "id": ped.germplasmDbId,
            "sire_id": sire,
            "dam_id": dam
        })

    result = await service.load_pedigree(load_data, organization_id)

    # Return count
    return create_brapi_response([], 0, 0, len(load_data)) # Simplified response
