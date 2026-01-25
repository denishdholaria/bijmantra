"""
BrAPI v2.1 Crossing Projects Endpoints
GET/POST /crossingprojects
GET/PUT /crossingprojects/{crossingProjectDbId}

Database-backed implementation for production use.
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Query, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pydantic import BaseModel
import uuid

from app.core.database import get_db
from app.api.deps import get_organization_id
from app.models.germplasm import CrossingProject as CrossingProjectModel
from app.models.core import Program

router = APIRouter()


class CrossingProjectBase(BaseModel):
    crossingProjectName: str
    crossingProjectDescription: Optional[str] = None
    programDbId: Optional[str] = None
    programName: Optional[str] = None
    commonCropName: Optional[str] = None
    potentialParentDbIds: Optional[List[str]] = []
    additionalInfo: dict = {}
    externalReferences: List[dict] = []


class CrossingProjectCreate(CrossingProjectBase):
    pass


class CrossingProjectUpdate(BaseModel):
    crossingProjectName: Optional[str] = None
    crossingProjectDescription: Optional[str] = None
    programDbId: Optional[str] = None
    programName: Optional[str] = None
    potentialParentDbIds: Optional[List[str]] = None
    additionalInfo: Optional[dict] = None


def model_to_dict(project: CrossingProjectModel, program_name: str = None) -> Dict[str, Any]:
    """Convert CrossingProject model to BrAPI response dict"""
    return {
        "crossingProjectDbId": project.crossing_project_db_id,
        "crossingProjectName": project.crossing_project_name,
        "crossingProjectDescription": project.crossing_project_description,
        "programDbId": None,  # Would need to look up program_db_id
        "programName": program_name,
        "commonCropName": project.common_crop_name,
        "potentialParentDbIds": [],  # Not stored in current model
        "additionalInfo": project.additional_info or {},
        "externalReferences": project.external_references or [],
    }


def create_response(data, page=0, page_size=1000, total_count=1):
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


@router.get("/crossingprojects")
async def get_crossing_projects(
    page: int = Query(0, ge=0),
    pageSize: int = Query(1000, ge=1, le=2000),
    crossingProjectDbId: Optional[str] = Query(None),
    crossingProjectName: Optional[str] = Query(None),
    programDbId: Optional[str] = Query(None),
    commonCropName: Optional[str] = Query(None),
    externalReferenceId: Optional[str] = Query(None, alias="externalReferenceID"),
    externalReferenceSource: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    org_id: int = Depends(get_organization_id)
):
    """
    Get list of crossing projects
    
    BrAPI Endpoint: GET /crossingprojects
    """
    # Build query
    query = select(CrossingProjectModel).where(CrossingProjectModel.organization_id == org_id)
    
    if crossingProjectDbId:
        query = query.where(CrossingProjectModel.crossing_project_db_id == crossingProjectDbId)
    if crossingProjectName:
        query = query.where(CrossingProjectModel.crossing_project_name.ilike(f"%{crossingProjectName}%"))
    if commonCropName:
        query = query.where(CrossingProjectModel.common_crop_name == commonCropName)
    if programDbId:
        # Join with Program to filter by program_db_id
        subquery = select(Program.id).where(Program.program_db_id == programDbId)
        query = query.where(CrossingProjectModel.program_id.in_(subquery))
    
    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total_count = total_result.scalar() or 0
    
    # Apply pagination
    query = query.order_by(CrossingProjectModel.crossing_project_name)
    query = query.offset(page * pageSize).limit(pageSize)
    
    result = await db.execute(query)
    projects = result.scalars().all()
    
    # Build response with related data
    result_data = []
    for project in projects:
        # Get program name if exists
        program_name = None
        if project.program_id:
            prog_result = await db.execute(
                select(Program.program_name).where(Program.id == project.program_id)
            )
            program_name = prog_result.scalar()
        
        result_data.append(model_to_dict(project, program_name))
    
    return create_response({"data": result_data}, page, pageSize, total_count)


@router.get("/crossingprojects/{crossingProjectDbId}")
async def get_crossing_project(
    crossingProjectDbId: str,
    db: AsyncSession = Depends(get_db),
    org_id: int = Depends(get_organization_id)
):
    """
    Get a single crossing project by DbId
    
    BrAPI Endpoint: GET /crossingprojects/{crossingProjectDbId}
    """
    query = select(CrossingProjectModel).where(
        CrossingProjectModel.crossing_project_db_id == crossingProjectDbId,
        CrossingProjectModel.organization_id == org_id
    )
    result = await db.execute(query)
    project = result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(status_code=404, detail="Crossing project not found")
    
    # Get program name
    program_name = None
    if project.program_id:
        prog_result = await db.execute(
            select(Program.program_name).where(Program.id == project.program_id)
        )
        program_name = prog_result.scalar()
    
    return create_response(model_to_dict(project, program_name))


@router.post("/crossingprojects", status_code=201)
async def create_crossing_projects(
    projects: List[CrossingProjectCreate],
    db: AsyncSession = Depends(get_db),
    org_id: int = Depends(get_organization_id)
):
    """
    Create new crossing projects
    
    BrAPI Endpoint: POST /crossingprojects
    """
    created = []
    
    for proj_in in projects:
        proj_id = f"cp-{uuid.uuid4().hex[:8]}"
        
        # Resolve program ID if provided
        program_id = None
        if proj_in.programDbId:
            prog_result = await db.execute(
                select(Program.id).where(
                    Program.program_db_id == proj_in.programDbId,
                    Program.organization_id == org_id
                )
            )
            program_id = prog_result.scalar()
        
        new_project = CrossingProjectModel(
            organization_id=org_id,
            program_id=program_id,
            crossing_project_db_id=proj_id,
            crossing_project_name=proj_in.crossingProjectName,
            crossing_project_description=proj_in.crossingProjectDescription,
            common_crop_name=proj_in.commonCropName,
            additional_info=proj_in.additionalInfo,
            external_references=proj_in.externalReferences,
        )
        
        db.add(new_project)
        created.append(new_project)
    
    await db.commit()
    
    # Build response
    result_data = []
    for project in created:
        await db.refresh(project)
        result_data.append(model_to_dict(project))
    
    return create_response({"data": result_data}, total_count=len(result_data))


@router.put("/crossingprojects/{crossingProjectDbId}")
async def update_crossing_project(
    crossingProjectDbId: str,
    proj_in: CrossingProjectUpdate,
    db: AsyncSession = Depends(get_db),
    org_id: int = Depends(get_organization_id)
):
    """
    Update a crossing project
    
    BrAPI Endpoint: PUT /crossingprojects/{crossingProjectDbId}
    """
    query = select(CrossingProjectModel).where(
        CrossingProjectModel.crossing_project_db_id == crossingProjectDbId,
        CrossingProjectModel.organization_id == org_id
    )
    result = await db.execute(query)
    project = result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(status_code=404, detail="Crossing project not found")
    
    # Update fields
    if proj_in.crossingProjectName is not None:
        project.crossing_project_name = proj_in.crossingProjectName
    if proj_in.crossingProjectDescription is not None:
        project.crossing_project_description = proj_in.crossingProjectDescription
    if proj_in.additionalInfo is not None:
        project.additional_info = proj_in.additionalInfo
    
    # Update program if provided
    if proj_in.programDbId is not None:
        prog_result = await db.execute(
            select(Program.id).where(
                Program.program_db_id == proj_in.programDbId,
                Program.organization_id == org_id
            )
        )
        project.program_id = prog_result.scalar()
    
    await db.commit()
    await db.refresh(project)
    
    # Get program name for response
    program_name = None
    if project.program_id:
        prog_result = await db.execute(
            select(Program.program_name).where(Program.id == project.program_id)
        )
        program_name = prog_result.scalar()
    
    return create_response(model_to_dict(project, program_name))


@router.delete("/crossingprojects/{crossingProjectDbId}")
async def delete_crossing_project(
    crossingProjectDbId: str,
    db: AsyncSession = Depends(get_db),
    org_id: int = Depends(get_organization_id)
):
    """Delete a crossing project"""
    query = select(CrossingProjectModel).where(
        CrossingProjectModel.crossing_project_db_id == crossingProjectDbId,
        CrossingProjectModel.organization_id == org_id
    )
    result = await db.execute(query)
    project = result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(status_code=404, detail="Crossing project not found")
    
    await db.delete(project)
    await db.commit()
    
    return {"message": "Crossing project deleted successfully"}
