"""BrAPI Core Trials endpoints.

This module provides a FastAPI router for managing agricultural trials,
adhering to the BrAPI v2.0 specification for the 'trials' endpoint.
It includes endpoints for creating, retrieving, updating, listing, and
deleting trials within a specific organization's scope.

The BrAPI (Breeding API) is a standardized RESTful web service API
specification for exchanging plant breeding data.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import get_organization_id
from app.crud.core import trial as trial_crud
from app.schemas.core import Trial, TrialCreate, TrialUpdate
from app.schemas.brapi import BrAPIResponse, Metadata, Pagination, Status
from app.core.config import settings

router = APIRouter()


def create_brapi_response(data: any, page: int, page_size: int, total_count: int):
    """Constructs a standard BrAPI response object.

    Args:
        data: The main data payload for the response.
        page: The current page number.
        page_size: The number of items per page.
        total_count: The total number of items available.

    Returns:
        A BrAPIResponse object containing metadata and the result data.
    """
    total_pages = (total_count + page_size - 1) // page_size
    metadata = Metadata(
        pagination=Pagination(
            current_page=page, page_size=page_size,
            total_count=total_count, total_pages=total_pages
        ),
        status=[Status(message="Success", message_type="INFO")]
    )
    return BrAPIResponse(metadata=metadata, result={"data": data})


@router.get("/trials", response_model=BrAPIResponse[dict])
async def list_trials(
    page: int = Query(0, ge=0),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE),
    program_db_id: str = Query(None, alias="programDbId"),
    active: bool = Query(None),
    db: AsyncSession = Depends(get_db),
    org_id: int = Depends(get_organization_id)
):
    """Retrieves a paginated list of trials.

    This endpoint implements the BrAPI `GET /trials` call, allowing clients
    to fetch trials with filtering and pagination.

    Args:
        page: The page number to retrieve.
        page_size: The number of trials per page.
        program_db_id: Not currently implemented. Kept for BrAPI compatibility.
        active: Filter by the active status of the trial.
        db: The database session dependency.
        org_id: The organization ID, injected as a dependency.

    Returns:
        A BrAPI-formatted response containing a list of trials.
    """
    filters = {}
    if active is not None:
        filters['active'] = active
    
    skip = page * page_size
    trials, total_count = await trial_crud.get_multi(
        db, skip=skip, limit=page_size, org_id=org_id, filters=filters if filters else None
    )
    
    trial_list = [Trial.model_validate(t) for t in trials]
    return create_brapi_response(trial_list, page, page_size, total_count)


@router.get("/trials/{trialDbId}", response_model=BrAPIResponse[dict])
async def get_trial(
    trialDbId: str,
    db: AsyncSession = Depends(get_db),
    org_id: int = Depends(get_organization_id)
):
    """Retrieves a single trial by its database ID.

    Implements the BrAPI `GET /trials/{trialDbId}` endpoint.

    Args:
        trialDbId: The unique database identifier for a trial.
        db: The database session dependency.
        org_id: The organization ID, injected as a dependency.

    Returns:
        A BrAPI-formatted response containing the requested trial data.

    Raises:
        HTTPException: 404 Not Found if no trial with the given `trialDbId`
                       exists for the organization.
    """
    trial = await trial_crud.get_by_db_id(db, trialDbId, org_id)
    if not trial:
        raise HTTPException(status_code=404, detail="Trial not found")
    
    trial_data = Trial.model_validate(trial)
    metadata = Metadata(
        pagination=Pagination(current_page=0, page_size=1, total_count=1, total_pages=1),
        status=[Status(message="Success", message_type="INFO")]
    )
    return BrAPIResponse(metadata=metadata, result=trial_data)


@router.post("/trials", response_model=BrAPIResponse[dict], status_code=201)
async def create_trial(
    trial_in: TrialCreate,
    db: AsyncSession = Depends(get_db),
    org_id: int = Depends(get_organization_id)
):
    """Creates a new trial.

    Implements the BrAPI `POST /trials` endpoint. The new trial will be
    associated with the current user's organization.

    Args:
        trial_in: A `TrialCreate` schema object containing the new trial's data.
        db: The database session dependency.
        org_id: The organization ID, injected as a dependency.

    Returns:
        A BrAPI-formatted response containing the newly created trial data.
        The HTTP status code will be 201 Created.
    """
    trial = await trial_crud.create(db, obj_in=trial_in, org_id=org_id)
    await db.commit()
    
    trial_data = Trial.model_validate(trial)
    metadata = Metadata(
        pagination=Pagination(current_page=0, page_size=1, total_count=1, total_pages=1),
        status=[Status(message="Trial created successfully", message_type="INFO")]
    )
    return BrAPIResponse(metadata=metadata, result=trial_data)


@router.put("/trials/{trialDbId}", response_model=BrAPIResponse[dict])
async def update_trial(
    trialDbId: str,
    trial_in: TrialUpdate,
    db: AsyncSession = Depends(get_db),
    org_id: int = Depends(get_organization_id)
):
    """Updates an existing trial.

    Implements the BrAPI `PUT /trials/{trialDbId}` endpoint.

    Args:
        trialDbId: The database ID of the trial to update.
        trial_in: A `TrialUpdate` schema object with the fields to be updated.
        db: The database session dependency.
        org_id: The organization ID, injected as a dependency.

    Returns:
        A BrAPI-formatted response containing the updated trial data.

    Raises:
        HTTPException: 404 Not Found if no trial with the given `trialDbId`
                       exists for the organization.
    """
    trial = await trial_crud.get_by_db_id(db, trialDbId, org_id)
    if not trial:
        raise HTTPException(status_code=404, detail="Trial not found")
    
    trial = await trial_crud.update(db, db_obj=trial, obj_in=trial_in)
    await db.commit()
    
    trial_data = Trial.model_validate(trial)
    metadata = Metadata(
        pagination=Pagination(current_page=0, page_size=1, total_count=1, total_pages=1),
        status=[Status(message="Trial updated successfully", message_type="INFO")]
    )
    return BrAPIResponse(metadata=metadata, result=trial_data)


@router.delete("/trials/{trialDbId}", status_code=204)
async def delete_trial(
    trialDbId: str,
    db: AsyncSession = Depends(get_db),
    org_id: int = Depends(get_organization_id)
):
    """Deletes a trial.

    This endpoint is not part of the BrAPI v2.0 specification but is included
    for complete CRUD functionality. It permanently removes a trial record.

    Note:
        The BrAPI specification does not define a DELETE method for the
        `/trials/{trialDbId}` endpoint. This is a custom extension.

    Args:
        trialDbId: The database ID of the trial to delete.
        db: The database session dependency.
        org_id: The organization ID, injected as a dependency.

    Returns:
        None. A 204 No Content status code is returned on success.

    Raises:
        HTTPException: 404 Not Found if no trial with the given `trialDbId`
                       exists for the organization.
    """
    trial = await trial_crud.get_by_db_id(db, trialDbId, org_id)
    if not trial:
        raise HTTPException(status_code=404, detail="Trial not found")
    
    await trial_crud.delete(db, id=trial.id)
    await db.commit()
    
    return None
