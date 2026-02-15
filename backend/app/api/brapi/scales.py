"""
BrAPI v2.1 Scales Endpoints
Measurement scales for observation variables

Production-ready: Uses Service layer and Pydantic schemas.
"""

from fastapi import APIRouter, Query, Depends, HTTPException, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List, Union

from app.api.deps import get_db
from app.core.rls import set_tenant_context
from app.services.scales_service import ScalesService
from app.schemas.brapi_scales import (
    Scale, ScaleCreate, ScaleUpdate,
    ScaleListResponse, ScaleSingleResponse, ScaleDeleteResponse,
    ValidValues, OntologyReference, ExternalReference
)
from app.models.brapi_phenotyping import Scale as ScaleModel

router = APIRouter()

def scale_to_schema(scale: ScaleModel) -> Scale:
    """Converts a Scale SQLAlchemy model to Pydantic schema."""
    valid_values = None
    if scale.valid_values_min is not None or scale.valid_values_max is not None or scale.valid_values_categories:
        valid_values = ValidValues(
            min=scale.valid_values_min,
            max=scale.valid_values_max,
            categories=scale.valid_values_categories
        )

    ontology_ref = None
    if scale.ontology_db_id:
        ontology_ref = OntologyReference(
            ontologyDbId=scale.ontology_db_id,
            ontologyName=scale.ontology_name,
            version=scale.ontology_version
        )

    return Scale(
        scaleDbId=scale.scale_db_id or str(scale.id),
        scaleName=scale.scale_name,
        scalePUI=scale.scale_pui,
        dataType=scale.data_type,
        decimalPlaces=scale.decimal_places,
        validValues=valid_values,
        ontologyReference=ontology_ref,
        externalReferences=[ExternalReference(**ref) for ref in (scale.external_references or [])],
        additionalInfo=scale.additional_info
    )

def brapi_response(result: Union[List[Scale], Scale], page: int = 0, page_size: int = 1000, total_count: Optional[int] = None) -> dict:
    if isinstance(result, list):
        if total_count is None:
            total_count = len(result)
        return {
            "metadata": {
                "datafiles": [],
                "pagination": {
                    "currentPage": page,
                    "pageSize": page_size,
                    "totalCount": total_count,
                    "totalPages": (total_count + page_size - 1) // page_size if total_count > 0 else 1
                },
                "status": [{"message": "Success", "messageType": "INFO"}]
            },
            "result": {"data": result}
        }
    return {
        "metadata": {
            "datafiles": [],
            "pagination": {"currentPage": 0, "pageSize": 1, "totalCount": 1, "totalPages": 1},
            "status": [{"message": "Success", "messageType": "INFO"}]
        },
        "result": result
    }

@router.get("/scales", response_model=ScaleListResponse)
async def get_scales(
    request: Request,
    scaleDbId: Optional[str] = None,
    scaleName: Optional[str] = None,
    dataType: Optional[str] = None,
    ontologyDbId: Optional[str] = None,
    page: int = Query(0, ge=0),
    pageSize: int = Query(1000, ge=1, le=10000),
    db: AsyncSession = Depends(get_db)
):
    """Retrieves a list of scales based on search criteria."""
    org_id = getattr(request.state, "organization_id", None)
    is_superuser = getattr(request.state, "is_superuser", False)
    await set_tenant_context(db, org_id, is_superuser)
    
    scales, total = await ScalesService.get_all(
        db, page, pageSize,
        scale_db_id=scaleDbId,
        scale_name=scaleName,
        data_type=dataType,
        ontology_db_id=ontologyDbId
    )
    
    return brapi_response([scale_to_schema(s) for s in scales], page, pageSize, total)

@router.get("/scales/{scaleDbId}", response_model=ScaleSingleResponse)
async def get_scale(
    scaleDbId: str,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Retrieves a single scale by its unique identifier."""
    org_id = getattr(request.state, "organization_id", None)
    is_superuser = getattr(request.state, "is_superuser", False)
    await set_tenant_context(db, org_id, is_superuser)
    
    scale = await ScalesService.get_by_id(db, scaleDbId)
    
    if not scale:
        return {
            "metadata": {
                "datafiles": [],
                "pagination": {"currentPage": 0, "pageSize": 0, "totalCount": 0, "totalPages": 0},
                "status": [{"message": f"Scale {scaleDbId} not found", "messageType": "ERROR"}]
            },
            "result": None
        }
    
    return brapi_response(scale_to_schema(scale))

@router.post("/scales", response_model=ScaleListResponse)
async def create_scales(
    scales: List[ScaleCreate],
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Creates one or more new scales."""
    org_id = getattr(request.state, "organization_id", None)
    is_superuser = getattr(request.state, "is_superuser", False)
    await set_tenant_context(db, org_id, is_superuser)
    
    if not org_id and not is_superuser:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    # Use default org for superusers if not specified (simplification)
    target_org_id = org_id if org_id else 1

    created = []
    for scale_in in scales:
        new_scale = await ScalesService.create(db, scale_in, target_org_id)
        created.append(scale_to_schema(new_scale))
    
    await db.commit()
    return brapi_response(created)

@router.put("/scales/{scaleDbId}", response_model=ScaleSingleResponse)
async def update_scale(
    scaleDbId: str,
    scale_in: ScaleUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Updates an existing scale."""
    org_id = getattr(request.state, "organization_id", None)
    is_superuser = getattr(request.state, "is_superuser", False)
    await set_tenant_context(db, org_id, is_superuser)
    
    updated_scale = await ScalesService.update(db, scaleDbId, scale_in)
    
    if not updated_scale:
        return {
            "metadata": {
                "datafiles": [],
                "pagination": {"currentPage": 0, "pageSize": 0, "totalCount": 0, "totalPages": 0},
                "status": [{"message": f"Scale {scaleDbId} not found", "messageType": "ERROR"}]
            },
            "result": None
        }
    
    await db.commit()
    return brapi_response(scale_to_schema(updated_scale))

@router.delete("/scales/{scaleDbId}", response_model=ScaleDeleteResponse)
async def delete_scale(
    scaleDbId: str,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Deletes a scale."""
    org_id = getattr(request.state, "organization_id", None)
    is_superuser = getattr(request.state, "is_superuser", False)
    await set_tenant_context(db, org_id, is_superuser)

    success = await ScalesService.delete(db, scaleDbId)

    if not success:
         return {
            "metadata": {
                "datafiles": [],
                "pagination": {"currentPage": 0, "pageSize": 0, "totalCount": 0, "totalPages": 0},
                "status": [{"message": f"Scale {scaleDbId} not found", "messageType": "ERROR"}]
            },
            "result": None
        }
    
    await db.commit()
    return {
        "metadata": {
            "datafiles": [],
            "pagination": {"currentPage": 0, "pageSize": 0, "totalCount": 0, "totalPages": 0},
            "status": [{"message": "Scale deleted successfully", "messageType": "INFO"}]
        },
        "result": None
    }
