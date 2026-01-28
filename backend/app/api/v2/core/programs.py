"""
BrAPI Core - Programs endpoints
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import get_organization_id
from app.crud.core import program as program_crud
from app.schemas.core import Program, ProgramCreate, ProgramUpdate
from app.schemas.brapi import BrAPIResponse, Metadata, Pagination, Status
from app.core.config import settings
from app.core.rls import set_tenant_context
from app.models.core import User
from app.api.deps import get_current_active_user

router = APIRouter()


def create_brapi_response(data: any, page: int, page_size: int, total_count: int):
    """Creates a BrAPI-formatted response with metadata.

    Args:
        data (any): The data to be included in the response.
        page (int): The current page number.
        page_size (int): The number of items per page.
        total_count (int): The total number of items.

    Returns:
        A BrAPIResponse object containing the formatted data and metadata.
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


@router.get("/programs", response_model=BrAPIResponse[dict])
async def list_programs(
    page: int = Query(0, ge=0, description="Page number"),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE),
    program_name: str = Query(None, alias="programName"),
    abbreviation: str = Query(None),
    common_crop_name: str = Query(None, alias="commonCropName"),
    db: AsyncSession = Depends(get_db),
    org_id: int = Depends(get_organization_id)
):
    """Lists breeding programs with pagination and filtering.

    Args:
        page (int): The page number to retrieve.
        page_size (int): The number of items per page.
        program_name (str): The name of the program to filter by.
        abbreviation (str): The abbreviation of the program to filter by.
        common_crop_name (str): The common crop name to filter by.
        db (AsyncSession): The database session.
        org_id (int): The ID of the organization.

    Returns:
        A BrAPIResponse object containing a list of programs.
    """
    # Build filters
    filters = {}
    if program_name:
        filters['program_name'] = program_name
    if abbreviation:
        filters['abbreviation'] = abbreviation
    
    # Get programs
    skip = page * page_size
    programs, total_count = await program_crud.get_multi(
        db,
        skip=skip,
        limit=page_size,
        org_id=org_id,
        filters=filters if filters else None
    )
    
    # Convert to response schema - must use model_dump for JSON serialization
    program_list = [Program.model_validate(p).model_dump(by_alias=True) for p in programs]
    
    return create_brapi_response(program_list, page, page_size, total_count)


@router.get("/programs/{programDbId}", response_model=BrAPIResponse[dict])
async def get_program(
    programDbId: str,
    db: AsyncSession = Depends(get_db),
    org_id: int = Depends(get_organization_id)
):
    """Gets a single program by its BrAPI-compliant database ID.

    Args:
        programDbId (str): The BrAPI-compliant database ID of the program.
        db (AsyncSession): The database session.
        org_id (int): The ID of the organization.

    Returns:
        A BrAPIResponse object containing the program data.

    Raises:
        HTTPException: If the program is not found.
    """
    program = await program_crud.get_by_db_id(db, programDbId, org_id)
    
    if not program:
        raise HTTPException(status_code=404, detail="Program not found")
    
    program_data = Program.model_validate(program).model_dump(by_alias=True)
    
    metadata = Metadata(
        pagination=Pagination(current_page=0, page_size=1, total_count=1, total_pages=1),
        status=[Status(message="Success", message_type="INFO")]
    )
    
    return BrAPIResponse(metadata=metadata, result=program_data)


@router.post("/programs", response_model=BrAPIResponse[dict], status_code=201)
async def create_program(
    program_in: ProgramCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Creates a new breeding program.

    Args:
        program_in (ProgramCreate): The program data to create.
        db (AsyncSession): The database session.
        current_user (User): The current authenticated user.

    Returns:
        A BrAPIResponse object containing the created program data.

    Raises:
        HTTPException: If a program with the same name already exists.
    """
    try:
        # logger.debug(f"create_program called for user {current_user.email} org_id={current_user.organization_id}")
        await set_tenant_context(db, current_user.organization_id, current_user.is_superuser)
        
        program = await program_crud.create(db, obj_in=program_in, org_id=current_user.organization_id)
        await db.commit()
        
        program_data = Program.model_validate(program).model_dump(by_alias=True)
        
        metadata = Metadata(
            pagination=Pagination(current_page=0, page_size=1, total_count=1, total_pages=1),
            status=[Status(message="Program created successfully", message_type="INFO")]
        )
        
        return BrAPIResponse(metadata=metadata, result=program_data)
    except Exception as e:
        # logger.error(f"create_program FAILED: {type(e).__name__}: {e}")
        raise


@router.put("/programs/{programDbId}", response_model=BrAPIResponse[dict])
async def update_program(
    programDbId: str,
    program_in: ProgramUpdate,
    db: AsyncSession = Depends(get_db),
    org_id: int = Depends(get_organization_id)
):
    """Updates a breeding program.

    Args:
        programDbId (str): The BrAPI-compliant database ID of the program to update.
        program_in (ProgramUpdate): The program data to update.
        db (AsyncSession): The database session.
        org_id (int): The ID of the organization.

    Returns:
        A BrAPIResponse object containing the updated program data.

    Raises:
        HTTPException: If the program is not found.
    """
    program = await program_crud.get_by_db_id(db, programDbId, org_id)
    
    if not program:
        raise HTTPException(status_code=404, detail="Program not found")
    
    program = await program_crud.update(db, db_obj=program, obj_in=program_in)
    await db.commit()
    
    program_data = Program.model_validate(program).model_dump(by_alias=True)
    
    metadata = Metadata(
        pagination=Pagination(current_page=0, page_size=1, total_count=1, total_pages=1),
        status=[Status(message="Program updated successfully", message_type="INFO")]
    )
    
    return BrAPIResponse(metadata=metadata, result=program_data)


@router.delete("/programs/{programDbId}", status_code=204)
async def delete_program(
    programDbId: str,
    db: AsyncSession = Depends(get_db),
    org_id: int = Depends(get_organization_id)
):
    """Deletes a breeding program.

    Args:
        programDbId (str): The BrAPI-compliant database ID of the program to delete.
        db (AsyncSession): The database session.
        org_id (int): The ID of the organization.

    Raises:
        HTTPException: If the program is not found.
    """
    program = await program_crud.get_by_db_id(db, programDbId, org_id)
    
    if not program:
        raise HTTPException(status_code=404, detail="Program not found")
    
    await program_crud.delete(db, id=program.id)
    await db.commit()
    
    return None
