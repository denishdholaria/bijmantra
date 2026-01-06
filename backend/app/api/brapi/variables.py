"""
BrAPI v2.1 Observation Variables Endpoints

Database-backed implementation (no in-memory demo data).
Demo data is seeded into Demo Organization via seeders.

GOVERNANCE.md §4.3.1 Compliant: Fully async implementation.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pydantic import BaseModel
import uuid

from app.core.database import get_db
from app.api.deps import get_current_user, get_optional_user
from app.models.phenotyping import ObservationVariable

router = APIRouter()


class VariableBase(BaseModel):
    observationVariableName: str
    commonCropName: Optional[str] = None
    defaultValue: Optional[str] = None
    growthStage: Optional[str] = None
    institution: Optional[str] = None
    language: Optional[str] = None
    scientist: Optional[str] = None
    status: Optional[str] = None
    synonyms: Optional[List[str]] = None
    # Trait
    traitDbId: Optional[str] = None
    traitName: Optional[str] = None
    traitDescription: Optional[str] = None
    traitClass: Optional[str] = None
    # Method
    methodDbId: Optional[str] = None
    methodName: Optional[str] = None
    methodDescription: Optional[str] = None
    methodClass: Optional[str] = None
    formula: Optional[str] = None
    # Scale
    scaleDbId: Optional[str] = None
    scaleName: Optional[str] = None
    dataType: Optional[str] = None
    decimalPlaces: Optional[int] = None
    validValues: Optional[dict] = None
    # Ontology
    ontologyDbId: Optional[str] = None
    ontologyName: Optional[str] = None


class VariableCreate(VariableBase):
    pass


class VariableUpdate(VariableBase):
    observationVariableName: Optional[str] = None


def _model_to_brapi(var: ObservationVariable) -> dict:
    """Convert SQLAlchemy model to BrAPI response format"""
    return {
        "observationVariableDbId": var.observation_variable_db_id,
        "observationVariableName": var.observation_variable_name,
        "commonCropName": var.common_crop_name,
        "defaultValue": var.default_value,
        "growthStage": var.growth_stage,
        "institution": var.institution,
        "language": var.language,
        "scientist": var.scientist,
        "status": var.status,
        "submissionTimestamp": var.submission_timestamp,
        "synonyms": var.synonyms,
        "trait": {
            "traitDbId": var.trait_db_id,
            "traitName": var.trait_name,
            "traitDescription": var.trait_description,
            "traitClass": var.trait_class,
        } if var.trait_name else None,
        "method": {
            "methodDbId": var.method_db_id,
            "methodName": var.method_name,
            "methodDescription": var.method_description,
            "methodClass": var.method_class,
            "formula": var.formula,
        } if var.method_name else None,
        "scale": {
            "scaleDbId": var.scale_db_id,
            "scaleName": var.scale_name,
            "dataType": var.data_type,
            "decimalPlaces": var.decimal_places,
            "validValues": var.valid_values,
        } if var.scale_name else None,
        "ontologyReference": {
            "ontologyDbId": var.ontology_db_id,
            "ontologyName": var.ontology_name,
        } if var.ontology_name else None,
        "additionalInfo": var.additional_info,
        "externalReferences": var.external_references,
    }


@router.get("/variables")
async def list_variables(
    page: int = Query(0, ge=0),
    pageSize: int = Query(20, ge=1, le=1000),
    observationVariableDbId: Optional[str] = None,
    observationVariableName: Optional[str] = None,
    traitClass: Optional[str] = None,
    commonCropName: Optional[str] = None,
    methodDbId: Optional[str] = None,
    scaleDbId: Optional[str] = None,
    ontologyDbId: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_optional_user),
):
    """Get list of observation variables from database"""
    # Build base query
    stmt = select(ObservationVariable)
    
    # Apply filters
    if observationVariableDbId:
        stmt = stmt.where(ObservationVariable.observation_variable_db_id == observationVariableDbId)
    if observationVariableName:
        stmt = stmt.where(ObservationVariable.observation_variable_name.ilike(f"%{observationVariableName}%"))
    if traitClass:
        stmt = stmt.where(ObservationVariable.trait_class.ilike(f"%{traitClass}%"))
    if commonCropName:
        stmt = stmt.where(ObservationVariable.common_crop_name.ilike(f"%{commonCropName}%"))
    if methodDbId:
        stmt = stmt.where(ObservationVariable.method_db_id == methodDbId)
    if scaleDbId:
        stmt = stmt.where(ObservationVariable.scale_db_id == scaleDbId)
    if ontologyDbId:
        stmt = stmt.where(ObservationVariable.ontology_db_id == ontologyDbId)
    
    # Get total count
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total_result = await db.execute(count_stmt)
    total = total_result.scalar() or 0
    
    # Apply pagination
    stmt = stmt.offset(page * pageSize).limit(pageSize)
    
    # Execute query
    result = await db.execute(stmt)
    variables = result.scalars().all()
    data = [_model_to_brapi(v) for v in variables]
    
    return {
        "metadata": {
            "datafiles": [],
            "pagination": {
                "currentPage": page,
                "pageSize": pageSize,
                "totalCount": total,
                "totalPages": (total + pageSize - 1) // pageSize if total > 0 else 0
            },
            "status": [{"message": "Request successful", "messageType": "INFO"}]
        },
        "result": {"data": data}
    }


@router.post("/variables")
async def create_variable(
    variable: VariableCreate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Create new observation variable in database"""
    org_id = current_user.organization_id if current_user else 1
    var_db_id = f"var_{uuid.uuid4().hex[:12]}"
    
    new_var = ObservationVariable(
        organization_id=org_id,
        observation_variable_db_id=var_db_id,
        observation_variable_name=variable.observationVariableName,
        common_crop_name=variable.commonCropName,
        default_value=variable.defaultValue,
        growth_stage=variable.growthStage,
        institution=variable.institution,
        language=variable.language,
        scientist=variable.scientist,
        status=variable.status or "active",
        synonyms=variable.synonyms,
        trait_db_id=variable.traitDbId,
        trait_name=variable.traitName,
        trait_description=variable.traitDescription,
        trait_class=variable.traitClass,
        method_db_id=variable.methodDbId,
        method_name=variable.methodName,
        method_description=variable.methodDescription,
        method_class=variable.methodClass,
        formula=variable.formula,
        scale_db_id=variable.scaleDbId,
        scale_name=variable.scaleName,
        data_type=variable.dataType,
        decimal_places=variable.decimalPlaces,
        valid_values=variable.validValues,
        ontology_db_id=variable.ontologyDbId,
        ontology_name=variable.ontologyName,
    )
    
    db.add(new_var)
    await db.commit()
    await db.refresh(new_var)
    
    return {
        "metadata": {
            "datafiles": [],
            "pagination": {"currentPage": 0, "pageSize": 1, "totalCount": 1, "totalPages": 1},
            "status": [{"message": "Variable created successfully", "messageType": "INFO"}]
        },
        "result": _model_to_brapi(new_var)
    }


@router.get("/variables/{observationVariableDbId}")
async def get_variable(
    observationVariableDbId: str,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_optional_user)
):
    """Get observation variable by ID from database"""
    stmt = select(ObservationVariable).where(
        ObservationVariable.observation_variable_db_id == observationVariableDbId
    )
    result = await db.execute(stmt)
    var = result.scalar_one_or_none()
    
    if not var:
        raise HTTPException(status_code=404, detail="Observation variable not found")
    
    return {
        "metadata": {
            "datafiles": [],
            "pagination": {"currentPage": 0, "pageSize": 1, "totalCount": 1, "totalPages": 1},
            "status": []
        },
        "result": _model_to_brapi(var)
    }


@router.put("/variables/{observationVariableDbId}")
async def update_variable(
    observationVariableDbId: str,
    variable: VariableUpdate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """Update observation variable"""
    stmt = select(ObservationVariable).where(
        ObservationVariable.observation_variable_db_id == observationVariableDbId
    )
    result = await db.execute(stmt)
    var = result.scalar_one_or_none()
    
    if not var:
        raise HTTPException(status_code=404, detail="Observation variable not found")
    
    # Update fields if provided
    if variable.observationVariableName:
        var.observation_variable_name = variable.observationVariableName
    if variable.commonCropName:
        var.common_crop_name = variable.commonCropName
    if variable.traitName:
        var.trait_name = variable.traitName
    if variable.traitDescription:
        var.trait_description = variable.traitDescription
    if variable.traitClass:
        var.trait_class = variable.traitClass
    if variable.methodName:
        var.method_name = variable.methodName
    if variable.methodDescription:
        var.method_description = variable.methodDescription
    if variable.scaleName:
        var.scale_name = variable.scaleName
    if variable.dataType:
        var.data_type = variable.dataType
    if variable.status:
        var.status = variable.status
    
    await db.commit()
    await db.refresh(var)
    
    return {
        "metadata": {
            "datafiles": [],
            "pagination": {"currentPage": 0, "pageSize": 1, "totalCount": 1, "totalPages": 1},
            "status": [{"message": "Variable updated successfully", "messageType": "INFO"}]
        },
        "result": _model_to_brapi(var)
    }


@router.delete("/variables/{observationVariableDbId}")
async def delete_variable(
    observationVariableDbId: str,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """Delete observation variable"""
    stmt = select(ObservationVariable).where(
        ObservationVariable.observation_variable_db_id == observationVariableDbId
    )
    result = await db.execute(stmt)
    var = result.scalar_one_or_none()
    
    if not var:
        raise HTTPException(status_code=404, detail="Observation variable not found")
    
    await db.delete(var)
    await db.commit()
    
    return {
        "metadata": {
            "datafiles": [],
            "pagination": {"currentPage": 0, "pageSize": 1, "totalCount": 1, "totalPages": 1},
            "status": [{"message": "Variable deleted successfully", "messageType": "INFO"}]
        },
        "result": {"observationVariableDbId": observationVariableDbId}
    }
