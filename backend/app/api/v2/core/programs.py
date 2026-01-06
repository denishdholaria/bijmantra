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
    """
    List breeding programs with pagination and filtering
    
    BrAPI Endpoint: GET /programs
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
    
    # Convert to response schema
    program_list = [Program.model_validate(p) for p in programs]
    
    return create_brapi_response(program_list, page, page_size, total_count)


@router.get("/programs/{programDbId}", response_model=BrAPIResponse[dict])
async def get_program(
    programDbId: str,
    db: AsyncSession = Depends(get_db),
    org_id: int = Depends(get_organization_id)
):
    """
    Get a single program by DbId
    
    BrAPI Endpoint: GET /programs/{programDbId}
    """
    program = await program_crud.get_by_db_id(db, programDbId, org_id)
    
    if not program:
        raise HTTPException(status_code=404, detail="Program not found")
    
    program_data = Program.model_validate(program)
    
    metadata = Metadata(
        pagination=Pagination(current_page=0, page_size=1, total_count=1, total_pages=1),
        status=[Status(message="Success", message_type="INFO")]
    )
    
    return BrAPIResponse(metadata=metadata, result=program_data)


@router.post("/programs", response_model=BrAPIResponse[dict], status_code=201)
async def create_program(
    program_in: ProgramCreate,
    db: AsyncSession = Depends(get_db),
    org_id: int = Depends(get_organization_id)
):
    """
    Create a new breeding program
    
    BrAPI Endpoint: POST /programs
    """
    program = await program_crud.create(db, obj_in=program_in, org_id=org_id)
    await db.commit()
    
    program_data = Program.model_validate(program)
    
    metadata = Metadata(
        pagination=Pagination(current_page=0, page_size=1, total_count=1, total_pages=1),
        status=[Status(message="Program created successfully", message_type="INFO")]
    )
    
    return BrAPIResponse(metadata=metadata, result=program_data)


@router.put("/programs/{programDbId}", response_model=BrAPIResponse[dict])
async def update_program(
    programDbId: str,
    program_in: ProgramUpdate,
    db: AsyncSession = Depends(get_db),
    org_id: int = Depends(get_organization_id)
):
    """
    Update a breeding program
    
    BrAPI Endpoint: PUT /programs/{programDbId}
    """
    program = await program_crud.get_by_db_id(db, programDbId, org_id)
    
    if not program:
        raise HTTPException(status_code=404, detail="Program not found")
    
    program = await program_crud.update(db, db_obj=program, obj_in=program_in)
    await db.commit()
    
    program_data = Program.model_validate(program)
    
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
    """
    Delete a breeding program
    
    BrAPI Endpoint: DELETE /programs/{programDbId}
    """
    program = await program_crud.get_by_db_id(db, programDbId, org_id)
    
    if not program:
        raise HTTPException(status_code=404, detail="Program not found")
    
    await program_crud.delete(db, id=program.id)
    await db.commit()
    
    return None
