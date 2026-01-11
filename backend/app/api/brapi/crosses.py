"""
BrAPI v2.1 Crosses Endpoints

Database-backed implementation (no in-memory demo data).
Demo data is seeded into Demo Organization via seeders.

GOVERNANCE.md §4.3.1 Compliant: Fully async implementation.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from pydantic import BaseModel
import uuid

from app.core.database import get_db
from app.api.deps import get_current_user, get_optional_user
from app.models.germplasm import Cross, CrossingProject, Germplasm

router = APIRouter()


class CrossBase(BaseModel):
    crossName: Optional[str] = None
    crossType: Optional[str] = None
    crossingProjectDbId: Optional[str] = None
    crossingProjectName: Optional[str] = None
    parent1DbId: Optional[str] = None
    parent1Name: Optional[str] = None
    parent1Type: Optional[str] = None
    parent2DbId: Optional[str] = None
    parent2Name: Optional[str] = None
    parent2Type: Optional[str] = None
    pollinationTimeStamp: Optional[str] = None
    plannedCrossDbId: Optional[str] = None
    crossingYear: Optional[int] = None


class CrossCreate(CrossBase):
    crossName: str


class CrossUpdate(CrossBase):
    crossDbId: Optional[str] = None


def _model_to_brapi(cross: Cross) -> dict:
    """Convert a Cross SQLAlchemy model to a BrAPI-compliant dictionary.

    Args:
        cross (Cross): The Cross object to convert.

    Returns:
        dict: A dictionary representing the Cross in BrAPI format.
    """
    return {
        "crossDbId": cross.cross_db_id,
        "crossName": cross.cross_name,
        "crossType": cross.cross_type,
        "crossingProjectDbId": cross.crossing_project.crossing_project_db_id if cross.crossing_project else None,
        "crossingProjectName": cross.crossing_project.crossing_project_name if cross.crossing_project else None,
        "parent1DbId": cross.parent1.germplasm_db_id if cross.parent1 else None,
        "parent1Name": cross.parent1.germplasm_name if cross.parent1 else None,
        "parent1Type": cross.parent1_type,
        "parent2DbId": cross.parent2.germplasm_db_id if cross.parent2 else None,
        "parent2Name": cross.parent2.germplasm_name if cross.parent2 else None,
        "parent2Type": cross.parent2_type,
        "pollinationTimeStamp": cross.pollination_time_stamp,
        "crossingYear": cross.crossing_year,
        "crossStatus": cross.cross_status,
        "additionalInfo": cross.additional_info,
        "externalReferences": cross.external_references,
    }


@router.get("/crosses")
async def list_crosses(
    page: int = Query(0, ge=0),
    pageSize: int = Query(20, ge=1, le=1000),
    crossingProjectDbId: Optional[str] = None,
    crossType: Optional[str] = None,
    crossDbId: Optional[str] = None,
    crossName: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_optional_user),
):
    """Get a list of crosses.

    Args:
        page (int): The page number to return.
        pageSize (int): The number of items to return per page.
        crossingProjectDbId (Optional[str]): The database ID of the crossing project to filter by.
        crossType (Optional[str]): The type of cross to filter by.
        crossDbId (Optional[str]): The database ID of the cross to filter by.
        crossName (Optional[str]): The name of the cross to filter by.
        db (AsyncSession): The database session.
        current_user: The current authenticated user.

    Returns:
        dict: A dictionary containing the list of crosses and metadata.
    """
    # Build base statement with eager loading for relationships
    stmt = select(Cross).options(
        selectinload(Cross.crossing_project),
        selectinload(Cross.parent1),
        selectinload(Cross.parent2),
    )
    
    # Filter by user's organization (multi-tenant isolation)
    if current_user and current_user.organization_id:
        stmt = stmt.where(Cross.organization_id == current_user.organization_id)
    
    # Apply filters
    if crossingProjectDbId:
        stmt = stmt.join(Cross.crossing_project).where(
            CrossingProject.crossing_project_db_id == crossingProjectDbId
        )
    if crossType:
        stmt = stmt.where(Cross.cross_type == crossType)
    if crossDbId:
        stmt = stmt.where(Cross.cross_db_id == crossDbId)
    if crossName:
        stmt = stmt.where(Cross.cross_name.ilike(f"%{crossName}%"))
    
    # Get total count
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total_result = await db.execute(count_stmt)
    total = total_result.scalar() or 0
    
    # Apply pagination
    stmt = stmt.offset(page * pageSize).limit(pageSize)
    
    # Execute query
    result = await db.execute(stmt)
    crosses = result.scalars().all()
    data = [_model_to_brapi(c) for c in crosses]
    
    return {
        "metadata": {
            "datafiles": [],
            "pagination": {
                "currentPage": page,
                "pageSize": pageSize,
                "totalCount": total,
                "totalPages": (total + pageSize - 1) // pageSize if total > 0 else 0
            },
            "status": [{"message": "Request successful", "messageType": "INFO"}]
        },
        "result": {"data": data}
    }


@router.post("/crosses")
async def create_cross(
    cross: CrossCreate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """Create a new cross.

    Args:
        cross (CrossCreate): The cross to create.
        db (AsyncSession): The database session.
        current_user: The current authenticated user.

    Returns:
        dict: A dictionary containing the newly created cross and metadata.
    """
    org_id = current_user.organization_id if current_user else 1
    cross_db_id = f"cross_{uuid.uuid4().hex[:12]}"
    
    # Look up crossing project
    project_id = None
    if cross.crossingProjectDbId:
        stmt = select(CrossingProject).where(
            CrossingProject.crossing_project_db_id == cross.crossingProjectDbId
        )
        result = await db.execute(stmt)
        project = result.scalar_one_or_none()
        if project:
            project_id = project.id
    
    # Look up parents
    parent1_id = None
    parent2_id = None
    if cross.parent1DbId:
        stmt = select(Germplasm).where(Germplasm.germplasm_db_id == cross.parent1DbId)
        result = await db.execute(stmt)
        p1 = result.scalar_one_or_none()
        if p1:
            parent1_id = p1.id
    if cross.parent2DbId:
        stmt = select(Germplasm).where(Germplasm.germplasm_db_id == cross.parent2DbId)
        result = await db.execute(stmt)
        p2 = result.scalar_one_or_none()
        if p2:
            parent2_id = p2.id
    
    new_cross = Cross(
        organization_id=org_id,
        cross_db_id=cross_db_id,
        cross_name=cross.crossName,
        cross_type=cross.crossType,
        crossing_project_id=project_id,
        parent1_db_id=parent1_id,
        parent1_type=cross.parent1Type,
        parent2_db_id=parent2_id,
        parent2_type=cross.parent2Type,
        pollination_time_stamp=cross.pollinationTimeStamp,
        crossing_year=cross.crossingYear,
    )
    
    db.add(new_cross)
    await db.flush()
    await db.refresh(new_cross, attribute_names=["crossing_project", "parent1", "parent2"])
    
    return {
        "metadata": {
            "datafiles": [],
            "pagination": {"currentPage": 0, "pageSize": 1, "totalCount": 1, "totalPages": 1},
            "status": [{"message": "Cross created successfully", "messageType": "INFO"}]
        },
        "result": _model_to_brapi(new_cross)
    }


@router.get("/crosses/{crossDbId}")
async def get_cross(
    crossDbId: str,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_optional_user)
):
    """Get a cross by its database ID.

    Args:
        crossDbId (str): The database ID of the cross to retrieve.
        db (AsyncSession): The database session.
        current_user: The current authenticated user.

    Raises:
        HTTPException: If the cross with the given ID is not found.

    Returns:
        dict: A dictionary containing the cross data and metadata.
    """
    stmt = select(Cross).options(
        selectinload(Cross.crossing_project),
        selectinload(Cross.parent1),
        selectinload(Cross.parent2),
    ).where(Cross.cross_db_id == crossDbId)
    
    result = await db.execute(stmt)
    cross = result.scalar_one_or_none()
    
    if not cross:
        raise HTTPException(status_code=404, detail="Cross not found")
    
    return {
        "metadata": {
            "datafiles": [],
            "pagination": {"currentPage": 0, "pageSize": 1, "totalCount": 1, "totalPages": 1},
            "status": []
        },
        "result": _model_to_brapi(cross)
    }


@router.put("/crosses")
async def update_crosses(
    crosses: List[CrossUpdate],
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """Update existing crosses in bulk.

    Args:
        crosses (List[CrossUpdate]): A list of cross objects to update.
        db (AsyncSession): The database session.
        current_user: The current authenticated user.

    Returns:
        dict: A dictionary containing the list of updated crosses and metadata.
    """
    updated = []
    
    for cross_data in crosses:
        if not cross_data.crossDbId:
            continue
        
        stmt = select(Cross).options(
            selectinload(Cross.crossing_project),
            selectinload(Cross.parent1),
            selectinload(Cross.parent2),
        ).where(Cross.cross_db_id == cross_data.crossDbId)
        
        result = await db.execute(stmt)
        cross = result.scalar_one_or_none()
        
        if cross:
            if cross_data.crossName:
                cross.cross_name = cross_data.crossName
            if cross_data.crossType:
                cross.cross_type = cross_data.crossType
            if cross_data.pollinationTimeStamp:
                cross.pollination_time_stamp = cross_data.pollinationTimeStamp
            if cross_data.crossingYear:
                cross.crossing_year = cross_data.crossingYear
            
            updated.append(cross)
    
    await db.flush()
    
    return {
        "metadata": {
            "datafiles": [],
            "pagination": {"currentPage": 0, "pageSize": len(updated), "totalCount": len(updated), "totalPages": 1},
            "status": [{"message": f"Updated {len(updated)} crosses", "messageType": "INFO"}]
        },
        "result": {"data": [_model_to_brapi(c) for c in updated]}
    }
