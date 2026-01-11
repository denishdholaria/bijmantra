"""
BrAPI Core - Pedigree endpoints
GET/POST/PUT /pedigree - Pedigree information
"""

from typing import List, Optional
from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel
from datetime import datetime
import uuid

router = APIRouter()


# In-memory storage for demo
PEDIGREE_DB = {}


class PedigreeNode(BaseModel):
    """Pedigree node representing a germplasm and its parents"""
    germplasmDbId: str
    germplasmName: Optional[str] = None
    pedigreeString: Optional[str] = None
    crossingProjectDbId: Optional[str] = None
    crossingYear: Optional[int] = None
    familyCode: Optional[str] = None
    breedingMethodDbId: Optional[str] = None
    breedingMethodName: Optional[str] = None
    parents: List[dict] = []  # List of {germplasmDbId, germplasmName, parentType}
    siblings: List[dict] = []
    progeny: List[dict] = []
    externalReferences: List[dict] = []
    additionalInfo: dict = {}


class PedigreeCreate(BaseModel):
    """Create pedigree entry"""
    germplasmDbId: str
    germplasmName: Optional[str] = None
    pedigreeString: Optional[str] = None
    crossingProjectDbId: Optional[str] = None
    crossingYear: Optional[int] = None
    familyCode: Optional[str] = None
    breedingMethodDbId: Optional[str] = None
    breedingMethodName: Optional[str] = None
    parents: List[dict] = []
    externalReferences: List[dict] = []
    additionalInfo: dict = {}


class PedigreeUpdate(BaseModel):
    """Update pedigree entry"""
    germplasmDbId: str
    germplasmName: Optional[str] = None
    pedigreeString: Optional[str] = None
    crossingProjectDbId: Optional[str] = None
    crossingYear: Optional[int] = None
    familyCode: Optional[str] = None
    breedingMethodDbId: Optional[str] = None
    breedingMethodName: Optional[str] = None
    parents: Optional[List[dict]] = None
    externalReferences: Optional[List[dict]] = None
    additionalInfo: Optional[dict] = None


def create_response(data, page=0, page_size=1000, total_count=1):
    """Helper to create BrAPI response"""
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
        "result": data
    }


# Initialize demo data
def init_demo_data():
    if not PEDIGREE_DB:
        demo_pedigrees = [
            {
                "germplasmDbId": "germ-001",
                "germplasmName": "IR64",
                "pedigreeString": "IR5657-33-2-1/IR2061-465-1-5-5",
                "crossingYear": 1985,
                "breedingMethodName": "Single Seed Descent",
                "parents": [
                    {"germplasmDbId": "germ-p1", "germplasmName": "IR5657-33-2-1", "parentType": "FEMALE"},
                    {"germplasmDbId": "germ-p2", "germplasmName": "IR2061-465-1-5-5", "parentType": "MALE"}
                ]
            },
            {
                "germplasmDbId": "germ-002",
                "germplasmName": "Swarna",
                "pedigreeString": "Vasistha/Mahsuri",
                "crossingYear": 1979,
                "breedingMethodName": "Pedigree Selection",
                "parents": [
                    {"germplasmDbId": "germ-p3", "germplasmName": "Vasistha", "parentType": "FEMALE"},
                    {"germplasmDbId": "germ-p4", "germplasmName": "Mahsuri", "parentType": "MALE"}
                ]
            },
            {
                "germplasmDbId": "germ-003",
                "germplasmName": "MTU1010",
                "pedigreeString": "Krishnaveni/IR64",
                "crossingYear": 2000,
                "breedingMethodName": "Backcross",
                "parents": [
                    {"germplasmDbId": "germ-p5", "germplasmName": "Krishnaveni", "parentType": "FEMALE"},
                    {"germplasmDbId": "germ-001", "germplasmName": "IR64", "parentType": "MALE"}
                ]
            },
        ]
        for ped in demo_pedigrees:
            PEDIGREE_DB[ped["germplasmDbId"]] = PedigreeNode(**ped)


init_demo_data()


@router.get("/pedigree")
async def get_pedigree(
    page: int = Query(0, ge=0),
    pageSize: int = Query(1000, ge=1, le=2000),
    germplasmDbId: Optional[str] = Query(None, description="Filter by germplasm DbId"),
    germplasmName: Optional[str] = Query(None, description="Filter by germplasm name"),
    pedigreeDepth: int = Query(1, ge=0, le=10, description="Depth of pedigree to return"),
    progenyDepth: int = Query(0, ge=0, le=10, description="Depth of progeny to return"),
    includeParents: bool = Query(True, description="Include parent information"),
    includeSiblings: bool = Query(False, description="Include sibling information"),
    includeProgeny: bool = Query(False, description="Include progeny information"),
    includeFullTree: bool = Query(False, description="Include full pedigree tree"),
):
    """
    Get pedigree information
    
    BrAPI Endpoint: GET /pedigree
    """
    # Filter pedigrees
    filtered = list(PEDIGREE_DB.values())
    
    if germplasmDbId:
        filtered = [p for p in filtered if p.germplasmDbId == germplasmDbId]
    if germplasmName:
        filtered = [p for p in filtered if germplasmName.lower() in (p.germplasmName or "").lower()]
    
    # Paginate
    total_count = len(filtered)
    start = page * pageSize
    end = start + pageSize
    paginated = filtered[start:end]
    
    # Build response data
    result_data = []
    for ped in paginated:
        node = ped.model_dump()
        if not includeParents:
            node["parents"] = []
        if not includeSiblings:
            node["siblings"] = []
        if not includeProgeny:
            node["progeny"] = []
        result_data.append(node)
    
    return create_response({"data": result_data}, page, pageSize, total_count)


@router.post("/pedigree", status_code=201)
async def create_pedigree(pedigrees: List[PedigreeCreate]):
    """
    Create new pedigree entries
    
    BrAPI Endpoint: POST /pedigree
    """
    created = []
    for ped_in in pedigrees:
        new_ped = PedigreeNode(
            germplasmDbId=ped_in.germplasmDbId,
            germplasmName=ped_in.germplasmName,
            pedigreeString=ped_in.pedigreeString,
            crossingProjectDbId=ped_in.crossingProjectDbId,
            crossingYear=ped_in.crossingYear,
            familyCode=ped_in.familyCode,
            breedingMethodDbId=ped_in.breedingMethodDbId,
            breedingMethodName=ped_in.breedingMethodName,
            parents=ped_in.parents,
            externalReferences=ped_in.externalReferences,
            additionalInfo=ped_in.additionalInfo
        )
        PEDIGREE_DB[ped_in.germplasmDbId] = new_ped
        created.append(new_ped.model_dump())
    
    return create_response({"data": created}, total_count=len(created))


@router.put("/pedigree")
async def update_pedigree(pedigrees: List[PedigreeUpdate]):
    """
    Update existing pedigree entries
    
    BrAPI Endpoint: PUT /pedigree
    """
    updated = []
    for ped_in in pedigrees:
        if ped_in.germplasmDbId not in PEDIGREE_DB:
            # Create new if doesn't exist
            new_ped = PedigreeNode(
                germplasmDbId=ped_in.germplasmDbId,
                germplasmName=ped_in.germplasmName,
                pedigreeString=ped_in.pedigreeString,
                crossingProjectDbId=ped_in.crossingProjectDbId,
                crossingYear=ped_in.crossingYear,
                familyCode=ped_in.familyCode,
                breedingMethodDbId=ped_in.breedingMethodDbId,
                breedingMethodName=ped_in.breedingMethodName,
                parents=ped_in.parents or [],
                externalReferences=ped_in.externalReferences or [],
                additionalInfo=ped_in.additionalInfo or {}
            )
            PEDIGREE_DB[ped_in.germplasmDbId] = new_ped
        else:
            existing = PEDIGREE_DB[ped_in.germplasmDbId]
            update_data = ped_in.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                if value is not None:
                    setattr(existing, field, value)
        
        updated.append(PEDIGREE_DB[ped_in.germplasmDbId].model_dump())
    
    return create_response({"data": updated}, total_count=len(updated))
