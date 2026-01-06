"""
BrAPI Core - Locations endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import get_organization_id
from app.crud.core import location as location_crud
from app.schemas.core import Location, LocationCreate, LocationUpdate
from app.schemas.brapi import BrAPIResponse, Metadata, Pagination, Status
from app.core.config import settings

router = APIRouter()


def create_brapi_response(data: any, page: int, page_size: int, total_count: int):
    """Helper to create BrAPI response with metadata"""
    total_pages = (total_count + page_size - 1) // page_size
    
    metadata = Metadata(
        pagination=Pagination(
            current_page=page,
            page_size=page_size,
            total_count=total_count,
            total_pages=total_pages
        ),
        status=[Status(message="Success", message_type="INFO")]
    )
    
    return BrAPIResponse(metadata=metadata, result={"data": data})


@router.get("/locations", response_model=BrAPIResponse[dict])
async def list_locations(
    page: int = Query(0, ge=0),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE),
    location_type: str = Query(None, alias="locationType"),
    db: AsyncSession = Depends(get_db),
    org_id: int = Depends(get_organization_id)
):
    """List locations with pagination"""
    filters = {}
    if location_type:
        filters['location_type'] = location_type
    
    skip = page * page_size
    locations, total_count = await location_crud.get_multi(
        db, skip=skip, limit=page_size, org_id=org_id, filters=filters if filters else None
    )
    
    location_list = [Location.model_validate(loc) for loc in locations]
    return create_brapi_response(location_list, page, page_size, total_count)


@router.get("/locations/{locationDbId}", response_model=BrAPIResponse[dict])
async def get_location(
    locationDbId: str,
    db: AsyncSession = Depends(get_db),
    org_id: int = Depends(get_organization_id)
):
    """Get a single location by DbId"""
    location = await location_crud.get_by_db_id(db, locationDbId, org_id)
    
    if not location:
        raise HTTPException(status_code=404, detail="Location not found")
    
    location_data = Location.model_validate(location)
    metadata = Metadata(
        pagination=Pagination(current_page=0, page_size=1, total_count=1, total_pages=1),
        status=[Status(message="Success", message_type="INFO")]
    )
    
    return BrAPIResponse(metadata=metadata, result=location_data)


@router.post("/locations", response_model=BrAPIResponse[dict], status_code=201)
async def create_location(
    location_in: LocationCreate,
    db: AsyncSession = Depends(get_db),
    org_id: int = Depends(get_organization_id)
):
    """Create a new location"""
    location = await location_crud.create(db, obj_in=location_in, org_id=org_id)
    await db.commit()
    
    location_data = Location.model_validate(location)
    metadata = Metadata(
        pagination=Pagination(current_page=0, page_size=1, total_count=1, total_pages=1),
        status=[Status(message="Location created successfully", message_type="INFO")]
    )
    
    return BrAPIResponse(metadata=metadata, result=location_data)


@router.put("/locations/{locationDbId}", response_model=BrAPIResponse[dict])
async def update_location(
    locationDbId: str,
    location_in: LocationUpdate,
    db: AsyncSession = Depends(get_db),
    org_id: int = Depends(get_organization_id)
):
    """Update a location"""
    location = await location_crud.get_by_db_id(db, locationDbId, org_id)
    
    if not location:
        raise HTTPException(status_code=404, detail="Location not found")
    
    location = await location_crud.update(db, db_obj=location, obj_in=location_in)
    await db.commit()
    
    location_data = Location.model_validate(location)
    metadata = Metadata(
        pagination=Pagination(current_page=0, page_size=1, total_count=1, total_pages=1),
        status=[Status(message="Location updated successfully", message_type="INFO")]
    )
    
    return BrAPIResponse(metadata=metadata, result=location_data)


@router.delete("/locations/{locationDbId}", status_code=204)
async def delete_location(
    locationDbId: str,
    db: AsyncSession = Depends(get_db),
    org_id: int = Depends(get_organization_id)
):
    """
    Delete a location
    
    BrAPI Endpoint: DELETE /locations/{locationDbId}
    """
    location = await location_crud.get_by_db_id(db, locationDbId, org_id)
    
    if not location:
        raise HTTPException(status_code=404, detail="Location not found")
    
    await location_crud.delete(db, id=location.id)
    await db.commit()
    
    return None
