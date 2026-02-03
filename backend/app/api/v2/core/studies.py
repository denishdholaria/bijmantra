"""
BrAPI Core - Studies endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import get_organization_id, get_current_active_user
from app.crud.core import study as study_crud
from app.schemas.core import Study, StudyCreate, StudyUpdate
from app.schemas.brapi import BrAPIResponse, Metadata, Pagination, Status
from app.core.config import settings
from app.core.rls import set_tenant_context
from app.models.core import User

router = APIRouter()


def create_brapi_response(data: any, page: int, page_size: int, total_count: int):
    """Creates a BrAPI response object.

    Args:
        data (any): The data to be returned in the response.
        page (int): The current page number.
        page_size (int): The number of items per page.
        total_count (int): The total number of items.

    Returns:
        A BrAPIResponse object.
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


@router.get("/studies", response_model=BrAPIResponse[dict])
async def list_studies(
    page: int = Query(0, ge=0),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE),
    trial_db_id: str = Query(None, alias="trialDbId"),
    active: bool = Query(None),
    db: AsyncSession = Depends(get_db),
    org_id: int = Depends(get_organization_id)
):
    """List studies with pagination.

    Args:
        page (int): The page number to return.
        page_size (int): The number of items to return per page.
        trial_db_id (str): The trialDbId to filter by.
        active (bool): Whether to filter by active studies.
        db (AsyncSession): The database session.
        org_id (int): The organization ID.

    Returns:
        BrAPIResponse[dict]: A BrAPIResponse object containing a list of studies.
    """
    filters = {}
    if active is not None:
        filters['active'] = active
    
    skip = page * page_size
    studies, total_count = await study_crud.get_multi(
        db, skip=skip, limit=page_size, org_id=org_id, filters=filters if filters else None
    )
    
    study_list = [Study.model_validate(s).model_dump(by_alias=True) for s in studies]
    return create_brapi_response(study_list, page, page_size, total_count)


@router.get("/studies/{studyDbId}", response_model=BrAPIResponse[dict])
async def get_study(
    studyDbId: str,
    db: AsyncSession = Depends(get_db),
    org_id: int = Depends(get_organization_id)
):
    """Get a single study by its database ID.

    Args:
        studyDbId (str): The database ID of the study to return.
        db (AsyncSession): The database session.
        org_id (int): The organization ID.

    Returns:
        BrAPIResponse[dict]: A BrAPIResponse object containing the study.

    Raises:
        HTTPException: If the study is not found.
    """
    study = await study_crud.get_by_db_id(db, studyDbId, org_id)
    if not study:
        raise HTTPException(status_code=404, detail="Study not found")
    
    study_data = Study.model_validate(study).model_dump(by_alias=True)
    metadata = Metadata(
        pagination=Pagination(current_page=0, page_size=1, total_count=1, total_pages=1),
        status=[Status(message="Success", message_type="INFO")]
    )
    return BrAPIResponse(metadata=metadata, result=study_data)


@router.post("/studies", response_model=BrAPIResponse[dict], status_code=201)
async def create_study(
    study_in: StudyCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create a new study.

    Args:
        study_in (StudyCreate): The study to create.
        db (AsyncSession): The database session.
        current_user (User): The current user.

    Returns:
        BrAPIResponse[dict]: A BrAPIResponse object containing the created study.
    """
    await set_tenant_context(db, current_user.organization_id, current_user.is_superuser)
    
    study = await study_crud.create(db, obj_in=study_in, org_id=current_user.organization_id)
    await db.commit()
    
    study_data = Study.model_validate(study).model_dump(by_alias=True)
    metadata = Metadata(
        pagination=Pagination(current_page=0, page_size=1, total_count=1, total_pages=1),
        status=[Status(message="Study created successfully", message_type="INFO")]
    )
    return BrAPIResponse(metadata=metadata, result=study_data)


@router.put("/studies/{studyDbId}", response_model=BrAPIResponse[dict])
async def update_study(
    studyDbId: str,
    study_in: StudyUpdate,
    db: AsyncSession = Depends(get_db),
    org_id: int = Depends(get_organization_id)
):
    """Update an existing study.

    Args:
        studyDbId (str): The database ID of the study to update.
        study_in (StudyUpdate): The study data to update.
        db (AsyncSession): The database session.
        org_id (int): The organization ID.

    Returns:
        BrAPIResponse[dict]: A BrAPIResponse object containing the updated study.

    Raises:
        HTTPException: If the study is not found.
    """
    study = await study_crud.get_by_db_id(db, studyDbId, org_id)
    if not study:
        raise HTTPException(status_code=404, detail="Study not found")
    
    study = await study_crud.update(db, db_obj=study, obj_in=study_in)
    await db.commit()
    
    study_data = Study.model_validate(study).model_dump(by_alias=True)
    metadata = Metadata(
        pagination=Pagination(current_page=0, page_size=1, total_count=1, total_pages=1),
        status=[Status(message="Study updated successfully", message_type="INFO")]
    )
    return BrAPIResponse(metadata=metadata, result=study_data)


@router.delete("/studies/{studyDbId}", status_code=204)
async def delete_study(
    studyDbId: str,
    db: AsyncSession = Depends(get_db),
    org_id: int = Depends(get_organization_id)
):
    """Delete a study.

    Args:
        studyDbId (str): The database ID of the study to delete.
        db (AsyncSession): The database session.
        org_id (int): The organization ID.

    Raises:
        HTTPException: If the study is not found.
    """
    study = await study_crud.get_by_db_id(db, studyDbId, org_id)
    if not study:
        raise HTTPException(status_code=404, detail="Study not found")
    
    await study_crud.delete(db, id=study.id)
    await db.commit()
    
    return None
