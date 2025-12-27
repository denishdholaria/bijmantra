"""
BrAPI v2.1 Crosses Endpoints

Database-backed implementation (no in-memory demo data).
Demo data is seeded into Demo Organization via seeders.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
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
    """Convert SQLAlchemy model to BrAPI response format"""
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
    db: Session = Depends(get_db),
    current_user = Depends(get_optional_user),
):
    """Get list of crosses from database"""
    query = db.query(Cross)
    
    if crossingProjectDbId:
        query = query.join(CrossingProject).filter(
            CrossingProject.crossing_project_db_id == crossingProjectDbId
        )
    if crossType:
        query = query.filter(Cross.cross_type == crossType)
    if crossDbId:
        query = query.filter(Cross.cross_db_id == crossDbId)
    if crossName:
        query = query.filter(Cross.cross_name.ilike(f"%{crossName}%"))
    
    total = query.count()
    results = query.offset(page * pageSize).limit(pageSize).all()
    data = [_model_to_brapi(c) for c in results]
    
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
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """Create new cross in database"""
    org_id = current_user.organization_id if current_user else 1
    cross_db_id = f"cross_{uuid.uuid4().hex[:12]}"
    
    # Look up crossing project
    project_id = None
    if cross.crossingProjectDbId:
        project = db.query(CrossingProject).filter(
            CrossingProject.crossing_project_db_id == cross.crossingProjectDbId
        ).first()
        if project:
            project_id = project.id
    
    # Look up parents
    parent1_id = None
    parent2_id = None
    if cross.parent1DbId:
        p1 = db.query(Germplasm).filter(Germplasm.germplasm_db_id == cross.parent1DbId).first()
        if p1:
            parent1_id = p1.id
    if cross.parent2DbId:
        p2 = db.query(Germplasm).filter(Germplasm.germplasm_db_id == cross.parent2DbId).first()
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
    db.commit()
    db.refresh(new_cross)
    
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
    db: Session = Depends(get_db),
    current_user = Depends(get_optional_user)
):
    """Get cross by ID from database"""
    cross = db.query(Cross).filter(Cross.cross_db_id == crossDbId).first()
    
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
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """Update existing crosses (bulk)"""
    updated = []
    
    for cross_data in crosses:
        if not cross_data.crossDbId:
            continue
        
        cross = db.query(Cross).filter(Cross.cross_db_id == cross_data.crossDbId).first()
        
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
    
    db.commit()
    
    return {
        "metadata": {
            "datafiles": [],
            "pagination": {"currentPage": 0, "pageSize": len(updated), "totalCount": len(updated), "totalPages": 1},
            "status": [{"message": f"Updated {len(updated)} crosses", "messageType": "INFO"}]
        },
        "result": {"data": [_model_to_brapi(c) for c in updated]}
    }
