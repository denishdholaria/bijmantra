"""
BrAPI v2.1 Scales Endpoints
Measurement scales for observation variables

Production-ready: All data from database, no in-memory mock data.
"""

from fastapi import APIRouter, Query, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import Optional, List
import uuid

from app.api.deps import get_db
from app.models.brapi_phenotyping import Scale
from app.core.rls import set_tenant_context

router = APIRouter()


def brapi_response(result, page: int = 0, page_size: int = 1000):
    """Standard BrAPI response wrapper"""
    if isinstance(result, list):
        total = len(result)
        start = page * page_size
        end = start + page_size
        data = result[start:end]
        return {
            "metadata": {
                "datafiles": [],
                "pagination": {
                    "currentPage": page,
                    "pageSize": page_size,
                    "totalCount": total,
                    "totalPages": (total + page_size - 1) // page_size if total > 0 else 1
                },
                "status": [{"message": "Success", "messageType": "INFO"}]
            },
            "result": {"data": data}
        }
    return {
        "metadata": {
            "datafiles": [],
            "pagination": {"currentPage": 0, "pageSize": 1, "totalCount": 1, "totalPages": 1},
            "status": [{"message": "Success", "messageType": "INFO"}]
        },
        "result": result
    }


def scale_to_brapi(scale: Scale) -> dict:
    """Convert Scale model to BrAPI format"""
    valid_values = {}
    if scale.valid_values_min is not None:
        valid_values["min"] = scale.valid_values_min
    if scale.valid_values_max is not None:
        valid_values["max"] = scale.valid_values_max
    if scale.valid_values_categories:
        valid_values["categories"] = scale.valid_values_categories
    
    ontology_ref = None
    if scale.ontology_db_id:
        ontology_ref = {
            "ontologyDbId": scale.ontology_db_id,
            "ontologyName": scale.ontology_name,
            "version": scale.ontology_version
        }
    
    return {
        "scaleDbId": scale.scale_db_id or str(scale.id),
        "scaleName": scale.scale_name,
        "scalePUI": scale.scale_pui,
        "dataType": scale.data_type,
        "decimalPlaces": scale.decimal_places,
        "validValues": valid_values if valid_values else {},
        "ontologyReference": ontology_ref,
        "externalReferences": scale.external_references or [],
        "additionalInfo": scale.additional_info or {}
    }


@router.get("/scales")
async def get_scales(
    request: Request,
    scaleDbId: Optional[str] = None,
    scaleName: Optional[str] = None,
    dataType: Optional[str] = None,
    ontologyDbId: Optional[str] = None,
    externalReferenceId: Optional[str] = None,
    externalReferenceSource: Optional[str] = None,
    page: int = Query(0, ge=0),
    pageSize: int = Query(1000, ge=1, le=10000),
    db: AsyncSession = Depends(get_db)
):
    """Get list of scales"""
    # Set tenant context from request
    org_id = getattr(request.state, "organization_id", None)
    is_superuser = getattr(request.state, "is_superuser", False)
    await set_tenant_context(db, org_id, is_superuser)
    
    # Build query
    query = select(Scale)
    
    if scaleDbId:
        query = query.where(Scale.scale_db_id == scaleDbId)
    if scaleName:
        query = query.where(Scale.scale_name.ilike(f"%{scaleName}%"))
    if dataType:
        query = query.where(Scale.data_type == dataType)
    if ontologyDbId:
        query = query.where(Scale.ontology_db_id == ontologyDbId)
    
    # Execute query
    result = await db.execute(query)
    scales = result.scalars().all()
    
    # Convert to BrAPI format
    brapi_scales = [scale_to_brapi(s) for s in scales]
    
    return brapi_response(brapi_scales, page, pageSize)


@router.get("/scales/{scaleDbId}")
async def get_scale(
    scaleDbId: str,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Get a single scale by ID"""
    org_id = getattr(request.state, "organization_id", None)
    is_superuser = getattr(request.state, "is_superuser", False)
    await set_tenant_context(db, org_id, is_superuser)
    
    # Try to find by scale_db_id first, then by id
    query = select(Scale).where(Scale.scale_db_id == scaleDbId)
    result = await db.execute(query)
    scale = result.scalar_one_or_none()
    
    if not scale:
        # Try by numeric ID
        try:
            scale_id = int(scaleDbId)
            query = select(Scale).where(Scale.id == scale_id)
            result = await db.execute(query)
            scale = result.scalar_one_or_none()
        except ValueError:
            pass
    
    if not scale:
        return {
            "metadata": {
                "status": [{"message": f"Scale {scaleDbId} not found", "messageType": "ERROR"}]
            },
            "result": None
        }
    
    return brapi_response(scale_to_brapi(scale))


@router.post("/scales")
async def create_scales(
    scales: List[dict],
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Create new scales"""
    org_id = getattr(request.state, "organization_id", None)
    is_superuser = getattr(request.state, "is_superuser", False)
    await set_tenant_context(db, org_id, is_superuser)
    
    if not org_id and not is_superuser:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    created = []
    for scale_data in scales:
        new_scale = Scale(
            organization_id=org_id,
            scale_db_id=scale_data.get("scaleDbId") or str(uuid.uuid4()),
            scale_name=scale_data.get("scaleName", ""),
            scale_pui=scale_data.get("scalePUI"),
            data_type=scale_data.get("dataType", "Numerical"),
            decimal_places=scale_data.get("decimalPlaces"),
            valid_values_min=scale_data.get("validValues", {}).get("min"),
            valid_values_max=scale_data.get("validValues", {}).get("max"),
            valid_values_categories=scale_data.get("validValues", {}).get("categories"),
            ontology_db_id=scale_data.get("ontologyReference", {}).get("ontologyDbId") if scale_data.get("ontologyReference") else None,
            ontology_name=scale_data.get("ontologyReference", {}).get("ontologyName") if scale_data.get("ontologyReference") else None,
            ontology_version=scale_data.get("ontologyReference", {}).get("version") if scale_data.get("ontologyReference") else None,
            external_references=scale_data.get("externalReferences", []),
            additional_info=scale_data.get("additionalInfo", {})
        )
        db.add(new_scale)
        await db.flush()
        created.append(scale_to_brapi(new_scale))
    
    await db.commit()
    return brapi_response(created)


@router.put("/scales/{scaleDbId}")
async def update_scale(
    scaleDbId: str,
    scale_data: dict,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Update an existing scale"""
    org_id = getattr(request.state, "organization_id", None)
    is_superuser = getattr(request.state, "is_superuser", False)
    await set_tenant_context(db, org_id, is_superuser)
    
    # Find the scale
    query = select(Scale).where(Scale.scale_db_id == scaleDbId)
    result = await db.execute(query)
    scale = result.scalar_one_or_none()
    
    if not scale:
        return {
            "metadata": {
                "status": [{"message": f"Scale {scaleDbId} not found", "messageType": "ERROR"}]
            },
            "result": None
        }
    
    # Update fields
    if "scaleName" in scale_data:
        scale.scale_name = scale_data["scaleName"]
    if "scalePUI" in scale_data:
        scale.scale_pui = scale_data["scalePUI"]
    if "dataType" in scale_data:
        scale.data_type = scale_data["dataType"]
    if "decimalPlaces" in scale_data:
        scale.decimal_places = scale_data["decimalPlaces"]
    if "validValues" in scale_data:
        valid_values = scale_data["validValues"]
        scale.valid_values_min = valid_values.get("min")
        scale.valid_values_max = valid_values.get("max")
        scale.valid_values_categories = valid_values.get("categories")
    if "ontologyReference" in scale_data and scale_data["ontologyReference"]:
        scale.ontology_db_id = scale_data["ontologyReference"].get("ontologyDbId")
        scale.ontology_name = scale_data["ontologyReference"].get("ontologyName")
        scale.ontology_version = scale_data["ontologyReference"].get("version")
    if "externalReferences" in scale_data:
        scale.external_references = scale_data["externalReferences"]
    if "additionalInfo" in scale_data:
        scale.additional_info = scale_data["additionalInfo"]
    
    await db.commit()
    await db.refresh(scale)
    
    return brapi_response(scale_to_brapi(scale))
