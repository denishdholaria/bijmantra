"""
BrAPI v2.1 Observations Endpoints

Database-backed implementation (no in-memory demo data).
Demo data is seeded into Demo Organization via seeders.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime
import uuid

from app.core.database import get_db
from app.api.deps import get_current_user, get_optional_user
from app.models.phenotyping import Observation, ObservationVariable, ObservationUnit

router = APIRouter()


class ObservationBase(BaseModel):
    observationUnitDbId: Optional[str] = None
    observationVariableDbId: Optional[str] = None
    observationVariableName: Optional[str] = None
    value: Optional[str] = None
    observationTimeStamp: Optional[str] = None
    collector: Optional[str] = None
    studyDbId: Optional[str] = None
    germplasmDbId: Optional[str] = None
    germplasmName: Optional[str] = None
    seasonDbId: Optional[str] = None


class ObservationCreate(ObservationBase):
    pass


class ObservationUpdate(ObservationBase):
    observationDbId: Optional[str] = None


def _model_to_brapi(obs: Observation) -> dict:
    """Convert SQLAlchemy model to BrAPI response format"""
    return {
        "observationDbId": obs.observation_db_id,
        "observationUnitDbId": obs.observation_unit.observation_unit_db_id if obs.observation_unit else None,
        "observationVariableDbId": obs.observation_variable.observation_variable_db_id if obs.observation_variable else None,
        "observationVariableName": obs.observation_variable.observation_variable_name if obs.observation_variable else None,
        "value": obs.value,
        "observationTimeStamp": obs.observation_time_stamp,
        "collector": obs.collector,
        "studyDbId": str(obs.study_id) if obs.study_id else None,
        "germplasmDbId": str(obs.germplasm_id) if obs.germplasm_id else None,
        "seasonDbId": obs.season_db_id,
        "additionalInfo": obs.additional_info,
        "externalReferences": obs.external_references,
    }


@router.get("/observations")
async def list_observations(
    page: int = Query(0, ge=0),
    pageSize: int = Query(20, ge=1, le=1000),
    studyDbId: Optional[str] = None,
    germplasmDbId: Optional[str] = None,
    observationVariableDbId: Optional[str] = None,
    observationUnitDbId: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_optional_user),
):
    """Get list of observations from database"""
    query = db.query(Observation)
    
    # Apply filters
    if studyDbId:
        query = query.filter(Observation.study_id == int(studyDbId))
    if germplasmDbId:
        query = query.filter(Observation.germplasm_id == int(germplasmDbId))
    if observationVariableDbId:
        query = query.join(ObservationVariable).filter(
            ObservationVariable.observation_variable_db_id == observationVariableDbId
        )
    if observationUnitDbId:
        query = query.join(ObservationUnit).filter(
            ObservationUnit.observation_unit_db_id == observationUnitDbId
        )
    
    total = query.count()
    results = query.offset(page * pageSize).limit(pageSize).all()
    data = [_model_to_brapi(obs) for obs in results]
    
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


@router.post("/observations")
async def create_observation(
    observation: ObservationCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Create new observation in database"""
    org_id = current_user.organization_id if current_user else 1
    obs_db_id = f"obs_{uuid.uuid4().hex[:12]}"
    
    # Look up related entities
    obs_unit_id = None
    obs_var_id = None
    
    if observation.observationUnitDbId:
        unit = db.query(ObservationUnit).filter(
            ObservationUnit.observation_unit_db_id == observation.observationUnitDbId
        ).first()
        if unit:
            obs_unit_id = unit.id
    
    if observation.observationVariableDbId:
        var = db.query(ObservationVariable).filter(
            ObservationVariable.observation_variable_db_id == observation.observationVariableDbId
        ).first()
        if var:
            obs_var_id = var.id
    
    new_obs = Observation(
        organization_id=org_id,
        observation_db_id=obs_db_id,
        observation_unit_id=obs_unit_id,
        observation_variable_id=obs_var_id,
        value=observation.value,
        observation_time_stamp=observation.observationTimeStamp or datetime.utcnow().isoformat() + "Z",
        collector=observation.collector,
        season_db_id=observation.seasonDbId,
    )
    
    db.add(new_obs)
    db.commit()
    db.refresh(new_obs)
    
    return {
        "metadata": {
            "datafiles": [],
            "pagination": {"currentPage": 0, "pageSize": 1, "totalCount": 1, "totalPages": 1},
            "status": [{"message": "Observation created successfully", "messageType": "INFO"}]
        },
        "result": _model_to_brapi(new_obs)
    }


@router.get("/observations/{observationDbId}")
async def get_observation(
    observationDbId: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_optional_user)
):
    """Get observation by ID from database"""
    obs = db.query(Observation).filter(
        Observation.observation_db_id == observationDbId
    ).first()
    
    if not obs:
        raise HTTPException(status_code=404, detail="Observation not found")
    
    return {
        "metadata": {
            "datafiles": [],
            "pagination": {"currentPage": 0, "pageSize": 1, "totalCount": 1, "totalPages": 1},
            "status": []
        },
        "result": _model_to_brapi(obs)
    }


@router.put("/observations")
async def update_observations(
    observations: List[ObservationUpdate],
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """Update existing observations (bulk)"""
    updated = []
    
    for obs_data in observations:
        if not obs_data.observationDbId:
            continue
        
        obs = db.query(Observation).filter(
            Observation.observation_db_id == obs_data.observationDbId
        ).first()
        
        if obs:
            if obs_data.value is not None:
                obs.value = obs_data.value
            if obs_data.collector is not None:
                obs.collector = obs_data.collector
            if obs_data.observationTimeStamp is not None:
                obs.observation_time_stamp = obs_data.observationTimeStamp
            if obs_data.seasonDbId is not None:
                obs.season_db_id = obs_data.seasonDbId
            
            updated.append(obs)
    
    db.commit()
    
    return {
        "metadata": {
            "datafiles": [],
            "pagination": {"currentPage": 0, "pageSize": len(updated), "totalCount": len(updated), "totalPages": 1},
            "status": [{"message": f"Updated {len(updated)} observations", "messageType": "INFO"}]
        },
        "result": {"data": [_model_to_brapi(obs) for obs in updated]}
    }


@router.put("/observations/{observationDbId}")
async def update_observation(
    observationDbId: str,
    observation: ObservationCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """Update a single observation"""
    obs = db.query(Observation).filter(
        Observation.observation_db_id == observationDbId
    ).first()
    
    if not obs:
        raise HTTPException(status_code=404, detail="Observation not found")
    
    if observation.value is not None:
        obs.value = observation.value
    if observation.collector is not None:
        obs.collector = observation.collector
    if observation.observationTimeStamp is not None:
        obs.observation_time_stamp = observation.observationTimeStamp
    if observation.seasonDbId is not None:
        obs.season_db_id = observation.seasonDbId
    
    db.commit()
    db.refresh(obs)
    
    return {
        "metadata": {
            "datafiles": [],
            "pagination": {"currentPage": 0, "pageSize": 1, "totalCount": 1, "totalPages": 1},
            "status": [{"message": "Observation updated successfully", "messageType": "INFO"}]
        },
        "result": _model_to_brapi(obs)
    }


@router.get("/observations/table")
async def get_observations_table(
    studyDbId: Optional[str] = None,
    observationUnitDbId: Optional[List[str]] = Query(None),
    observationVariableDbId: Optional[List[str]] = Query(None),
    germplasmDbId: Optional[List[str]] = Query(None),
    db: Session = Depends(get_db),
    current_user = Depends(get_optional_user),
):
    """Get observations in table format"""
    query = db.query(Observation)
    
    if studyDbId:
        query = query.filter(Observation.study_id == int(studyDbId))
    if observationUnitDbId:
        query = query.join(ObservationUnit).filter(
            ObservationUnit.observation_unit_db_id.in_(observationUnitDbId)
        )
    if observationVariableDbId:
        query = query.join(ObservationVariable).filter(
            ObservationVariable.observation_variable_db_id.in_(observationVariableDbId)
        )
    if germplasmDbId:
        query = query.filter(Observation.germplasm_id.in_([int(g) for g in germplasmDbId]))
    
    results = query.all()
    
    # Get unique variables
    variables = list(set(
        obs.observation_variable.observation_variable_name 
        for obs in results 
        if obs.observation_variable
    ))
    
    # Build header row
    header_row = ["observationUnitDbId", "germplasmDbId", "germplasmName"] + variables
    
    # Build data rows (grouped by observation unit)
    units = {}
    for obs in results:
        unit_id = obs.observation_unit.observation_unit_db_id if obs.observation_unit else obs.observation_db_id
        if unit_id not in units:
            units[unit_id] = {
                "observationUnitDbId": unit_id,
                "germplasmDbId": str(obs.germplasm_id) if obs.germplasm_id else None,
                "germplasmName": obs.germplasm.germplasm_name if obs.germplasm else None,
            }
        if obs.observation_variable:
            var_name = obs.observation_variable.observation_variable_name
            units[unit_id][var_name] = obs.value
    
    data_rows = []
    for unit in units.values():
        row = [unit.get(col, "") for col in header_row]
        data_rows.append(row)
    
    return {
        "metadata": {
            "datafiles": [],
            "pagination": {"currentPage": 0, "pageSize": len(data_rows), "totalCount": len(data_rows), "totalPages": 1},
            "status": [{"message": "Request successful", "messageType": "INFO"}]
        },
        "result": {
            "headerRow": header_row,
            "observationVariableDbIds": [None] * 3 + [None] * len(variables),
            "observationVariableNames": [None] * 3 + variables,
            "data": data_rows
        }
    }


class DeleteObservationsRequest(BaseModel):
    observationDbIds: List[str]


@router.post("/delete/observations")
async def delete_observations_bulk(
    request: DeleteObservationsRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """Delete multiple observations at once."""
    deleted_ids = []
    
    for obs_id in request.observationDbIds:
        obs = db.query(Observation).filter(
            Observation.observation_db_id == obs_id
        ).first()
        
        if obs:
            db.delete(obs)
            deleted_ids.append(obs_id)
    
    db.commit()
    
    return {
        "metadata": {
            "datafiles": [],
            "pagination": {"currentPage": 0, "pageSize": len(deleted_ids), "totalCount": len(deleted_ids), "totalPages": 1},
            "status": [{"message": f"Deleted {len(deleted_ids)} observations", "messageType": "INFO"}]
        },
        "result": {
            "deletedObservationDbIds": deleted_ids
        }
    }
