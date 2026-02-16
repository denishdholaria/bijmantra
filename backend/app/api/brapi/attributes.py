"""
BrAPI v2.1 Germplasm Attributes Endpoints
GET/POST /attributes - Germplasm attribute definitions
GET/PUT/DELETE /attributes/{attributeDbId}
GET /attributes/categories

Production-ready: All data from database, no in-memory mock data.
Uses GermplasmAttributeService for business logic.
"""

from typing import List, Optional
from fastapi import APIRouter, Query, HTTPException, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.core.rls import set_tenant_context
from app.services.germplasm_attribute_service import GermplasmAttributeService
from app.schemas.germplasm_attribute import (
    GermplasmAttributeDefinitionNewRequest,
    GermplasmAttributeDefinition as GermplasmAttributeSchema
)
from app.schemas.brapi import BrAPIResponse, Metadata, Pagination, Status

router = APIRouter()


def create_response(data, page=0, page_size=1000, total_count=1):
    """
    Creates a BrAPI compliant response object.
    """
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


def attr_to_brapi(attr) -> dict:
    """
    Convert GermplasmAttributeDefinition model to BrAPI format.
    """
    return {
        "attributeDbId": attr.attribute_db_id or str(attr.id),
        "attributeName": attr.attribute_name,
        "attributePUI": attr.attribute_pui,
        "attributeDescription": attr.attribute_description,
        "attributeCategory": attr.attribute_category,
        "commonCropName": attr.common_crop_name,
        "contextOfUse": attr.context_of_use or [],
        "defaultValue": attr.default_value,
        "documentationURL": attr.documentation_url,
        "growthStage": attr.growth_stage,
        "institution": attr.institution,
        "language": attr.language,
        "scientist": attr.scientist,
        "status": attr.status,
        "submissionTimestamp": attr.submission_timestamp,
        "synonyms": attr.synonyms or [],
        "traitDbId": attr.trait_db_id,
        "traitName": attr.trait_name,
        "traitDescription": attr.trait_description,
        "traitClass": attr.trait_class,
        "methodDbId": attr.method_db_id,
        "methodName": attr.method_name,
        "methodDescription": attr.method_description,
        "methodClass": attr.method_class,
        "scaleDbId": attr.scale_db_id,
        "scaleName": attr.scale_name,
        "dataType": attr.data_type,
        "additionalInfo": attr.additional_info or {},
        "externalReferences": attr.external_references or []
    }


@router.get("/attributes")
async def get_attributes(
    request: Request,
    page: int = Query(0, ge=0),
    pageSize: int = Query(1000, ge=1, le=2000),
    attributeCategory: Optional[str] = Query(None),
    attributeDbId: Optional[str] = Query(None),
    attributeName: Optional[str] = Query(None),
    attributePUI: Optional[str] = Query(None),
    commonCropName: Optional[str] = Query(None),
    germplasmDbId: Optional[str] = Query(None),
    programDbId: Optional[str] = Query(None),
    traitDbId: Optional[str] = Query(None),
    methodDbId: Optional[str] = Query(None),
    scaleDbId: Optional[str] = Query(None),
    externalReferenceId: Optional[str] = Query(None, alias="externalReferenceID"),
    externalReferenceSource: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """
    Get a list of germplasm attributes.
    """
    org_id = getattr(request.state, "organization_id", None)
    is_superuser = getattr(request.state, "is_superuser", False)
    await set_tenant_context(db, org_id, is_superuser)

    attrs = await GermplasmAttributeService.get_attributes(
        db, page, pageSize, attributeCategory, attributeDbId, attributeName,
        common_crop_name=commonCropName, trait_db_id=traitDbId,
        method_db_id=methodDbId, scale_db_id=scaleDbId,
        organization_id=org_id if not is_superuser else None
    )

    total_count = await GermplasmAttributeService.get_total_count(
        db, attributeCategory, attributeDbId, attributeName,
        common_crop_name=commonCropName, trait_db_id=traitDbId,
        method_db_id=methodDbId, scale_db_id=scaleDbId,
        organization_id=org_id if not is_superuser else None
    )

    return create_response(
        {"data": [attr_to_brapi(a) for a in attrs]},
        page, pageSize, total_count
    )


@router.get("/attributes/categories")
async def get_attribute_categories(
    request: Request,
    page: int = Query(0, ge=0),
    pageSize: int = Query(1000, ge=1, le=2000),
    db: AsyncSession = Depends(get_db)
):
    """
    Get a list of attribute categories.
    """
    org_id = getattr(request.state, "organization_id", None)
    is_superuser = getattr(request.state, "is_superuser", False)
    await set_tenant_context(db, org_id, is_superuser)

    categories = await GermplasmAttributeService.get_attribute_categories(
        db, page, pageSize, organization_id=org_id if not is_superuser else None
    )

    # We might need a separate count for categories, but here we assume list is small or paginated
    total_count = len(categories) # This is approximate if paginated inside service

    return create_response({"data": categories}, page, pageSize, total_count)


@router.get("/attributes/{attributeDbId}")
async def get_attribute(
    attributeDbId: str,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Get a single attribute by DbId.
    """
    org_id = getattr(request.state, "organization_id", None)
    is_superuser = getattr(request.state, "is_superuser", False)
    await set_tenant_context(db, org_id, is_superuser)

    attr = await GermplasmAttributeService.get_attribute(
        db, attributeDbId, organization_id=org_id if not is_superuser else None
    )

    if not attr:
        raise HTTPException(status_code=404, detail="Attribute not found")

    return create_response(attr_to_brapi(attr))


@router.post("/attributes", status_code=201)
async def create_attributes(
    attributes: List[GermplasmAttributeDefinitionNewRequest],
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Create new attributes.
    """
    org_id = getattr(request.state, "organization_id", None)
    is_superuser = getattr(request.state, "is_superuser", False)
    await set_tenant_context(db, org_id, is_superuser)

    if not org_id and not is_superuser:
        raise HTTPException(status_code=401, detail="Authentication required")

    # Default to org_id 1 if not set and is_superuser (fallback)
    target_org_id = org_id or 1

    created = await GermplasmAttributeService.create_attributes(
        db, attributes, organization_id=target_org_id
    )

    return create_response(
        {"data": [attr_to_brapi(a) for a in created]},
        total_count=len(created)
    )


@router.put("/attributes/{attributeDbId}")
async def update_attribute(
    attributeDbId: str,
    attr_in: GermplasmAttributeDefinitionNewRequest,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Update an attribute.
    """
    org_id = getattr(request.state, "organization_id", None)
    is_superuser = getattr(request.state, "is_superuser", False)
    await set_tenant_context(db, org_id, is_superuser)

    updated = await GermplasmAttributeService.update_attribute(
        db, attributeDbId, attr_in, organization_id=org_id if not is_superuser else None
    )

    if not updated:
        raise HTTPException(status_code=404, detail="Attribute not found")

    return create_response(attr_to_brapi(updated))


@router.delete("/attributes/{attributeDbId}", status_code=200)
async def delete_attribute(
    attributeDbId: str,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Delete an attribute.
    """
    org_id = getattr(request.state, "organization_id", None)
    is_superuser = getattr(request.state, "is_superuser", False)
    await set_tenant_context(db, org_id, is_superuser)

    success = await GermplasmAttributeService.delete_attribute(
        db, attributeDbId, organization_id=org_id if not is_superuser else None
    )

    if not success:
        raise HTTPException(status_code=404, detail="Attribute not found")

    return create_response({"message": "Attribute deleted successfully"}, total_count=1)
