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
from app.core.rls import set_tenant_context
from app.models.core import User
from app.api.deps import get_current_active_user

router = APIRouter()


def create_brapi_response(data: any, page: int, page_size: int, total_count: int):
    """Creates a standardized BrAPI response object.

    This helper function constructs a `BrAPIResponse` object, populating the
    metadata with pagination details and a default success status.

    Args:
        data (any): The data to be included in the 'result' field of the response.
        page (int): The current page number.
        page_size (int): The number of items per page.
        total_count (int): The total number of items available.

    Returns:
        BrAPIResponse: A BrAPI response object containing the data and metadata.
    """
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
    """Lists locations with pagination.

    Retrieves a paginated list of locations, with an optional filter for
    location type.

    Args:
        page (int): The page number to retrieve.
        page_size (int): The number of locations per page.
        location_type (str): An optional filter for the location type.
        db (AsyncSession): The database session dependency.
        org_id (int): The organization ID of the current user.

    Returns:
        BrAPIResponse[dict]: A BrAPI response containing a list of locations.
    """
    filters = {}
    if location_type:
        filters['location_type'] = location_type

    skip = page * page_size
    locations, total_count = await location_crud.get_multi(
        db, skip=skip, limit=page_size, org_id=org_id, filters=filters if filters else None
    )

    location_list = [Location.model_validate(loc).model_dump(by_alias=True) for loc in locations]
    return create_brapi_response(location_list, page, page_size, total_count)


@router.get("/locations/{locationDbId}", response_model=BrAPIResponse[dict])
async def get_location(
    locationDbId: str,
    db: AsyncSession = Depends(get_db),
    org_id: int = Depends(get_organization_id)
):
    """Gets a single location by its database ID.

    Args:
        locationDbId (str): The database ID of the location to retrieve.
        db (AsyncSession): The database session dependency.
        org_id (int): The organization ID of the current user.

    Raises:
        HTTPException: If no location with the given ID is found.

    Returns:
        BrAPIResponse[dict]: A BrAPI response containing the location data.
    """
    location = await location_crud.get_by_db_id(db, locationDbId, org_id)

    if not location:
        raise HTTPException(status_code=404, detail="Location not found")

    location_data = Location.model_validate(location).model_dump(by_alias=True)
    metadata = Metadata(
        pagination=Pagination(current_page=0, page_size=1, total_count=1, total_pages=1),
        status=[Status(message="Success", message_type="INFO")]
    )

    return BrAPIResponse(metadata=metadata, result=location_data)


@router.post("/locations", response_model=BrAPIResponse[dict], status_code=201)
async def create_location(
    location_in: LocationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Creates a new location.

    Args:
        location_in (LocationCreate): The data for the new location.
        db (AsyncSession): The database session dependency.
        current_user (User): The currently authenticated user.

    Returns:
        BrAPIResponse[dict]: A BrAPI response containing the newly created
        location's data.
    """
    await set_tenant_context(db, current_user.organization_id, current_user.is_superuser)

    location = await location_crud.create(db, obj_in=location_in, org_id=current_user.organization_id)
    await db.commit()

    location_data = Location.model_validate(location).model_dump(by_alias=True)
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
    """Updates a location.

    Args:
        locationDbId (str): The database ID of the location to update.
        location_in (LocationUpdate): The data to update the location with.
        db (AsyncSession): The database session dependency.
        org_id (int): The organization ID of the current user.

    Raises:
        HTTPException: If no location with the given ID is found.

    Returns:
        BrAPIResponse[dict]: A BrAPI response containing the updated
        location's data.
    """
    location = await location_crud.get_by_db_id(db, locationDbId, org_id)

    if not location:
        raise HTTPException(status_code=404, detail="Location not found")

    location = await location_crud.update(db, db_obj=location, obj_in=location_in)
    await db.commit()

    location_data = Location.model_validate(location).model_dump(by_alias=True)
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
    """Deletes a location.

    Args:
        locationDbId (str): The database ID of the location to delete.
        db (AsyncSession): The database session dependency.
        org_id (int): The organization ID of the current user.

    Raises:
        HTTPException: If no location with the given ID is found.
    """
    location = await location_crud.get_by_db_id(db, locationDbId, org_id)

    if not location:
        raise HTTPException(status_code=404, detail="Location not found")

    await location_crud.delete(db, id=location.id)
    await db.commit()

    return None
