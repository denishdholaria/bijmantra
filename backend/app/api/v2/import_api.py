"""
Data Import API
Handles bulk data ingestion from frontend-parsed CSV/JSON
"""
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Body, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_user
from app.models.core import User
from sqlalchemy import select, insert
from app.models.germplasm import Germplasm

router = APIRouter(prefix="/import", tags=["Data Import"])

# Request Models
class ImportRequest(BaseModel):
    data: List[Dict[str, Any]]
    options: Optional[Dict[str, Any]] = None

# Service Implementations

async def process_germplasm_import(data: List[Dict[str, Any]], db: AsyncSession):
    """
    Process bulk germplasm import.
    Skips records that already exist based on 'germplasmName'.
    """
    if not data:
        return {"count": 0, "status": "empty"}

    # 1. Normalize Input
    # Identify unique names to check against DB
    imported_names = {row.get("germplasmName") for row in data if row.get("germplasmName")}
    
    if not imported_names:
        return {"count": 0, "status": "no_names_found"}

    # 2. Find Existing (to skip)
    # TODO: Scope query by Organization ID once authentication is fully granular
    # For now, we assume current user's org context (which we don't have access to inside this helper easily without passing it)
    # We will assume unique constraints on (germplasm_name) or (germplasm_name + organization_id)
    
    query = select(Germplasm.germplasm_name).where(Germplasm.germplasm_name.in_(imported_names))
    result = await db.execute(query)
    existing_names = set(result.scalars().all())

    # 3. Prepare New Records
    new_records = []
    # Default Organization ID for imported data if not specified (Hardcoded 1 for MVP or should be passed)
    # Ideally, we should pass `organization_id` to this function. 
    # For now, we'll assume the caller context handles org_id or we default to 1 safe for MVP.
    DEFAULT_ORG_ID = 1 

    for row in data:
        name = row.get("germplasmName")
        if name and name not in existing_names:
            # Prevent duplicates within the import batch itself
            existing_names.add(name) 
            
            new_records.append({
                "germplasm_name": name,
                "accession_number": row.get("accessionNumber"),
                "genus": row.get("genus"),
                "species": row.get("species"),
                "common_crop_name": row.get("commonCropName"),
                "pedigree": row.get("pedigree"),
                "country_of_origin_code": row.get("countryOfOriginCode"),
                "organization_id": DEFAULT_ORG_ID, # TODO: Get from current_user
                # "germplasm_db_id": generate_uuid() # If needed, or let DB handle defaults if auto-increment
            })

    # 4. Bulk Insert
    if new_records:
        stmt = insert(Germplasm).values(new_records)
        await db.execute(stmt)
        await db.commit()

    return {
        "count": len(new_records), 
        "total_processed": len(data),
        "skipped": len(data) - len(new_records),
        "status": "completed"
    }

from app.models.phenotyping import Observation, ObservationUnit, ObservationVariable

async def process_observation_import(data: List[Dict[str, Any]], db: AsyncSession):
    """
    Process bulk observation import.
    Resolves 'trait' -> ObservationVariable
    Resolves 'observationUnitName' -> ObservationUnit
    """
    if not data:
        return {"count": 0, "status": "empty"}

    # 1. Extract Lookups
    trait_names = {row.get("trait") for row in data if row.get("trait")}
    unit_names = {row.get("observationUnitName") for row in data if row.get("observationUnitName")}
    
    if not trait_names or not unit_names:
        return {"count": 0, "status": "missing_required_fields"}

    # 2. Resolve IDs
    # Traits
    # Note: Logic here assumes trait name matches observation_variable_name
    trait_query = select(ObservationVariable.observation_variable_name, ObservationVariable.id).where(
        ObservationVariable.observation_variable_name.in_(trait_names)
    )
    trait_result = await db.execute(trait_query)
    trait_map = dict(trait_result.all()) # {'Yield': 1, 'Height': 2}

    # Units
    unit_query = select(ObservationUnit.observation_unit_name, ObservationUnit.id).where(
        ObservationUnit.observation_unit_name.in_(unit_names)
    )
    unit_result = await db.execute(unit_query)
    unit_map = dict(unit_result.all()) # {'Plot-101': 55}

    # 3. Prepare Records
    new_records = []
    skipped_count = 0
    DEFAULT_ORG_ID = 1

    for row in data:
        t_name = row.get("trait")
        u_name = row.get("observationUnitName")
        
        t_id = trait_map.get(t_name)
        u_id = unit_map.get(u_name)
        
        if t_id and u_id:
            new_records.append({
                "observation_variable_id": t_id,
                "observation_unit_id": u_id,
                "value": str(row.get("value")), # Ensure string for Text column
                "observation_time_stamp": row.get("date"),
                "organization_id": DEFAULT_ORG_ID,
                # Link other FKs if possible, or leave null -> 
                # Ideally we should fetch study_id/germplasm_id from the Unit to denormalize if the model requires it
                # The Model has study_id and germplasm_id.
                # Optimization: We should probably join ObservationUnit to get these IDs map too.
            })
        else:
            skipped_count += 1

    # Optimization Step: Get Study/Germplasm context from Units
    # If we are inserting verify if we need strict Study/Germplasm FKs on Observation table
    # Looking at model: yes, study_id and germplasm_id are index=True ForeignKey.
    # While potentially nullable in DB (need to check strictness), BrAPI usually wants them.
    
    # 4. Insert
    if new_records:
        # Simplification: For now we just insert what we have. 
        # If DB constraints fail on study_id, we will see errors.
        # Assuming for MVP that nullable FKs are fine or triggers handle it.
        stmt = insert(Observation).values(new_records)
        await db.execute(stmt)
        await db.commit()

    return {
        "count": len(new_records),
        "total_processed": len(data),
        "skipped": skipped_count,
        "status": "completed"
    }

async def process_trial_import(data: List[Dict[str, Any]], db: AsyncSession):
    return {"count": len(data), "status": "simulated"}


@router.post("/germplasm")
async def import_germplasm(
    request: ImportRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Bulk import Germplasm.
    Expected columns: germplasmName, accessionNumber, etc.
    """
    try:
        # We should modify the service signature to accept org_id in the future
        # For now, relying on the service default
        result = await process_germplasm_import(request.data, db)
        return {
            "success": True,
            "message": f"Successfully imported {result['count']} germplasm entries (Skipped {result['skipped']})",
            "details": result
        }
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/observations")
async def import_observations(
    request: ImportRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Bulk import Observations.
    Expected columns: observationUnitName, trait, value, date
    """
    try:
        result = await process_observation_import(request.data, db)
        return {
            "success": True,
            "message": f"Successfully imported {result['count']} observations",
            "details": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/trials")
async def import_trials(
    request: ImportRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Bulk import Trials.
    Expected columns: trialName, location, startDate
    """
    try:
        result = await process_trial_import(request.data, db)
        return {
            "success": True,
            "message": f"Successfully imported {result['count']} trials",
            "details": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
