"""
BrAPI v2.1 Planned Crosses Endpoints
GET/POST/PUT /plannedcrosses

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
from app.models.germplasm import PlannedCross as PlannedCrossModel, CrossingProject, Germplasm

router = APIRouter()


class PlannedCrossParent(BaseModel):
    germplasmDbId: str
    germplasmName: Optional[str] = None
    observationUnitDbId: Optional[str] = None
    observationUnitName: Optional[str] = None
    parentType: str  # MALE, FEMALE, SELF, POPULATION


class PlannedCrossBase(BaseModel):
    crossingProjectDbId: Optional[str] = None
    crossingProjectName: Optional[str] = None
    crossType: Optional[str] = "BIPARENTAL"
    plannedCrossName: Optional[str] = None
    status: Optional[str] = "TODO"  # TODO, DONE, FAILED
    parent1: Optional[PlannedCrossParent] = None
    parent2: Optional[PlannedCrossParent] = None
    additionalInfo: dict = {}
    externalReferences: List[dict] = []


class PlannedCrossCreate(PlannedCrossBase):
    pass


class PlannedCrossUpdate(BaseModel):
    plannedCrossDbId: str
    crossingProjectDbId: Optional[str] = None
    crossType: Optional[str] = None
    plannedCrossName: Optional[str] = None
    status: Optional[str] = None
    parent1: Optional[PlannedCrossParent] = None
    parent2: Optional[PlannedCrossParent] = None
    additionalInfo: Optional[dict] = None


def model_to_dict(cross: PlannedCrossModel, project_name: str = None, 
                  parent1_name: str = None, parent2_name: str = None) -> Dict[str, Any]:
    """Convert PlannedCross model to BrAPI response dict"""
    result = {
        "plannedCrossDbId": cross.planned_cross_db_id,
        "plannedCrossName": cross.planned_cross_name,
        "crossingProjectDbId": None,
        "crossingProjectName": project_name,
        "crossType": cross.cross_type,
        "status": cross.status,
        "additionalInfo": cross.additional_info or {},
        "externalReferences": cross.external_references or [],
    }
    
    # Build parent1
    if cross.parent1_db_id:
        result["parent1"] = {
            "germplasmDbId": str(cross.parent1_db_id),
            "germplasmName": parent1_name,
            "parentType": cross.parent1_type or "FEMALE",
        }
    else:
        result["parent1"] = None
    
    # Build parent2
    if cross.parent2_db_id:
        result["parent2"] = {
            "germplasmDbId": str(cross.parent2_db_id),
            "germplasmName": parent2_name,
            "parentType": cross.parent2_type or "MALE",
        }
    else:
        result["parent2"] = None
    
    return result


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


@router.get("/plannedcrosses")
async def get_planned_crosses(
    page: int = Query(0, ge=0),
    pageSize: int = Query(1000, ge=1, le=2000),
    crossingProjectDbId: Optional[str] = Query(None),
    crossingProjectName: Optional[str] = Query(None),
    plannedCrossDbId: Optional[str] = Query(None),
    plannedCrossName: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    externalReferenceId: Optional[str] = Query(None, alias="externalReferenceID"),
    externalReferenceSource: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    org_id: int = Depends(get_organization_id)
):
    """
    Get list of planned crosses
    
    BrAPI Endpoint: GET /plannedcrosses
    """
    # Build query
    query = select(PlannedCrossModel).where(PlannedCrossModel.organization_id == org_id)
    
    if plannedCrossDbId:
        query = query.where(PlannedCrossModel.planned_cross_db_id == plannedCrossDbId)
    if plannedCrossName:
        query = query.where(PlannedCrossModel.planned_cross_name.ilike(f"%{plannedCrossName}%"))
    if status:
        query = query.where(PlannedCrossModel.status == status)
    if crossingProjectDbId:
        # Need to join with CrossingProject
        subquery = select(CrossingProject.id).where(
            CrossingProject.crossing_project_db_id == crossingProjectDbId
        )
        query = query.where(PlannedCrossModel.crossing_project_id.in_(subquery))
    
    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total_count = total_result.scalar() or 0
    
    # Apply pagination
    query = query.order_by(PlannedCrossModel.planned_cross_name)
    query = query.offset(page * pageSize).limit(pageSize)
    
    result = await db.execute(query)
    crosses = result.scalars().all()
    
    # Build response with related data
    result_data = []
    for cross in crosses:
        # Get project name if exists
        project_name = None
        if cross.crossing_project_id:
            proj_result = await db.execute(
                select(CrossingProject.crossing_project_name).where(
                    CrossingProject.id == cross.crossing_project_id
                )
            )
            project_name = proj_result.scalar()
        
        # Get parent names
        parent1_name = None
        parent2_name = None
        if cross.parent1_db_id:
            p1_result = await db.execute(
                select(Germplasm.germplasm_name).where(Germplasm.id == cross.parent1_db_id)
            )
            parent1_name = p1_result.scalar()
        if cross.parent2_db_id:
            p2_result = await db.execute(
                select(Germplasm.germplasm_name).where(Germplasm.id == cross.parent2_db_id)
            )
            parent2_name = p2_result.scalar()
        
        result_data.append(model_to_dict(cross, project_name, parent1_name, parent2_name))
    
    return create_response({"data": result_data}, page, pageSize, total_count)


@router.get("/plannedcrosses/{plannedCrossDbId}")
async def get_planned_cross(
    plannedCrossDbId: str,
    db: AsyncSession = Depends(get_db),
    org_id: int = Depends(get_organization_id)
):
    """Get a single planned cross by ID"""
    query = select(PlannedCrossModel).where(
        PlannedCrossModel.planned_cross_db_id == plannedCrossDbId,
        PlannedCrossModel.organization_id == org_id
    )
    result = await db.execute(query)
    cross = result.scalar_one_or_none()
    
    if not cross:
        raise HTTPException(status_code=404, detail="Planned cross not found")
    
    # Get related data
    project_name = None
    if cross.crossing_project_id:
        proj_result = await db.execute(
            select(CrossingProject.crossing_project_name).where(
                CrossingProject.id == cross.crossing_project_id
            )
        )
        project_name = proj_result.scalar()
    
    parent1_name = None
    parent2_name = None
    if cross.parent1_db_id:
        p1_result = await db.execute(
            select(Germplasm.germplasm_name).where(Germplasm.id == cross.parent1_db_id)
        )
        parent1_name = p1_result.scalar()
    if cross.parent2_db_id:
        p2_result = await db.execute(
            select(Germplasm.germplasm_name).where(Germplasm.id == cross.parent2_db_id)
        )
        parent2_name = p2_result.scalar()
    
    return create_response(model_to_dict(cross, project_name, parent1_name, parent2_name))


@router.post("/plannedcrosses", status_code=201)
async def create_planned_crosses(
    crosses: List[PlannedCrossCreate],
    db: AsyncSession = Depends(get_db),
    org_id: int = Depends(get_organization_id)
):
    """
    Create new planned crosses
    
    BrAPI Endpoint: POST /plannedcrosses
    """
    created = []
    
    for cross_in in crosses:
        cross_id = f"pc-{uuid.uuid4().hex[:8]}"
        
        # Resolve crossing project ID
        project_id = None
        if cross_in.crossingProjectDbId:
            proj_result = await db.execute(
                select(CrossingProject.id).where(
                    CrossingProject.crossing_project_db_id == cross_in.crossingProjectDbId,
                    CrossingProject.organization_id == org_id
                )
            )
            project_id = proj_result.scalar()
        
        # Resolve parent IDs
        parent1_id = None
        parent2_id = None
        if cross_in.parent1 and cross_in.parent1.germplasmDbId:
            p1_result = await db.execute(
                select(Germplasm.id).where(
                    Germplasm.germplasm_db_id == cross_in.parent1.germplasmDbId,
                    Germplasm.organization_id == org_id
                )
            )
            parent1_id = p1_result.scalar()
        if cross_in.parent2 and cross_in.parent2.germplasmDbId:
            p2_result = await db.execute(
                select(Germplasm.id).where(
                    Germplasm.germplasm_db_id == cross_in.parent2.germplasmDbId,
                    Germplasm.organization_id == org_id
                )
            )
            parent2_id = p2_result.scalar()
        
        new_cross = PlannedCrossModel(
            organization_id=org_id,
            crossing_project_id=project_id,
            planned_cross_db_id=cross_id,
            planned_cross_name=cross_in.plannedCrossName,
            cross_type=cross_in.crossType,
            parent1_db_id=parent1_id,
            parent1_type=cross_in.parent1.parentType if cross_in.parent1 else None,
            parent2_db_id=parent2_id,
            parent2_type=cross_in.parent2.parentType if cross_in.parent2 else None,
            status=cross_in.status,
            additional_info=cross_in.additionalInfo,
            external_references=cross_in.externalReferences,
        )
        
        db.add(new_cross)
        created.append(new_cross)
    
    await db.commit()
    
    # Build response
    result_data = []
    for cross in created:
        await db.refresh(cross)
        result_data.append(model_to_dict(cross))
    
    return create_response({"data": result_data}, total_count=len(result_data))


@router.put("/plannedcrosses")
async def update_planned_crosses(
    crosses: List[PlannedCrossUpdate],
    db: AsyncSession = Depends(get_db),
    org_id: int = Depends(get_organization_id)
):
    """
    Update planned crosses
    
    BrAPI Endpoint: PUT /plannedcrosses
    """
    updated = []
    
    for cross_in in crosses:
        cross_id = cross_in.plannedCrossDbId
        
        # Find existing
        query = select(PlannedCrossModel).where(
            PlannedCrossModel.planned_cross_db_id == cross_id,
            PlannedCrossModel.organization_id == org_id
        )
        result = await db.execute(query)
        cross = result.scalar_one_or_none()
        
        if not cross:
            # Create new if doesn't exist
            cross = PlannedCrossModel(
                organization_id=org_id,
                planned_cross_db_id=cross_id,
                planned_cross_name=cross_in.plannedCrossName,
                cross_type=cross_in.crossType or "BIPARENTAL",
                status=cross_in.status or "TODO",
                additional_info=cross_in.additionalInfo or {},
            )
            db.add(cross)
        else:
            # Update existing
            if cross_in.plannedCrossName is not None:
                cross.planned_cross_name = cross_in.plannedCrossName
            if cross_in.crossType is not None:
                cross.cross_type = cross_in.crossType
            if cross_in.status is not None:
                cross.status = cross_in.status
            if cross_in.additionalInfo is not None:
                cross.additional_info = cross_in.additionalInfo
            
            # Update parents if provided
            if cross_in.parent1:
                if cross_in.parent1.germplasmDbId:
                    p1_result = await db.execute(
                        select(Germplasm.id).where(
                            Germplasm.germplasm_db_id == cross_in.parent1.germplasmDbId,
                            Germplasm.organization_id == org_id
                        )
                    )
                    cross.parent1_db_id = p1_result.scalar()
                cross.parent1_type = cross_in.parent1.parentType
            
            if cross_in.parent2:
                if cross_in.parent2.germplasmDbId:
                    p2_result = await db.execute(
                        select(Germplasm.id).where(
                            Germplasm.germplasm_db_id == cross_in.parent2.germplasmDbId,
                            Germplasm.organization_id == org_id
                        )
                    )
                    cross.parent2_db_id = p2_result.scalar()
                cross.parent2_type = cross_in.parent2.parentType
        
        updated.append(cross)
    
    await db.commit()
    
    # Build response
    result_data = []
    for cross in updated:
        await db.refresh(cross)
        result_data.append(model_to_dict(cross))
    
    return create_response({"data": result_data}, total_count=len(result_data))


@router.delete("/plannedcrosses/{plannedCrossDbId}")
async def delete_planned_cross(
    plannedCrossDbId: str,
    db: AsyncSession = Depends(get_db),
    org_id: int = Depends(get_organization_id)
):
    """Delete a planned cross"""
    query = select(PlannedCrossModel).where(
        PlannedCrossModel.planned_cross_db_id == plannedCrossDbId,
        PlannedCrossModel.organization_id == org_id
    )
    result = await db.execute(query)
    cross = result.scalar_one_or_none()
    
    if not cross:
        raise HTTPException(status_code=404, detail="Planned cross not found")
    
    await db.delete(cross)
    await db.commit()
    
    return {"message": "Planned cross deleted successfully"}
