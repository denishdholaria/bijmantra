"""
BrAPI v2.1 Germplasm Endpoints
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from datetime import datetime

from app.core.database import get_db
from app.api.deps import get_current_user, get_organization_id

router = APIRouter()

# In-memory storage for demo (replace with database in production)
_germplasm_store: dict = {}
_germplasm_counter = 0


class GermplasmBase(BaseModel):
    germplasmName: str
    accessionNumber: Optional[str] = None
    germplasmPUI: Optional[str] = None
    defaultDisplayName: Optional[str] = None
    species: Optional[str] = None
    genus: Optional[str] = None
    subtaxa: Optional[str] = None
    commonCropName: Optional[str] = None
    instituteCode: Optional[str] = None
    instituteName: Optional[str] = None
    biologicalStatusOfAccessionCode: Optional[str] = None
    countryOfOriginCode: Optional[str] = None
    synonyms: Optional[List[str]] = []
    pedigree: Optional[str] = None
    seedSource: Optional[str] = None
    seedSourceDescription: Optional[str] = None


class GermplasmCreate(GermplasmBase):
    pass


class Germplasm(GermplasmBase):
    germplasmDbId: str
    
    class Config:
        from_attributes = True


class BrAPIResponse(BaseModel):
    metadata: dict
    result: dict


def _init_demo_data():
    """Initialize demo germplasm data"""
    global _germplasm_counter
    if _germplasm_store:
        return
    
    demo_germplasm = [
        {"germplasmName": "IR64", "species": "Oryza sativa", "genus": "Oryza", "commonCropName": "Rice", "countryOfOriginCode": "PHL", "accessionNumber": "IRRI-001"},
        {"germplasmName": "Swarna", "species": "Oryza sativa", "genus": "Oryza", "commonCropName": "Rice", "countryOfOriginCode": "IND", "accessionNumber": "CRRI-001"},
        {"germplasmName": "HD2967", "species": "Triticum aestivum", "genus": "Triticum", "commonCropName": "Wheat", "countryOfOriginCode": "IND", "accessionNumber": "IARI-001"},
        {"germplasmName": "PBW343", "species": "Triticum aestivum", "genus": "Triticum", "commonCropName": "Wheat", "countryOfOriginCode": "IND", "accessionNumber": "PAU-001"},
        {"germplasmName": "DH86", "species": "Zea mays", "genus": "Zea", "commonCropName": "Maize", "countryOfOriginCode": "IND", "accessionNumber": "DMR-001"},
        {"germplasmName": "Pusa Basmati 1121", "species": "Oryza sativa", "genus": "Oryza", "commonCropName": "Rice", "countryOfOriginCode": "IND", "accessionNumber": "IARI-002"},
        {"germplasmName": "Kalyan Sona", "species": "Triticum aestivum", "genus": "Triticum", "commonCropName": "Wheat", "countryOfOriginCode": "IND", "accessionNumber": "IARI-003"},
        {"germplasmName": "Sharbati", "species": "Triticum aestivum", "genus": "Triticum", "commonCropName": "Wheat", "countryOfOriginCode": "IND", "accessionNumber": "MP-001"},
    ]
    
    for g in demo_germplasm:
        _germplasm_counter += 1
        gid = f"germplasm_{_germplasm_counter}"
        _germplasm_store[gid] = {
            "germplasmDbId": gid,
            **g,
            "synonyms": [],
            "pedigree": None,
            "seedSource": None,
        }


@router.get("/germplasm")
async def list_germplasm(
    page: int = Query(0, ge=0),
    pageSize: int = Query(20, ge=1, le=1000),
    germplasmName: Optional[str] = None,
    commonCropName: Optional[str] = None,
    species: Optional[str] = None,
    genus: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """Get list of germplasm"""
    _init_demo_data()
    
    # Filter germplasm
    results = list(_germplasm_store.values())
    
    if germplasmName:
        results = [g for g in results if germplasmName.lower() in g.get("germplasmName", "").lower()]
    if commonCropName:
        results = [g for g in results if commonCropName.lower() in g.get("commonCropName", "").lower()]
    if species:
        results = [g for g in results if species.lower() in g.get("species", "").lower()]
    if genus:
        results = [g for g in results if genus.lower() in g.get("genus", "").lower()]
    
    total = len(results)
    start = page * pageSize
    end = start + pageSize
    paginated = results[start:end]
    
    return {
        "metadata": {
            "datafiles": [],
            "pagination": {
                "currentPage": page,
                "pageSize": pageSize,
                "totalCount": total,
                "totalPages": (total + pageSize - 1) // pageSize
            },
            "status": [{"message": "Request successful", "messageType": "INFO"}]
        },
        "result": {
            "data": paginated
        }
    }


@router.post("/germplasm")
async def create_germplasm(
    germplasm: GermplasmCreate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """Create new germplasm"""
    global _germplasm_counter
    _init_demo_data()
    
    _germplasm_counter += 1
    gid = f"germplasm_{_germplasm_counter}"
    
    new_germplasm = {
        "germplasmDbId": gid,
        **germplasm.model_dump()
    }
    _germplasm_store[gid] = new_germplasm
    
    return {
        "metadata": {
            "datafiles": [],
            "pagination": {"currentPage": 0, "pageSize": 1, "totalCount": 1, "totalPages": 1},
            "status": [{"message": "Germplasm created successfully", "messageType": "INFO"}]
        },
        "result": new_germplasm
    }


@router.get("/germplasm/{germplasmDbId}")
async def get_germplasm(
    germplasmDbId: str,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """Get germplasm by ID"""
    _init_demo_data()
    
    if germplasmDbId not in _germplasm_store:
        raise HTTPException(status_code=404, detail="Germplasm not found")
    
    return {
        "metadata": {
            "datafiles": [],
            "pagination": {"currentPage": 0, "pageSize": 1, "totalCount": 1, "totalPages": 1},
            "status": [{"message": "Request successful", "messageType": "INFO"}]
        },
        "result": _germplasm_store[germplasmDbId]
    }


@router.put("/germplasm/{germplasmDbId}")
async def update_germplasm(
    germplasmDbId: str,
    germplasm: GermplasmCreate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """Update germplasm"""
    _init_demo_data()
    
    if germplasmDbId not in _germplasm_store:
        raise HTTPException(status_code=404, detail="Germplasm not found")
    
    _germplasm_store[germplasmDbId].update(germplasm.model_dump())
    
    return {
        "metadata": {
            "datafiles": [],
            "pagination": {"currentPage": 0, "pageSize": 1, "totalCount": 1, "totalPages": 1},
            "status": [{"message": "Germplasm updated successfully", "messageType": "INFO"}]
        },
        "result": _germplasm_store[germplasmDbId]
    }


@router.delete("/germplasm/{germplasmDbId}")
async def delete_germplasm(
    germplasmDbId: str,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """Delete germplasm"""
    _init_demo_data()
    
    if germplasmDbId not in _germplasm_store:
        raise HTTPException(status_code=404, detail="Germplasm not found")
    
    del _germplasm_store[germplasmDbId]
    
    return {
        "metadata": {
            "datafiles": [],
            "pagination": {"currentPage": 0, "pageSize": 0, "totalCount": 0, "totalPages": 0},
            "status": [{"message": "Germplasm deleted successfully", "messageType": "INFO"}]
        },
        "result": None
    }
