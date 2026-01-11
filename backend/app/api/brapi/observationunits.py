"""
BrAPI v2.1 Observation Units Endpoints

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
from app.models.phenotyping import ObservationUnit
from app.models.core import Study
from app.models.germplasm import Germplasm

router = APIRouter()


class ObservationUnitBase(BaseModel):
    observationUnitName: str
    observationUnitPUI: Optional[str] = None
    studyDbId: Optional[str] = None
    germplasmDbId: Optional[str] = None
    germplasmName: Optional[str] = None
    crossDbId: Optional[str] = None
    seedLotDbId: Optional[str] = None
    observationLevel: Optional[str] = None
    observationLevelCode: Optional[str] = None
    observationLevelOrder: Optional[int] = None
    positionCoordinateX: Optional[str] = None
    positionCoordinateXType: Optional[str] = None
    positionCoordinateY: Optional[str] = None
    positionCoordinateYType: Optional[str] = None
    entryType: Optional[str] = None
    treatments: Optional[List[dict]] = None


class ObservationUnitCreate(ObservationUnitBase):
    pass


class ObservationUnitUpdate(ObservationUnitBase):
    observationUnitDbId: Optional[str] = None
    observationUnitName: Optional[str] = None


def _model_to_brapi(unit: ObservationUnit) -> dict:
    """Convert SQLAlchemy model to BrAPI response format"""
    return {
        "observationUnitDbId": unit.observation_unit_db_id,
        "observationUnitName": unit.observation_unit_name,
        "observationUnitPUI": unit.observation_unit_pui,
        "studyDbId": str(unit.study_id) if unit.study_id else None,
        "studyName": unit.study.study_name if unit.study else None,
        "germplasmDbId": str(unit.germplasm_id) if unit.germplasm_id else None,
        "germplasmName": unit.germplasm.germplasm_name if unit.germplasm else None,
        "crossDbId": unit.cross_db_id,
        "seedLotDbId": unit.seedlot_db_id,
        "observationLevel": unit.observation_level,
        "observationLevelCode": unit.observation_level_code,
        "observationLevelOrder": unit.observation_level_order,
        "positionCoordinateX": unit.position_coordinate_x,
        "positionCoordinateXType": unit.position_coordinate_x_type,
        "positionCoordinateY": unit.position_coordinate_y,
        "positionCoordinateYType": unit.position_coordinate_y_type,
        "entryType": unit.entry_type,
        "geoCoordinates": unit.geo_coordinates,
        "treatments": unit.treatments,
        "additionalInfo": unit.additional_info,
        "externalReferences": unit.external_references,
    }


@router.get("/observationunits")
async def list_observation_units(
    page: int = Query(0, ge=0),
    pageSize: int = Query(20, ge=1, le=1000),
    studyDbId: Optional[str] = None,
    germplasmDbId: Optional[str] = None,
    observationLevel: Optional[str] = None,
    observationUnitDbId: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_optional_user),
):
    """Get list of observation units from database"""
    # Build base statement with eager loading
    stmt = select(ObservationUnit).options(
        selectinload(ObservationUnit.study),
        selectinload(ObservationUnit.germplasm),
    )
    
    # Filter by user's organization (multi-tenant isolation)
    if current_user and current_user.organization_id:
        stmt = stmt.where(ObservationUnit.organization_id == current_user.organization_id)
    
    # Apply filters
    if studyDbId:
        stmt = stmt.where(ObservationUnit.study_id == int(studyDbId))
    if germplasmDbId:
        stmt = stmt.where(ObservationUnit.germplasm_id == int(germplasmDbId))
    if observationLevel:
        stmt = stmt.where(ObservationUnit.observation_level == observationLevel)
    if observationUnitDbId:
        stmt = stmt.where(ObservationUnit.observation_unit_db_id == observationUnitDbId)
    
    # Get total count
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total_result = await db.execute(count_stmt)
    total = total_result.scalar() or 0
    
    # Apply pagination and execute
    stmt = stmt.offset(page * pageSize).limit(pageSize)
    result = await db.execute(stmt)
    results = result.scalars().all()
    data = [_model_to_brapi(u) for u in results]
    
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


@router.post("/observationunits")
async def create_observation_unit(
    unit: ObservationUnitCreate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Create new observation unit in database"""
    org_id = current_user.organization_id if current_user else 1
    unit_db_id = f"ou_{uuid.uuid4().hex[:12]}"
    
    new_unit = ObservationUnit(
        organization_id=org_id,
        observation_unit_db_id=unit_db_id,
        observation_unit_name=unit.observationUnitName,
        observation_unit_pui=unit.observationUnitPUI,
        study_id=int(unit.studyDbId) if unit.studyDbId else None,
        germplasm_id=int(unit.germplasmDbId) if unit.germplasmDbId else None,
        cross_db_id=unit.crossDbId,
        seedlot_db_id=unit.seedLotDbId,
        observation_level=unit.observationLevel,
        observation_level_code=unit.observationLevelCode,
        observation_level_order=unit.observationLevelOrder,
        position_coordinate_x=unit.positionCoordinateX,
        position_coordinate_x_type=unit.positionCoordinateXType,
        position_coordinate_y=unit.positionCoordinateY,
        position_coordinate_y_type=unit.positionCoordinateYType,
        entry_type=unit.entryType,
        treatments=unit.treatments,
    )
    
    db.add(new_unit)
    await db.commit()
    await db.refresh(new_unit)
    
    return {
        "metadata": {
            "datafiles": [],
            "pagination": {"currentPage": 0, "pageSize": 1, "totalCount": 1, "totalPages": 1},
            "status": [{"message": "Observation unit created successfully", "messageType": "INFO"}]
        },
        "result": _model_to_brapi(new_unit)
    }


@router.get("/observationunits/{observationUnitDbId}")
async def get_observation_unit(
    observationUnitDbId: str,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_optional_user)
):
    """Get observation unit by ID from database"""
    stmt = select(ObservationUnit).options(
        selectinload(ObservationUnit.study),
        selectinload(ObservationUnit.germplasm),
    ).where(ObservationUnit.observation_unit_db_id == observationUnitDbId)
    
    result = await db.execute(stmt)
    unit = result.scalar_one_or_none()
    
    if not unit:
        raise HTTPException(status_code=404, detail="Observation unit not found")
    
    return {
        "metadata": {
            "datafiles": [],
            "pagination": {"currentPage": 0, "pageSize": 1, "totalCount": 1, "totalPages": 1},
            "status": []
        },
        "result": _model_to_brapi(unit)
    }


@router.put("/observationunits")
async def update_observation_units_bulk(
    units: List[ObservationUnitUpdate],
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """Update multiple observation units (bulk)"""
    updated = []
    
    for unit_data in units:
        if not unit_data.observationUnitDbId:
            continue
        
        stmt = select(ObservationUnit).options(
            selectinload(ObservationUnit.study),
            selectinload(ObservationUnit.germplasm),
        ).where(ObservationUnit.observation_unit_db_id == unit_data.observationUnitDbId)
        
        result = await db.execute(stmt)
        unit = result.scalar_one_or_none()
        
        if unit:
            if unit_data.observationUnitName:
                unit.observation_unit_name = unit_data.observationUnitName
            if unit_data.observationLevel:
                unit.observation_level = unit_data.observationLevel
            if unit_data.positionCoordinateX:
                unit.position_coordinate_x = unit_data.positionCoordinateX
            if unit_data.positionCoordinateY:
                unit.position_coordinate_y = unit_data.positionCoordinateY
            if unit_data.treatments:
                unit.treatments = unit_data.treatments
            
            updated.append(unit)
    
    await db.commit()
    
    return {
        "metadata": {
            "datafiles": [],
            "pagination": {"currentPage": 0, "pageSize": len(updated), "totalCount": len(updated), "totalPages": 1},
            "status": [{"message": f"Updated {len(updated)} observation units", "messageType": "INFO"}]
        },
        "result": {"data": [_model_to_brapi(u) for u in updated]}
    }


@router.put("/observationunits/{observationUnitDbId}")
async def update_observation_unit(
    observationUnitDbId: str,
    unit_data: ObservationUnitUpdate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """Update a single observation unit"""
    stmt = select(ObservationUnit).options(
        selectinload(ObservationUnit.study),
        selectinload(ObservationUnit.germplasm),
    ).where(ObservationUnit.observation_unit_db_id == observationUnitDbId)
    
    result = await db.execute(stmt)
    unit = result.scalar_one_or_none()
    
    if not unit:
        raise HTTPException(status_code=404, detail="Observation unit not found")
    
    if unit_data.observationUnitName:
        unit.observation_unit_name = unit_data.observationUnitName
    if unit_data.observationLevel:
        unit.observation_level = unit_data.observationLevel
    if unit_data.positionCoordinateX:
        unit.position_coordinate_x = unit_data.positionCoordinateX
    if unit_data.positionCoordinateY:
        unit.position_coordinate_y = unit_data.positionCoordinateY
    if unit_data.treatments:
        unit.treatments = unit_data.treatments
    
    await db.commit()
    await db.refresh(unit)
    
    return {
        "metadata": {
            "datafiles": [],
            "pagination": {"currentPage": 0, "pageSize": 1, "totalCount": 1, "totalPages": 1},
            "status": [{"message": "Observation unit updated successfully", "messageType": "INFO"}]
        },
        "result": _model_to_brapi(unit)
    }


@router.get("/observationunits/table")
async def get_observation_units_table(
    studyDbId: Optional[str] = None,
    observationLevel: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_optional_user),
):
    """Get observation units in table format"""
    stmt = select(ObservationUnit).options(
        selectinload(ObservationUnit.study),
        selectinload(ObservationUnit.germplasm),
    )
    
    if studyDbId:
        stmt = stmt.where(ObservationUnit.study_id == int(studyDbId))
    if observationLevel:
        stmt = stmt.where(ObservationUnit.observation_level == observationLevel)
    
    result = await db.execute(stmt)
    results = result.scalars().all()
    
    header_row = ["observationUnitDbId", "observationUnitName", "germplasmDbId", "germplasmName", "studyDbId", "observationLevel", "positionCoordinateX", "positionCoordinateY"]
    
    data_rows = []
    for unit in results:
        row = [
            unit.observation_unit_db_id,
            unit.observation_unit_name,
            str(unit.germplasm_id) if unit.germplasm_id else "",
            unit.germplasm.germplasm_name if unit.germplasm else "",
            str(unit.study_id) if unit.study_id else "",
            unit.observation_level or "",
            unit.position_coordinate_x or "",
            unit.position_coordinate_y or "",
        ]
        data_rows.append(row)
    
    return {
        "metadata": {
            "datafiles": [],
            "pagination": {"currentPage": 0, "pageSize": len(data_rows), "totalCount": len(data_rows), "totalPages": 1},
            "status": [{"message": "Request successful", "messageType": "INFO"}]
        },
        "result": {
            "headerRow": header_row,
            "data": data_rows
        }
    }
