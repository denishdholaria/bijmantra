"""
BrAPI Core - Lists endpoints
CRUD operations for generic lists

Database-backed implementation for production use.
"""

from typing import List as ListType, Optional
from fastapi import APIRouter, Query, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pydantic import BaseModel
from datetime import datetime, timezone
import uuid

from app.core.database import get_db
from app.api.deps import get_organization_id
from app.models.core import List as ListModel

router = APIRouter()


class ListCreate(BaseModel):
    """Create a new list"""
    listName: str
    listDescription: Optional[str] = None
    listType: str = "germplasm"
    listOwnerName: Optional[str] = None
    listOwnerPersonDbId: Optional[str] = None
    listSource: Optional[str] = None
    externalReferences: ListType[dict] = []
    additionalInfo: dict = {}
    data: ListType[str] = []


class ListUpdate(BaseModel):
    """Update a list"""
    listName: Optional[str] = None
    listDescription: Optional[str] = None
    listType: Optional[str] = None
    listOwnerName: Optional[str] = None
    listOwnerPersonDbId: Optional[str] = None
    listSource: Optional[str] = None
    externalReferences: Optional[ListType[dict]] = None
    additionalInfo: Optional[dict] = None
    data: Optional[ListType[str]] = None


def model_to_dict(list_obj: ListModel) -> dict:
    """Convert List model to BrAPI response dict"""
    return {
        "listDbId": list_obj.list_db_id,
        "listName": list_obj.list_name,
        "listDescription": list_obj.list_description,
        "listType": list_obj.list_type,
        "listOwnerName": list_obj.list_owner_name,
        "listOwnerPersonDbId": list_obj.list_owner_person_db_id,
        "listSize": list_obj.list_size or 0,
        "listSource": list_obj.list_source,
        "dateCreated": list_obj.date_created,
        "dateModified": list_obj.date_modified,
        "externalReferences": list_obj.external_references or [],
        "additionalInfo": list_obj.additional_info or {},
        "data": list_obj.data or [],
    }


def create_response(data, page=0, page_size=1000, total_count=1):
    """Helper to create BrAPI response"""
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


@router.get("/lists")
async def get_lists(
    page: int = Query(0, ge=0),
    pageSize: int = Query(1000, ge=1, le=2000),
    listType: Optional[str] = Query(None, description="Filter by list type"),
    listName: Optional[str] = Query(None, description="Filter by list name"),
    listDbId: Optional[str] = Query(None, description="Filter by list DbId"),
    listSource: Optional[str] = Query(None, description="Filter by list source"),
    externalReferenceId: Optional[str] = Query(None, alias="externalReferenceID"),
    externalReferenceSource: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    org_id: int = Depends(get_organization_id)
):
    """
    Get all lists with optional filtering
    
    BrAPI Endpoint: GET /lists
    """
    # Build query
    query = select(ListModel).where(ListModel.organization_id == org_id)
    
    if listType:
        query = query.where(ListModel.list_type == listType)
    if listName:
        query = query.where(ListModel.list_name.ilike(f"%{listName}%"))
    if listDbId:
        query = query.where(ListModel.list_db_id == listDbId)
    if listSource:
        query = query.where(ListModel.list_source == listSource)
    
    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total_count = total_result.scalar() or 0
    
    # Apply pagination
    query = query.order_by(ListModel.list_name)
    query = query.offset(page * pageSize).limit(pageSize)
    
    result = await db.execute(query)
    lists = result.scalars().all()
    
    # Convert to BrAPI format
    lists_data = [model_to_dict(l) for l in lists]
    
    return create_response({"data": lists_data}, page, pageSize, total_count)


@router.get("/lists/{listDbId}")
async def get_list(
    listDbId: str,
    db: AsyncSession = Depends(get_db),
    org_id: int = Depends(get_organization_id)
):
    """
    Get a single list by DbId
    
    BrAPI Endpoint: GET /lists/{listDbId}
    """
    query = select(ListModel).where(
        ListModel.list_db_id == listDbId,
        ListModel.organization_id == org_id
    )
    result = await db.execute(query)
    list_obj = result.scalar_one_or_none()
    
    if not list_obj:
        raise HTTPException(status_code=404, detail="List not found")
    
    return create_response(model_to_dict(list_obj))


@router.post("/lists", status_code=201)
async def create_list(
    list_in: ListCreate,
    db: AsyncSession = Depends(get_db),
    org_id: int = Depends(get_organization_id)
):
    """
    Create a new list
    
    BrAPI Endpoint: POST /lists
    """
    list_id = f"list-{uuid.uuid4().hex[:8]}"
    now = datetime.now(timezone.utc).isoformat() + "Z"
    
    new_list = ListModel(
        organization_id=org_id,
        list_db_id=list_id,
        list_name=list_in.listName,
        list_description=list_in.listDescription,
        list_type=list_in.listType,
        list_owner_name=list_in.listOwnerName,
        list_owner_person_db_id=list_in.listOwnerPersonDbId,
        list_source=list_in.listSource,
        list_size=len(list_in.data),
        date_created=now,
        date_modified=now,
        data=list_in.data,
        additional_info=list_in.additionalInfo,
        external_references=list_in.externalReferences,
    )
    
    db.add(new_list)
    await db.commit()
    await db.refresh(new_list)
    
    return create_response(model_to_dict(new_list))


@router.put("/lists/{listDbId}")
async def update_list(
    listDbId: str,
    list_in: ListUpdate,
    db: AsyncSession = Depends(get_db),
    org_id: int = Depends(get_organization_id)
):
    """
    Update an existing list
    
    BrAPI Endpoint: PUT /lists/{listDbId}
    """
    query = select(ListModel).where(
        ListModel.list_db_id == listDbId,
        ListModel.organization_id == org_id
    )
    result = await db.execute(query)
    list_obj = result.scalar_one_or_none()
    
    if not list_obj:
        raise HTTPException(status_code=404, detail="List not found")
    
    # Update fields
    if list_in.listName is not None:
        list_obj.list_name = list_in.listName
    if list_in.listDescription is not None:
        list_obj.list_description = list_in.listDescription
    if list_in.listType is not None:
        list_obj.list_type = list_in.listType
    if list_in.listOwnerName is not None:
        list_obj.list_owner_name = list_in.listOwnerName
    if list_in.listOwnerPersonDbId is not None:
        list_obj.list_owner_person_db_id = list_in.listOwnerPersonDbId
    if list_in.listSource is not None:
        list_obj.list_source = list_in.listSource
    if list_in.externalReferences is not None:
        list_obj.external_references = list_in.externalReferences
    if list_in.additionalInfo is not None:
        list_obj.additional_info = list_in.additionalInfo
    if list_in.data is not None:
        list_obj.data = list_in.data
        list_obj.list_size = len(list_in.data)
    
    list_obj.date_modified = datetime.now(timezone.utc).isoformat() + "Z"
    
    await db.commit()
    await db.refresh(list_obj)
    
    return create_response(model_to_dict(list_obj))


@router.post("/lists/{listDbId}/items", status_code=201)
async def add_list_items(
    listDbId: str,
    items: ListType[str],
    db: AsyncSession = Depends(get_db),
    org_id: int = Depends(get_organization_id)
):
    """
    Add items to an existing list
    
    BrAPI Endpoint: POST /lists/{listDbId}/items
    """
    query = select(ListModel).where(
        ListModel.list_db_id == listDbId,
        ListModel.organization_id == org_id
    )
    result = await db.execute(query)
    list_obj = result.scalar_one_or_none()
    
    if not list_obj:
        raise HTTPException(status_code=404, detail="List not found")
    
    # Add items
    current_data = list_obj.data or []
    current_data.extend(items)
    list_obj.data = current_data
    list_obj.list_size = len(current_data)
    list_obj.date_modified = datetime.now(timezone.utc).isoformat() + "Z"
    
    await db.commit()
    await db.refresh(list_obj)
    
    return create_response(model_to_dict(list_obj))


@router.post("/lists/{listDbId}/data", status_code=201)
async def set_list_data(
    listDbId: str,
    data: ListType[str],
    db: AsyncSession = Depends(get_db),
    org_id: int = Depends(get_organization_id)
):
    """
    Replace all items in a list
    
    BrAPI Endpoint: POST /lists/{listDbId}/data
    """
    query = select(ListModel).where(
        ListModel.list_db_id == listDbId,
        ListModel.organization_id == org_id
    )
    result = await db.execute(query)
    list_obj = result.scalar_one_or_none()
    
    if not list_obj:
        raise HTTPException(status_code=404, detail="List not found")
    
    list_obj.data = data
    list_obj.list_size = len(data)
    list_obj.date_modified = datetime.now(timezone.utc).isoformat() + "Z"
    
    await db.commit()
    await db.refresh(list_obj)
    
    return create_response(model_to_dict(list_obj))


@router.delete("/lists/{listDbId}")
async def delete_list(
    listDbId: str,
    db: AsyncSession = Depends(get_db),
    org_id: int = Depends(get_organization_id)
):
    """
    Delete a list
    
    BrAPI Endpoint: DELETE /lists/{listDbId}
    """
    query = select(ListModel).where(
        ListModel.list_db_id == listDbId,
        ListModel.organization_id == org_id
    )
    result = await db.execute(query)
    list_obj = result.scalar_one_or_none()
    
    if not list_obj:
        raise HTTPException(status_code=404, detail="List not found")
    
    await db.delete(list_obj)
    await db.commit()
    
    return {"message": "List deleted successfully"}
