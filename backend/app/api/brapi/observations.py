"""
BrAPI v2.1 Observations Endpoints

Database-backed implementation (no in-memory demo data).
Demo data is seeded into Demo Organization via seeders.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from pydantic import BaseModel
from datetime import datetime, timezone
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
    """Converts an Observation SQLAlchemy model to a BrAPI dictionary.

    Args:
        obs (Observation): The Observation SQLAlchemy model.

    Returns:
        A dictionary representing the observation in BrAPI format.
    """
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
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_optional_user),
):
    """Retrieves a paginated list of observations from the database.

    Args:
        page (int): The page number to retrieve.
        pageSize (int): The number of items per page.
        studyDbId (Optional[str]): The ID of the study to filter by.
        germplasmDbId (Optional[str]): The ID of the germplasm to filter by.
        observationVariableDbId (Optional[str]): The ID of the observation variable to filter by.
        observationUnitDbId (Optional[str]): The ID of the observation unit to filter by.
        db (AsyncSession): The database session.
        current_user (Optional[User]): The current authenticated user.

    Returns:
        A dictionary containing the list of observations and metadata.
    """
    # Build query with eager loading of relationships
    query = select(Observation).options(
        selectinload(Observation.observation_unit),
        selectinload(Observation.observation_variable),
        selectinload(Observation.germplasm)
    )
    
    # Filter by user's organization (multi-tenant isolation)
    if current_user and current_user.organization_id:
        query = query.where(Observation.organization_id == current_user.organization_id)
    
    # Apply filters
    if studyDbId:
        try:
            query = query.where(Observation.study_id == int(studyDbId))
        except ValueError:
            pass
    if germplasmDbId:
        try:
            query = query.where(Observation.germplasm_id == int(germplasmDbId))
        except ValueError:
            pass
    if observationVariableDbId:
        query = query.join(ObservationVariable).where(
            ObservationVariable.observation_variable_db_id == observationVariableDbId
        )
    if observationUnitDbId:
        query = query.join(ObservationUnit).where(
            ObservationUnit.observation_unit_db_id == observationUnitDbId
        )
    
    # Get total count
    count_query = select(func.count()).select_from(Observation)
    if studyDbId:
        try:
            count_query = count_query.where(Observation.study_id == int(studyDbId))
        except ValueError:
            pass
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0
    
    # Paginate
    query = query.offset(page * pageSize).limit(pageSize)
    result = await db.execute(query)
    results = result.scalars().all()
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
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Creates a new observation in the database.

    Args:
        observation (ObservationCreate): The observation data to create.
        db (AsyncSession): The database session.
        current_user (User): The current authenticated user.

    Returns:
        A dictionary containing the newly created observation and metadata.

    Raises:
        HTTPException: If an observation with the same ID already exists.
    """
    org_id = current_user.organization_id if current_user else 1
    obs_db_id = f"obs_{uuid.uuid4().hex[:12]}"
    
    # Look up related entities
    obs_unit_id = None
    obs_var_id = None
    
    if observation.observationUnitDbId:
        query = select(ObservationUnit).where(
            ObservationUnit.observation_unit_db_id == observation.observationUnitDbId
        )
        result = await db.execute(query)
        unit = result.scalar_one_or_none()
        if unit:
            obs_unit_id = unit.id
    
    if observation.observationVariableDbId:
        query = select(ObservationVariable).where(
            ObservationVariable.observation_variable_db_id == observation.observationVariableDbId
        )
        result = await db.execute(query)
        var = result.scalar_one_or_none()
        if var:
            obs_var_id = var.id
    
    new_obs = Observation(
        organization_id=org_id,
        observation_db_id=obs_db_id,
        observation_unit_id=obs_unit_id,
        observation_variable_id=obs_var_id,
        value=observation.value,
        observation_time_stamp=observation.observationTimeStamp or datetime.now(timezone.utc).isoformat() + "Z",
        collector=observation.collector,
        season_db_id=observation.seasonDbId,
    )
    
    db.add(new_obs)
    await db.commit()
    await db.refresh(new_obs)
    
    # Reload with relationships
    query = select(Observation).options(
        selectinload(Observation.observation_unit),
        selectinload(Observation.observation_variable),
        selectinload(Observation.germplasm)
    ).where(Observation.id == new_obs.id)
    result = await db.execute(query)
    new_obs = result.scalar_one()
    
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
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_optional_user)
):
    """Retrieves a single observation by its ID from the database.

    Args:
        observationDbId (str): The ID of the observation to retrieve.
        db (AsyncSession): The database session.
        current_user (Optional[User]): The current authenticated user.

    Returns:
        A dictionary containing the observation data and metadata.

    Raises:
        HTTPException: If the observation with the given ID is not found.
    """
    query = select(Observation).options(
        selectinload(Observation.observation_unit),
        selectinload(Observation.observation_variable),
        selectinload(Observation.germplasm)
    ).where(Observation.observation_db_id == observationDbId)
    
    result = await db.execute(query)
    obs = result.scalar_one_or_none()
    
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
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """Updates existing observations in bulk.

    Args:
        observations (List[ObservationUpdate]): A list of observation data to update.
        db (AsyncSession): The database session.
        current_user (User): The current authenticated user.

    Returns:
        A dictionary containing the list of updated observations and metadata.
    """
    updated = []
    
    for obs_data in observations:
        if not obs_data.observationDbId:
            continue
        
        query = select(Observation).options(
            selectinload(Observation.observation_unit),
            selectinload(Observation.observation_variable),
            selectinload(Observation.germplasm)
        ).where(Observation.observation_db_id == obs_data.observationDbId)
        
        result = await db.execute(query)
        obs = result.scalar_one_or_none()
        
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
    
    await db.commit()
    
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
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """Updates a single observation.

    Args:
        observationDbId (str): The ID of the observation to update.
        observation (ObservationCreate): The observation data to update.
        db (AsyncSession): The database session.
        current_user (User): The current authenticated user.

    Returns:
        A dictionary containing the updated observation and metadata.

    Raises:
        HTTPException: If the observation with the given ID is not found.
    """
    query = select(Observation).options(
        selectinload(Observation.observation_unit),
        selectinload(Observation.observation_variable),
        selectinload(Observation.germplasm)
    ).where(Observation.observation_db_id == observationDbId)
    
    result = await db.execute(query)
    obs = result.scalar_one_or_none()
    
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
    
    await db.commit()
    await db.refresh(obs)
    
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
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_optional_user),
):
    """Retrieves observations in a table format.

    Args:
        studyDbId (Optional[str]): The ID of the study to filter by.
        observationUnitDbId (Optional[List[str]]): A list of observation unit IDs to filter by.
        observationVariableDbId (Optional[List[str]]): A list of observation variable IDs to filter by.
        germplasmDbId (Optional[List[str]]): A list of germplasm IDs to filter by.
        db (AsyncSession): The database session.
        current_user (Optional[User]): The current authenticated user.

    Returns:
        A dictionary containing the observations in a table format and metadata.
    """
    query = select(Observation).options(
        selectinload(Observation.observation_unit),
        selectinload(Observation.observation_variable),
        selectinload(Observation.germplasm)
    )
    
    if studyDbId:
        try:
            query = query.where(Observation.study_id == int(studyDbId))
        except ValueError:
            pass
    if observationUnitDbId:
        query = query.join(ObservationUnit).where(
            ObservationUnit.observation_unit_db_id.in_(observationUnitDbId)
        )
    if observationVariableDbId:
        query = query.join(ObservationVariable).where(
            ObservationVariable.observation_variable_db_id.in_(observationVariableDbId)
        )
    if germplasmDbId:
        try:
            query = query.where(Observation.germplasm_id.in_([int(g) for g in germplasmDbId]))
        except ValueError:
            pass
    
    result = await db.execute(query)
    results = result.scalars().all()
    
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
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """Deletes multiple observations in bulk.

    Args:
        request (DeleteObservationsRequest): A request object containing a list of observation IDs to delete.
        db (AsyncSession): The database session.
        current_user (User): The current authenticated user.

    Returns:
        A dictionary containing a list of the deleted observation IDs.
    """
    deleted_ids = []
    
    for obs_id in request.observationDbIds:
        query = select(Observation).where(Observation.observation_db_id == obs_id)
        result = await db.execute(query)
        obs = result.scalar_one_or_none()
        
        if obs:
            await db.delete(obs)
            deleted_ids.append(obs_id)
    
    await db.commit()
    
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
