"""
BrAPI v2.1 Traits/Observation Variables Endpoints

Database-backed implementation (no in-memory demo data).
Demo data is seeded into Demo Organization via seeders.
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


class TraitBase(BaseModel):
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
    commonCropName: Optional[str] = None
    status: Optional[str] = None


class TraitCreate(TraitBase):
    pass


def _model_to_brapi(var: ObservationVariable) -> dict:
    """Convert an ObservationVariable SQLAlchemy model to a BrAPI-compliant dictionary.

    Args:
        var (ObservationVariable): The ObservationVariable SQLAlchemy model instance.

    Returns:
        A dictionary formatted according to the BrAPI v2.1 specification for an
        observation variable.
    """
    valid_values = var.valid_values or {}
    return {
        "observationVariableDbId": var.observation_variable_db_id,
        "observationVariableName": var.observation_variable_name,
        "traitName": var.trait_name,
        "traitDescription": var.trait_description,
        "traitClass": var.trait_class,
        "methodName": var.method_name,
        "methodDescription": var.method_description,
        "scaleName": var.scale_name,
        "scaleDataType": var.data_type,
        "scaleValidValueMin": valid_values.get("min"),
        "scaleValidValueMax": valid_values.get("max"),
        "defaultValue": var.default_value,
        "commonCropName": var.common_crop_name,
        "status": var.status,
        "additionalInfo": var.additional_info,
        "externalReferences": var.external_references,
    }


@router.get("/traits")
async def list_traits(
    page: int = Query(0, ge=0),
    pageSize: int = Query(20, ge=1, le=1000),
    traitClass: Optional[str] = None,
    observationVariableName: Optional[str] = None,
    commonCropName: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_optional_user),
):
    """Retrieves a paginated list of traits, with optional filtering.

    Args:
        page (int): The page number to retrieve.
        pageSize (int): The number of items per page.
        traitClass (Optional[str]): An optional filter for the trait class.
        observationVariableName (Optional[str]): An optional filter for the observation variable name.
        commonCropName (Optional[str]): An optional filter for the common crop name.
        db (AsyncSession): The SQLAlchemy asynchronous session.
        current_user: The authenticated user, if any.

    Returns:
        A BrAPI-compliant response containing a list of traits and pagination metadata.
    """
    # Build query
    query = select(ObservationVariable)

    # Filter by user's organization (multi-tenant isolation)
    if current_user and current_user.organization_id:
        query = query.where(ObservationVariable.organization_id == current_user.organization_id)

    # Apply filters
    if traitClass:
        query = query.where(ObservationVariable.trait_class.ilike(f"%{traitClass}%"))
    if observationVariableName:
        query = query.where(ObservationVariable.observation_variable_name.ilike(f"%{observationVariableName}%"))
    if commonCropName:
        query = query.where(ObservationVariable.common_crop_name.ilike(f"%{commonCropName}%"))

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Paginate
    query = query.offset(page * pageSize).limit(pageSize)
    result = await db.execute(query)
    results = result.scalars().all()

    # Convert to BrAPI format
    data = [_model_to_brapi(var) for var in results]

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


@router.post("/traits")
async def create_trait(
    trait: TraitCreate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Creates a new trait in the database.

    Args:
        trait (TraitCreate): A `TraitCreate` model containing the new trait's data.
        db (AsyncSession): The SQLAlchemy asynchronous session.
        current_user: The authenticated user.

    Returns:
        A BrAPI-compliant response containing the newly created trait.
    """
    # Get organization from current user
    org_id = current_user.organization_id if current_user else 1

    # Generate unique ID
    var_db_id = f"var_{uuid.uuid4().hex[:12]}"

    # Build valid_values dict
    valid_values = {}
    if trait.scaleValidValueMin is not None:
        valid_values["min"] = trait.scaleValidValueMin
    if trait.scaleValidValueMax is not None:
        valid_values["max"] = trait.scaleValidValueMax

    new_var = ObservationVariable(
        organization_id=org_id,
        observation_variable_db_id=var_db_id,
        observation_variable_name=trait.observationVariableName,
        trait_name=trait.traitName,
        trait_description=trait.traitDescription,
        trait_class=trait.traitClass,
        method_name=trait.methodName,
        method_description=trait.methodDescription,
        scale_name=trait.scaleName,
        data_type=trait.scaleDataType,
        default_value=trait.defaultValue,
        common_crop_name=trait.commonCropName,
        status=trait.status or "active",
        valid_values=valid_values if valid_values else None,
    )

    db.add(new_var)
    await db.commit()
    await db.refresh(new_var)

    return {
        "metadata": {
            "datafiles": [],
            "pagination": {"currentPage": 0, "pageSize": 1, "totalCount": 1, "totalPages": 1},
            "status": [{"message": "Trait created successfully", "messageType": "INFO"}]
        },
        "result": _model_to_brapi(new_var)
    }


@router.get("/traits/{observationVariableDbId}")
async def get_trait(
    observationVariableDbId: str,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_optional_user)
):
    """Retrieves a specific trait by its observationVariableDbId.

    Args:
        observationVariableDbId (str): The unique identifier for the trait.
        db (AsyncSession): The SQLAlchemy asynchronous session.
        current_user: The authenticated user, if any.

    Returns:
        A BrAPI-compliant response containing the requested trait.

    Raises:
        HTTPException: If no trait with the given ID is found.
    """
    query = select(ObservationVariable).where(
        ObservationVariable.observation_variable_db_id == observationVariableDbId
    )
    result = await db.execute(query)
    var = result.scalar_one_or_none()

    if not var:
        raise HTTPException(status_code=404, detail="Trait not found")

    return {
        "metadata": {
            "datafiles": [],
            "pagination": {"currentPage": 0, "pageSize": 1, "totalCount": 1, "totalPages": 1},
            "status": []
        },
        "result": _model_to_brapi(var)
    }


@router.put("/traits/{traitDbId}")
async def update_trait(
    traitDbId: str,
    trait: TraitCreate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """Updates an existing trait in the database.

    Args:
        traitDbId (str): The unique identifier for the trait to be updated.
        trait (TraitCreate): A `TraitCreate` model containing the updated trait data.
        db (AsyncSession): The SQLAlchemy asynchronous session.
        current_user: The authenticated user.

    Returns:
        A BrAPI-compliant response containing the updated trait.

    Raises:
        HTTPException: If no trait with the given ID is found.
    """
    query = select(ObservationVariable).where(
        ObservationVariable.observation_variable_db_id == traitDbId
    )
    result = await db.execute(query)
    var = result.scalar_one_or_none()

    if not var:
        raise HTTPException(status_code=404, detail="Trait not found")

    # Update fields
    var.observation_variable_name = trait.observationVariableName
    var.trait_name = trait.traitName
    var.trait_description = trait.traitDescription
    var.trait_class = trait.traitClass
    var.method_name = trait.methodName
    var.method_description = trait.methodDescription
    var.scale_name = trait.scaleName
    var.data_type = trait.scaleDataType
    var.default_value = trait.defaultValue
    var.common_crop_name = trait.commonCropName
    if trait.status:
        var.status = trait.status

    # Update valid_values
    valid_values = {}
    if trait.scaleValidValueMin is not None:
        valid_values["min"] = trait.scaleValidValueMin
    if trait.scaleValidValueMax is not None:
        valid_values["max"] = trait.scaleValidValueMax
    if valid_values:
        var.valid_values = valid_values

    await db.commit()
    await db.refresh(var)

    return {
        "metadata": {
            "datafiles": [],
            "pagination": {"currentPage": 0, "pageSize": 1, "totalCount": 1, "totalPages": 1},
            "status": [{"message": "Trait updated successfully", "messageType": "INFO"}]
        },
        "result": _model_to_brapi(var)
    }
