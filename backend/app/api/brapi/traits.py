"""
BrAPI v2.1 Traits/Observation Variables Endpoints
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.core.database import get_db
from app.api.deps import get_current_user, get_optional_user

router = APIRouter()

_traits_store: dict = {}
_traits_counter = 0


class TraitBase(BaseModel):
    observationVariableName: str
    traitName: Optional[str] = None
    traitDescription: Optional[str] = None
    traitClass: Optional[str] = None  # Agronomic, Morphological, Physiological, etc.
    methodName: Optional[str] = None
    methodDescription: Optional[str] = None
    scaleName: Optional[str] = None
    scaleDataType: Optional[str] = None  # Numerical, Ordinal, Nominal, Date, Text
    scaleValidValueMin: Optional[float] = None
    scaleValidValueMax: Optional[float] = None
    defaultValue: Optional[str] = None
    ontologyReference: Optional[dict] = None


class TraitCreate(TraitBase):
    pass


def _init_demo_data():
    global _traits_counter
    if _traits_store:
        return
    
    demo_traits = [
        {"observationVariableName": "Plant Height", "traitName": "Plant Height", "traitClass": "Morphological", "methodName": "Measurement", "scaleName": "cm", "scaleDataType": "Numerical", "scaleValidValueMin": 0, "scaleValidValueMax": 300},
        {"observationVariableName": "Days to Flowering", "traitName": "Days to Flowering", "traitClass": "Phenological", "methodName": "Counting", "scaleName": "days", "scaleDataType": "Numerical", "scaleValidValueMin": 0, "scaleValidValueMax": 200},
        {"observationVariableName": "Grain Yield", "traitName": "Grain Yield", "traitClass": "Agronomic", "methodName": "Weighing", "scaleName": "kg/ha", "scaleDataType": "Numerical", "scaleValidValueMin": 0, "scaleValidValueMax": 15000},
        {"observationVariableName": "1000 Grain Weight", "traitName": "1000 Grain Weight", "traitClass": "Agronomic", "methodName": "Weighing", "scaleName": "g", "scaleDataType": "Numerical", "scaleValidValueMin": 0, "scaleValidValueMax": 100},
        {"observationVariableName": "Leaf Color", "traitName": "Leaf Color", "traitClass": "Morphological", "methodName": "Visual", "scaleName": "1-5 scale", "scaleDataType": "Ordinal"},
        {"observationVariableName": "Disease Resistance", "traitName": "Disease Resistance", "traitClass": "Biotic Stress", "methodName": "Scoring", "scaleName": "1-9 scale", "scaleDataType": "Ordinal"},
        {"observationVariableName": "Drought Tolerance", "traitName": "Drought Tolerance", "traitClass": "Abiotic Stress", "methodName": "Scoring", "scaleName": "1-9 scale", "scaleDataType": "Ordinal"},
        {"observationVariableName": "Protein Content", "traitName": "Protein Content", "traitClass": "Quality", "methodName": "NIR Analysis", "scaleName": "%", "scaleDataType": "Numerical", "scaleValidValueMin": 0, "scaleValidValueMax": 25},
    ]
    
    for t in demo_traits:
        _traits_counter += 1
        tid = f"trait_{_traits_counter}"
        _traits_store[tid] = {"observationVariableDbId": tid, **t}


@router.get("/traits")
async def list_traits(
    page: int = Query(0, ge=0),
    pageSize: int = Query(20, ge=1, le=1000),
    traitClass: Optional[str] = None,
    observationVariableName: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_optional_user),
):
    """Get list of traits/observation variables"""
    _init_demo_data()
    
    results = list(_traits_store.values())
    
    if traitClass:
        results = [t for t in results if traitClass.lower() in t.get("traitClass", "").lower()]
    if observationVariableName:
        results = [t for t in results if observationVariableName.lower() in t.get("observationVariableName", "").lower()]
    
    total = len(results)
    start = page * pageSize
    paginated = results[start:start + pageSize]
    
    return {
        "metadata": {"datafiles": [], "pagination": {"currentPage": page, "pageSize": pageSize, "totalCount": total, "totalPages": (total + pageSize - 1) // pageSize}, "status": [{"message": "Request successful", "messageType": "INFO"}]},
        "result": {"data": paginated}
    }


@router.post("/traits")
async def create_trait(trait: TraitCreate, db: AsyncSession = Depends(get_db), current_user = Depends(get_current_user)):
    """Create new trait"""
    global _traits_counter
    _init_demo_data()
    
    _traits_counter += 1
    tid = f"trait_{_traits_counter}"
    new_trait = {"observationVariableDbId": tid, **trait.model_dump()}
    _traits_store[tid] = new_trait
    
    return {"metadata": {"datafiles": [], "pagination": {"currentPage": 0, "pageSize": 1, "totalCount": 1, "totalPages": 1}, "status": []}, "result": new_trait}


@router.get("/traits/{observationVariableDbId}")
async def get_trait(observationVariableDbId: str, db: AsyncSession = Depends(get_db), current_user = Depends(get_optional_user)):
    """Get trait by ID"""
    _init_demo_data()
    if observationVariableDbId not in _traits_store:
        raise HTTPException(status_code=404, detail="Trait not found")
    return {"metadata": {"datafiles": [], "pagination": {"currentPage": 0, "pageSize": 1, "totalCount": 1, "totalPages": 1}, "status": []}, "result": _traits_store[observationVariableDbId]}
