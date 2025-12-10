"""
BrAPI v2.1 Observation Variables Endpoints
Aliases to traits for BrAPI compliance
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.core.database import get_db
from app.api.deps import get_current_user, get_optional_user

router = APIRouter()

_variables_store: dict = {}
_variables_counter = 0


class VariableBase(BaseModel):
    observationVariableName: str
    traitName: Optional[str] = None
    traitDescription: Optional[str] = None
    traitClass: Optional[str] = None
    methodName: Optional[str] = None
    methodDescription: Optional[str] = None
    scaleName: Optional[str] = None
    scaleDataType: Optional[str] = None
    scaleValidValueMin: Optional[float] = None
    scaleValidValueMax: Optional[float] = None
    defaultValue: Optional[str] = None
    ontologyReference: Optional[dict] = None


class VariableCreate(VariableBase):
    pass


def _init_demo_data():
    global _variables_counter
    if _variables_store:
        return
    
    demo_variables = [
        {
            "observationVariableName": "Plant Height",
            "trait": {"traitName": "Plant Height", "traitClass": "Morphological", "traitDescription": "Height of the plant from ground to tip"},
            "method": {"methodName": "Measurement", "methodDescription": "Direct measurement with ruler"},
            "scale": {"scaleName": "cm", "scaleDataType": "Numerical", "validValueMin": 0, "validValueMax": 300}
        },
        {
            "observationVariableName": "Days to Flowering",
            "trait": {"traitName": "Days to Flowering", "traitClass": "Phenological", "traitDescription": "Days from sowing to 50% flowering"},
            "method": {"methodName": "Counting", "methodDescription": "Count days from sowing"},
            "scale": {"scaleName": "days", "scaleDataType": "Numerical", "validValueMin": 0, "validValueMax": 200}
        },
        {
            "observationVariableName": "Grain Yield",
            "trait": {"traitName": "Grain Yield", "traitClass": "Agronomic", "traitDescription": "Total grain yield per hectare"},
            "method": {"methodName": "Weighing", "methodDescription": "Harvest and weigh grain"},
            "scale": {"scaleName": "kg/ha", "scaleDataType": "Numerical", "validValueMin": 0, "validValueMax": 15000}
        },
        {
            "observationVariableName": "1000 Grain Weight",
            "trait": {"traitName": "1000 Grain Weight", "traitClass": "Agronomic", "traitDescription": "Weight of 1000 grains"},
            "method": {"methodName": "Weighing", "methodDescription": "Count and weigh 1000 grains"},
            "scale": {"scaleName": "g", "scaleDataType": "Numerical", "validValueMin": 0, "validValueMax": 100}
        },
        {
            "observationVariableName": "Leaf Color",
            "trait": {"traitName": "Leaf Color", "traitClass": "Morphological", "traitDescription": "Visual assessment of leaf color"},
            "method": {"methodName": "Visual", "methodDescription": "Visual scoring using color chart"},
            "scale": {"scaleName": "1-5 scale", "scaleDataType": "Ordinal"}
        },
        {
            "observationVariableName": "Disease Resistance",
            "trait": {"traitName": "Disease Resistance", "traitClass": "Biotic Stress", "traitDescription": "Resistance to major diseases"},
            "method": {"methodName": "Scoring", "methodDescription": "Score disease symptoms"},
            "scale": {"scaleName": "1-9 scale", "scaleDataType": "Ordinal"}
        },
        {
            "observationVariableName": "Drought Tolerance",
            "trait": {"traitName": "Drought Tolerance", "traitClass": "Abiotic Stress", "traitDescription": "Tolerance to water stress"},
            "method": {"methodName": "Scoring", "methodDescription": "Score plant recovery after stress"},
            "scale": {"scaleName": "1-9 scale", "scaleDataType": "Ordinal"}
        },
        {
            "observationVariableName": "Protein Content",
            "trait": {"traitName": "Protein Content", "traitClass": "Quality", "traitDescription": "Grain protein percentage"},
            "method": {"methodName": "NIR Analysis", "methodDescription": "Near-infrared spectroscopy"},
            "scale": {"scaleName": "%", "scaleDataType": "Numerical", "validValueMin": 0, "validValueMax": 25}
        },
    ]
    
    for v in demo_variables:
        _variables_counter += 1
        vid = f"var_{_variables_counter}"
        _variables_store[vid] = {"observationVariableDbId": vid, **v}


@router.get("/variables")
async def list_variables(
    page: int = Query(0, ge=0),
    pageSize: int = Query(20, ge=1, le=1000),
    traitClass: Optional[str] = None,
    observationVariableName: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_optional_user),
):
    """Get list of observation variables"""
    _init_demo_data()
    
    results = list(_variables_store.values())
    
    if traitClass:
        results = [v for v in results if traitClass.lower() in v.get("trait", {}).get("traitClass", "").lower()]
    if observationVariableName:
        results = [v for v in results if observationVariableName.lower() in v.get("observationVariableName", "").lower()]
    
    total = len(results)
    start = page * pageSize
    paginated = results[start:start + pageSize]
    
    return {
        "metadata": {"datafiles": [], "pagination": {"currentPage": page, "pageSize": pageSize, "totalCount": total, "totalPages": (total + pageSize - 1) // pageSize}, "status": [{"message": "Request successful", "messageType": "INFO"}]},
        "result": {"data": paginated}
    }


@router.post("/variables")
async def create_variable(variable: VariableCreate, db: AsyncSession = Depends(get_db), current_user = Depends(get_current_user)):
    """Create new observation variable"""
    global _variables_counter
    _init_demo_data()
    
    _variables_counter += 1
    vid = f"var_{_variables_counter}"
    new_var = {"observationVariableDbId": vid, **variable.model_dump()}
    _variables_store[vid] = new_var
    
    return {"metadata": {"datafiles": [], "pagination": {"currentPage": 0, "pageSize": 1, "totalCount": 1, "totalPages": 1}, "status": []}, "result": new_var}


@router.get("/variables/{observationVariableDbId}")
async def get_variable(observationVariableDbId: str, db: AsyncSession = Depends(get_db), current_user = Depends(get_optional_user)):
    """Get observation variable by ID"""
    _init_demo_data()
    if observationVariableDbId not in _variables_store:
        raise HTTPException(status_code=404, detail="Observation variable not found")
    return {"metadata": {"datafiles": [], "pagination": {"currentPage": 0, "pageSize": 1, "totalCount": 1, "totalPages": 1}, "status": []}, "result": _variables_store[observationVariableDbId]}


@router.put("/variables/{observationVariableDbId}")
async def update_variable(observationVariableDbId: str, variable: VariableCreate, db: AsyncSession = Depends(get_db), current_user = Depends(get_current_user)):
    """Update observation variable"""
    _init_demo_data()
    if observationVariableDbId not in _variables_store:
        raise HTTPException(status_code=404, detail="Observation variable not found")
    
    _variables_store[observationVariableDbId].update(variable.model_dump())
    return {"metadata": {"datafiles": [], "pagination": {"currentPage": 0, "pageSize": 1, "totalCount": 1, "totalPages": 1}, "status": []}, "result": _variables_store[observationVariableDbId]}


@router.delete("/variables/{observationVariableDbId}")
async def delete_variable(observationVariableDbId: str, db: AsyncSession = Depends(get_db), current_user = Depends(get_current_user)):
    """Delete observation variable"""
    _init_demo_data()
    if observationVariableDbId not in _variables_store:
        raise HTTPException(status_code=404, detail="Observation variable not found")
    
    del _variables_store[observationVariableDbId]
    return {"metadata": {"datafiles": [], "pagination": {"currentPage": 0, "pageSize": 0, "totalCount": 0, "totalPages": 0}, "status": [{"message": "Variable deleted", "messageType": "INFO"}]}, "result": None}
