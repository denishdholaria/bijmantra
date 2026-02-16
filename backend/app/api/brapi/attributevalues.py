"""
BrAPI v2.1 Germplasm Attribute Values Endpoints
GET/POST /attributevalues
GET/PUT /attributevalues/{attributeValueDbId}

PRODUCTION-READY: All data from database, no in-memory mock data.
"""

from typing import List, Optional
from fastapi import APIRouter, Query, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload
import uuid

from app.core.database import get_db
from app.models.brapi_phenotyping import GermplasmAttributeValue, GermplasmAttributeDefinition
from app.models.germplasm import Germplasm

router = APIRouter()


# ===========================================
# Pydantic Models
# ===========================================

class AttributeValueBase(BaseModel):
    attributeDbId: str
    attributeName: Optional[str] = None
    germplasmDbId: str
    germplasmName: Optional[str] = None
    value: str
    determinedDate: Optional[str] = None
    additionalInfo: dict = {}
    externalReferences: List[dict] = []


class AttributeValueResponse(AttributeValueBase):
    attributeValueDbId: str


class AttributeValueCreate(AttributeValueBase):
    pass


class AttributeValueUpdate(BaseModel):
    value: Optional[str] = None
    determinedDate: Optional[str] = None
    additionalInfo: Optional[dict] = None


# ===========================================
# Helper Functions
# ===========================================

def create_response(data, page=0, page_size=1000, total_count=1):
    """Create BrAPI-compliant response wrapper"""
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


def model_to_response(av: GermplasmAttributeValue) -> dict:
    """Convert database model to BrAPI response format"""
    return {
        "attributeValueDbId": av.attribute_value_db_id,
        "attributeDbId": av.attribute_db_id,
        "attributeName": av.attribute_name,
        "germplasmDbId": av.germplasm_db_id,
        "germplasmName": av.germplasm_name,
        "value": av.value,
        "determinedDate": av.determined_date,
        "additionalInfo": av.additional_info or {},
        "externalReferences": av.external_references or []
    }


# ===========================================
# BrAPI Endpoints
# ===========================================

@router.get("/attributevalues")
async def get_attribute_values(
    page: int = Query(0, ge=0),
    pageSize: int = Query(1000, ge=1, le=2000),
    attributeDbId: Optional[str] = Query(None),
    attributeName: Optional[str] = Query(None),
    attributeValueDbId: Optional[str] = Query(None),
    germplasmDbId: Optional[str] = Query(None),
    germplasmName: Optional[str] = Query(None),
    externalReferenceId: Optional[str] = Query(None, alias="externalReferenceID"),
    externalReferenceSource: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """
    Get list of germplasm attribute values
    
    BrAPI Endpoint: GET /attributevalues
    """
    # Build query with filters
    query = select(GermplasmAttributeValue)

    conditions = []
    if attributeDbId:
        conditions.append(GermplasmAttributeValue.attribute_db_id == attributeDbId)
    if attributeName:
        conditions.append(GermplasmAttributeValue.attribute_name.ilike(f"%{attributeName}%"))
    if attributeValueDbId:
        conditions.append(GermplasmAttributeValue.attribute_value_db_id == attributeValueDbId)
    if germplasmDbId:
        conditions.append(GermplasmAttributeValue.germplasm_db_id == germplasmDbId)
    if germplasmName:
        conditions.append(GermplasmAttributeValue.germplasm_name.ilike(f"%{germplasmName}%"))

    if conditions:
        query = query.where(and_(*conditions))

    # Get total count
    count_result = await db.execute(select(GermplasmAttributeValue.id).where(and_(*conditions)) if conditions else select(GermplasmAttributeValue.id))
    total_count = len(count_result.all())

    # Apply pagination
    query = query.offset(page * pageSize).limit(pageSize)

    result = await db.execute(query)
    values = result.scalars().all()

    return create_response(
        {"data": [model_to_response(v) for v in values]},
        page, pageSize, total_count
    )


@router.get("/attributevalues/{attributeValueDbId}")
async def get_attribute_value(
    attributeValueDbId: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get a single attribute value by DbId
    
    BrAPI Endpoint: GET /attributevalues/{attributeValueDbId}
    """
    query = select(GermplasmAttributeValue).where(
        GermplasmAttributeValue.attribute_value_db_id == attributeValueDbId
    )
    result = await db.execute(query)
    av = result.scalar_one_or_none()

    if not av:
        raise HTTPException(status_code=404, detail="Attribute value not found")

    return create_response(model_to_response(av))


@router.post("/attributevalues", status_code=201)
async def create_attribute_values(
    values: List[AttributeValueCreate],
    db: AsyncSession = Depends(get_db)
):
    """
    Create new attribute values
    
    BrAPI Endpoint: POST /attributevalues
    """
    created = []

    for val_in in values:
        # Generate unique ID
        val_id = f"av-{uuid.uuid4().hex[:8]}"

        # Look up germplasm to get organization_id and germplasm_id
        germ_query = select(Germplasm).where(
            Germplasm.germplasm_db_id == val_in.germplasmDbId
        )
        germ_result = await db.execute(germ_query)
        germplasm = germ_result.scalar_one_or_none()

        if not germplasm:
            raise HTTPException(
                status_code=400,
                detail=f"Germplasm not found: {val_in.germplasmDbId}"
            )

        # Look up attribute definition if exists
        attr_def_id = None
        if val_in.attributeDbId:
            attr_query = select(GermplasmAttributeDefinition).where(
                GermplasmAttributeDefinition.attribute_db_id == val_in.attributeDbId
            )
            attr_result = await db.execute(attr_query)
            attr_def = attr_result.scalar_one_or_none()
            if attr_def:
                attr_def_id = attr_def.id

        # Create new attribute value
        new_val = GermplasmAttributeValue(
            organization_id=germplasm.organization_id,
            germplasm_id=germplasm.id,
            attribute_definition_id=attr_def_id,
            attribute_value_db_id=val_id,
            attribute_db_id=val_in.attributeDbId,
            attribute_name=val_in.attributeName,
            germplasm_db_id=val_in.germplasmDbId,
            germplasm_name=val_in.germplasmName or germplasm.germplasm_name,
            value=val_in.value,
            determined_date=val_in.determinedDate,
            additional_info=val_in.additionalInfo,
            external_references=val_in.externalReferences
        )

        db.add(new_val)
        created.append(model_to_response(new_val))

    await db.commit()

    return create_response({"data": created}, total_count=len(created))


@router.put("/attributevalues/{attributeValueDbId}")
async def update_attribute_value(
    attributeValueDbId: str,
    val_in: AttributeValueUpdate,
    db: AsyncSession = Depends(get_db)
):
    """
    Update an attribute value
    
    BrAPI Endpoint: PUT /attributevalues/{attributeValueDbId}
    """
    query = select(GermplasmAttributeValue).where(
        GermplasmAttributeValue.attribute_value_db_id == attributeValueDbId
    )
    result = await db.execute(query)
    existing = result.scalar_one_or_none()

    if not existing:
        raise HTTPException(status_code=404, detail="Attribute value not found")

    # Update fields
    update_data = val_in.model_dump(exclude_unset=True)

    if "value" in update_data and update_data["value"] is not None:
        existing.value = update_data["value"]
    if "determinedDate" in update_data and update_data["determinedDate"] is not None:
        existing.determined_date = update_data["determinedDate"]
    if "additionalInfo" in update_data and update_data["additionalInfo"] is not None:
        existing.additional_info = update_data["additionalInfo"]

    await db.commit()
    await db.refresh(existing)

    return create_response(model_to_response(existing))
