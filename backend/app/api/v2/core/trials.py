"""
BrAPI Core - Trials endpoints
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
    """List trials with pagination"""
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
    """Get a single trial by DbId"""
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
    """Create a new trial"""
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
    """Update a trial"""
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
