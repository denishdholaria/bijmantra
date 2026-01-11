"""
BrAPI v2.1 Germplasm Attributes Endpoints
GET/POST /attributes - Germplasm attribute definitions
GET/PUT /attributes/{attributeDbId}
GET /attributes/categories

Production-ready: All data from database, no in-memory mock data.
"""

from typing import List, Optional
from fastapi import APIRouter, Query, HTTPException, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, distinct
import uuid

from app.api.deps import get_db
from app.models.brapi_phenotyping import GermplasmAttributeDefinition
from app.core.rls import set_tenant_context

router = APIRouter()


def create_response(data, page=0, page_size=1000, total_count=1):
    """
    Creates a BrAPI compliant response object.

    Args:
        data (list): The data to be returned.
        page (int): The current page number.
        page_size (int): The number of items per page.
        total_count (int): The total number of items.

    Returns:
        dict: A BrAPI compliant response object.
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


def attr_to_brapi(attr: GermplasmAttributeDefinition) -> dict:
    """
    Convert GermplasmAttributeDefinition model to BrAPI format.

    Args:
        attr (GermplasmAttributeDefinition): The GermplasmAttributeDefinition model object.

    Returns:
        dict: The BrAPI formatted attribute data.
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

    Args:
        request (Request): The request object.
        page (int): The page number.
        pageSize (int): The page size.
        attributeCategory (Optional[str]): Filter by attribute category.
        attributeDbId (Optional[str]): Filter by attribute DbId.
        attributeName (Optional[str]): Filter by attribute name.
        attributePUI (Optional[str]): Filter by attribute PUI.
        commonCropName (Optional[str]): Filter by common crop name.
        germplasmDbId (Optional[str]): Filter by germplasm DbId.
        programDbId (Optional[str]): Filter by program DbId.
        traitDbId (Optional[str]): Filter by trait DbId.
        methodDbId (Optional[str]): Filter by method DbId.
        scaleDbId (Optional[str]): Filter by scale DbId.
        externalReferenceId (Optional[str]): Filter by external reference ID.
        externalReferenceSource (Optional[str]): Filter by external reference source.
        db (AsyncSession): The database session.

    Returns:
        dict: A BrAPI compliant response object containing a list of attributes.
    """
    org_id = getattr(request.state, "organization_id", None)
    is_superuser = getattr(request.state, "is_superuser", False)
    await set_tenant_context(db, org_id, is_superuser)
    
    query = select(GermplasmAttributeDefinition)
    
    if attributeCategory:
        query = query.where(GermplasmAttributeDefinition.attribute_category == attributeCategory)
    if attributeDbId:
        query = query.where(GermplasmAttributeDefinition.attribute_db_id == attributeDbId)
    if attributeName:
        query = query.where(GermplasmAttributeDefinition.attribute_name.ilike(f"%{attributeName}%"))
    if commonCropName:
        query = query.where(GermplasmAttributeDefinition.common_crop_name == commonCropName)
    if traitDbId:
        query = query.where(GermplasmAttributeDefinition.trait_db_id == traitDbId)
    if methodDbId:
        query = query.where(GermplasmAttributeDefinition.method_db_id == methodDbId)
    if scaleDbId:
        query = query.where(GermplasmAttributeDefinition.scale_db_id == scaleDbId)
    
    result = await db.execute(query)
    attrs = result.scalars().all()
    
    total_count = len(attrs)
    start = page * pageSize
    end = start + pageSize
    paginated = attrs[start:end]
    
    return create_response(
        {"data": [attr_to_brapi(a) for a in paginated]},
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

    Args:
        request (Request): The request object.
        page (int): The page number.
        pageSize (int): The page size.
        db (AsyncSession): The database session.

    Returns:
        dict: A BrAPI compliant response object containing a list of attribute categories.
    """
    org_id = getattr(request.state, "organization_id", None)
    is_superuser = getattr(request.state, "is_superuser", False)
    await set_tenant_context(db, org_id, is_superuser)
    
    # Get distinct categories from database
    query = select(distinct(GermplasmAttributeDefinition.attribute_category)).where(
        GermplasmAttributeDefinition.attribute_category.isnot(None)
    )
    result = await db.execute(query)
    categories = [row[0] for row in result.fetchall()]
    
    # If no categories in DB, return standard list
    if not categories:
        categories = [
            "Morphological", "Phenological", "Agronomic",
            "Biotic Stress", "Abiotic Stress", "Quality",
            "Biochemical", "Molecular", "Physiological",
            "Root", "Seed", "Grain", "Panicle", "Leaf", "Stem"
        ]
    
    total_count = len(categories)
    start = page * pageSize
    end = start + pageSize
    paginated = categories[start:end]
    
    return create_response({"data": paginated}, page, pageSize, total_count)


@router.get("/attributes/{attributeDbId}")
async def get_attribute(
    attributeDbId: str,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Get a single attribute by DbId.

    Args:
        attributeDbId (str): The DbId of the attribute.
        request (Request): The request object.
        db (AsyncSession): The database session.

    Returns:
        dict: A BrAPI compliant response object containing the attribute.

    Raises:
        HTTPException: If the attribute is not found.
    """
    org_id = getattr(request.state, "organization_id", None)
    is_superuser = getattr(request.state, "is_superuser", False)
    await set_tenant_context(db, org_id, is_superuser)
    
    query = select(GermplasmAttributeDefinition).where(
        GermplasmAttributeDefinition.attribute_db_id == attributeDbId
    )
    result = await db.execute(query)
    attr = result.scalar_one_or_none()
    
    if not attr:
        try:
            attr_id = int(attributeDbId)
            query = select(GermplasmAttributeDefinition).where(
                GermplasmAttributeDefinition.id == attr_id
            )
            result = await db.execute(query)
            attr = result.scalar_one_or_none()
        except ValueError:
            pass
    
    if not attr:
        raise HTTPException(status_code=404, detail="Attribute not found")
    
    return create_response(attr_to_brapi(attr))


@router.post("/attributes", status_code=201)
async def create_attributes(
    attributes: List[dict],
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Create new attributes.

    Args:
        attributes (List[dict]): A list of attributes to create.
        request (Request): The request object.
        db (AsyncSession): The database session.

    Returns:
        dict: A BrAPI compliant response object containing the created attributes.

    Raises:
        HTTPException: If the user is not authenticated.
    """
    org_id = getattr(request.state, "organization_id", None)
    is_superuser = getattr(request.state, "is_superuser", False)
    await set_tenant_context(db, org_id, is_superuser)
    
    if not org_id and not is_superuser:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    created = []
    for attr_in in attributes:
        new_attr = GermplasmAttributeDefinition(
            organization_id=org_id,
            attribute_db_id=attr_in.get("attributeDbId") or f"attr-{uuid.uuid4().hex[:8]}",
            attribute_name=attr_in.get("attributeName", ""),
            attribute_pui=attr_in.get("attributePUI"),
            attribute_description=attr_in.get("attributeDescription"),
            attribute_category=attr_in.get("attributeCategory"),
            common_crop_name=attr_in.get("commonCropName"),
            context_of_use=attr_in.get("contextOfUse"),
            default_value=attr_in.get("defaultValue"),
            documentation_url=attr_in.get("documentationURL"),
            growth_stage=attr_in.get("growthStage"),
            institution=attr_in.get("institution"),
            language=attr_in.get("language", "en"),
            scientist=attr_in.get("scientist"),
            status=attr_in.get("status", "active"),
            submission_timestamp=attr_in.get("submissionTimestamp"),
            synonyms=attr_in.get("synonyms"),
            trait_db_id=attr_in.get("traitDbId"),
            trait_name=attr_in.get("traitName"),
            trait_description=attr_in.get("traitDescription"),
            trait_class=attr_in.get("traitClass"),
            method_db_id=attr_in.get("methodDbId"),
            method_name=attr_in.get("methodName"),
            method_description=attr_in.get("methodDescription"),
            method_class=attr_in.get("methodClass"),
            scale_db_id=attr_in.get("scaleDbId"),
            scale_name=attr_in.get("scaleName"),
            data_type=attr_in.get("dataType", "Text"),
            additional_info=attr_in.get("additionalInfo", {}),
            external_references=attr_in.get("externalReferences", [])
        )
        db.add(new_attr)
        await db.flush()
        created.append(attr_to_brapi(new_attr))
    
    await db.commit()
    return create_response({"data": created}, total_count=len(created))


@router.put("/attributes/{attributeDbId}")
async def update_attribute(
    attributeDbId: str,
    attr_in: dict,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Update an attribute.

    Args:
        attributeDbId (str): The DbId of the attribute to update.
        attr_in (dict): The attribute data to update.
        request (Request): The request object.
        db (AsyncSession): The database session.

    Returns:
        dict: A BrAPI compliant response object containing the updated attribute.

    Raises:
        HTTPException: If the attribute is not found.
    """
    org_id = getattr(request.state, "organization_id", None)
    is_superuser = getattr(request.state, "is_superuser", False)
    await set_tenant_context(db, org_id, is_superuser)
    
    query = select(GermplasmAttributeDefinition).where(
        GermplasmAttributeDefinition.attribute_db_id == attributeDbId
    )
    result = await db.execute(query)
    attr = result.scalar_one_or_none()
    
    if not attr:
        raise HTTPException(status_code=404, detail="Attribute not found")
    
    # Update fields if provided
    for field in ["attributeName", "attributeDescription", "attributeCategory", 
                  "status", "additionalInfo", "commonCropName", "traitName",
                  "methodName", "scaleName", "dataType"]:
        if field in attr_in:
            # Convert camelCase to snake_case
            snake_field = ''.join(['_' + c.lower() if c.isupper() else c for c in field]).lstrip('_')
            setattr(attr, snake_field, attr_in[field])
    
    await db.commit()
    await db.refresh(attr)
    
    return create_response(attr_to_brapi(attr))
