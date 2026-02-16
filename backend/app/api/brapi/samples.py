"""
BrAPI v2.1 Samples Endpoints

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
from app.models.phenotyping import Sample, ObservationUnit

router = APIRouter()


class SampleBase(BaseModel):
    sampleName: str
    sampleType: Optional[str] = None
    sampleDescription: Optional[str] = None
    sampleBarcode: Optional[str] = None
    samplePUI: Optional[str] = None
    sampleGroupDbId: Optional[str] = None
    sampleTimestamp: Optional[str] = None
    takenBy: Optional[str] = None
    observationUnitDbId: Optional[str] = None
    germplasmDbId: Optional[str] = None
    studyDbId: Optional[str] = None
    plateDbId: Optional[str] = None
    plateName: Optional[str] = None
    plateIndex: Optional[int] = None
    well: Optional[str] = None
    row: Optional[str] = None
    column: Optional[int] = None
    tissueType: Optional[str] = None
    concentration: Optional[float] = None
    volume: Optional[float] = None


class SampleCreate(SampleBase):
    pass


class SampleUpdate(SampleBase):
    sampleDbId: Optional[str] = None
    sampleName: Optional[str] = None


def _model_to_brapi(sample: Sample) -> dict:
    """Converts a Sample SQLAlchemy model to a BrAPI-compliant dictionary.

    Args:
        sample: The Sample SQLAlchemy model instance.

    Returns:
        A dictionary formatted according to BrAPI v2.1 Sample specification.
    """
    return {
        "sampleDbId": sample.sample_db_id,
        "sampleName": sample.sample_name,
        "sampleType": sample.sample_type,
        "sampleDescription": sample.sample_description,
        "sampleBarcode": sample.sample_barcode,
        "samplePUI": sample.sample_pui,
        "sampleGroupDbId": sample.sample_group_db_id,
        "sampleTimestamp": sample.sample_timestamp,
        "takenBy": sample.taken_by,
        "observationUnitDbId": sample.observation_unit.observation_unit_db_id if sample.observation_unit else None,
        "germplasmDbId": str(sample.germplasm_id) if sample.germplasm_id else None,
        "studyDbId": str(sample.study_id) if sample.study_id else None,
        "plateDbId": sample.plate_db_id,
        "plateName": sample.plate_name,
        "plateIndex": sample.plate_index,
        "well": sample.well,
        "row": sample.row,
        "column": sample.column,
        "tissueType": sample.tissue_type,
        "concentration": sample.concentration,
        "volume": sample.volume,
        "additionalInfo": sample.additional_info,
        "externalReferences": sample.external_references,
    }


@router.get("/samples")
async def list_samples(
    page: int = Query(0, ge=0),
    pageSize: int = Query(20, ge=1, le=1000),
    sampleDbId: Optional[str] = None,
    sampleName: Optional[str] = None,
    sampleType: Optional[str] = None,
    plateDbId: Optional[str] = None,
    germplasmDbId: Optional[str] = None,
    studyDbId: Optional[str] = None,
    observationUnitDbId: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_optional_user),
):
    """Retrieves a filtered list of samples.

    Args:
        page: The page number to retrieve.
        pageSize: The number of items per page.
        sampleDbId: The database ID of the sample.
        sampleName: The name of the sample.
        sampleType: The type of the sample.
        plateDbId: The database ID of the plate.
        germplasmDbId: The database ID of the germplasm.
        studyDbId: The database ID of the study.
        observationUnitDbId: The database ID of the observation unit.
        db: The database session.
        current_user: The current authenticated user.

    Returns:
        A paginated list of samples formatted according to BrAPI v2.1 specification.
    """
    # Build base query with eager loading for observation_unit
    stmt = select(Sample).options(selectinload(Sample.observation_unit))

    # Filter by user's organization (multi-tenant isolation)
    if current_user and current_user.organization_id:
        stmt = stmt.where(Sample.organization_id == current_user.organization_id)

    # Apply filters
    if sampleDbId:
        stmt = stmt.where(Sample.sample_db_id == sampleDbId)
    if sampleName:
        stmt = stmt.where(Sample.sample_name.ilike(f"%{sampleName}%"))
    if sampleType:
        stmt = stmt.where(Sample.sample_type == sampleType)
    if plateDbId:
        stmt = stmt.where(Sample.plate_db_id == plateDbId)
    if germplasmDbId:
        stmt = stmt.where(Sample.germplasm_id == int(germplasmDbId))
    if studyDbId:
        stmt = stmt.where(Sample.study_id == int(studyDbId))
    if observationUnitDbId:
        stmt = stmt.join(ObservationUnit).where(
            ObservationUnit.observation_unit_db_id == observationUnitDbId
        )

    # Get total count
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total_result = await db.execute(count_stmt)
    total = total_result.scalar() or 0

    # Apply pagination
    stmt = stmt.offset(page * pageSize).limit(pageSize)

    # Execute query
    result = await db.execute(stmt)
    samples = result.scalars().all()
    data = [_model_to_brapi(s) for s in samples]

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


@router.post("/samples")
async def create_sample(
    sample: SampleCreate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Creates a new sample in the database.

    Args:
        sample: The sample data to create.
        db: The database session.
        current_user: The current authenticated user.

    Returns:
        The newly created sample, formatted according to BrAPI v2.1 specification.
    """
    org_id = current_user.organization_id if current_user else 1
    sample_db_id = f"sample_{uuid.uuid4().hex[:12]}"

    # Look up observation unit
    obs_unit_id = None
    if sample.observationUnitDbId:
        stmt = select(ObservationUnit).where(
            ObservationUnit.observation_unit_db_id == sample.observationUnitDbId
        )
        result = await db.execute(stmt)
        unit = result.scalar_one_or_none()
        if unit:
            obs_unit_id = unit.id

    new_sample = Sample(
        organization_id=org_id,
        sample_db_id=sample_db_id,
        sample_name=sample.sampleName,
        sample_type=sample.sampleType,
        sample_description=sample.sampleDescription,
        sample_barcode=sample.sampleBarcode,
        sample_pui=sample.samplePUI,
        sample_group_db_id=sample.sampleGroupDbId,
        sample_timestamp=sample.sampleTimestamp,
        taken_by=sample.takenBy,
        observation_unit_id=obs_unit_id,
        germplasm_id=int(sample.germplasmDbId) if sample.germplasmDbId else None,
        study_id=int(sample.studyDbId) if sample.studyDbId else None,
        plate_db_id=sample.plateDbId,
        plate_name=sample.plateName,
        plate_index=sample.plateIndex,
        well=sample.well,
        row=sample.row,
        column=sample.column,
        tissue_type=sample.tissueType,
        concentration=sample.concentration,
        volume=sample.volume,
    )

    db.add(new_sample)
    await db.commit()
    await db.refresh(new_sample)

    return {
        "metadata": {
            "datafiles": [],
            "pagination": {"currentPage": 0, "pageSize": 1, "totalCount": 1, "totalPages": 1},
            "status": [{"message": "Sample created successfully", "messageType": "INFO"}]
        },
        "result": _model_to_brapi(new_sample)
    }


@router.get("/samples/{sampleDbId}")
async def get_sample(
    sampleDbId: str,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_optional_user)
):
    """Retrieves a sample by its database ID.

    Args:
        sampleDbId: The database ID of the sample to retrieve.
        db: The database session.
        current_user: The current authenticated user.

    Returns:
        The requested sample, formatted according to BrAPI v2.1 specification.

    Raises:
        HTTPException: If the sample is not found.
    """
    stmt = select(Sample).options(selectinload(Sample.observation_unit)).where(
        Sample.sample_db_id == sampleDbId
    )
    result = await db.execute(stmt)
    sample = result.scalar_one_or_none()

    if not sample:
        raise HTTPException(status_code=404, detail="Sample not found")

    return {
        "metadata": {
            "datafiles": [],
            "pagination": {"currentPage": 0, "pageSize": 1, "totalCount": 1, "totalPages": 1},
            "status": []
        },
        "result": _model_to_brapi(sample)
    }


@router.put("/samples")
async def update_samples_bulk(
    samples: List[SampleUpdate],
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """Updates multiple samples in bulk.

    Args:
        samples: A list of sample data to update.
        db: The database session.
        current_user: The current authenticated user.

    Returns:
        A list of the updated samples, formatted according to BrAPI v2.1 specification.
    """
    updated = []

    for sample_data in samples:
        if not sample_data.sampleDbId:
            continue

        stmt = select(Sample).where(Sample.sample_db_id == sample_data.sampleDbId)
        result = await db.execute(stmt)
        sample = result.scalar_one_or_none()

        if sample:
            if sample_data.sampleName:
                sample.sample_name = sample_data.sampleName
            if sample_data.sampleType:
                sample.sample_type = sample_data.sampleType
            if sample_data.sampleDescription:
                sample.sample_description = sample_data.sampleDescription
            if sample_data.tissueType:
                sample.tissue_type = sample_data.tissueType
            if sample_data.concentration is not None:
                sample.concentration = sample_data.concentration
            if sample_data.volume is not None:
                sample.volume = sample_data.volume
            if sample_data.well:
                sample.well = sample_data.well
            if sample_data.plateDbId:
                sample.plate_db_id = sample_data.plateDbId

            updated.append(sample)

    await db.commit()

    return {
        "metadata": {
            "datafiles": [],
            "pagination": {"currentPage": 0, "pageSize": len(updated), "totalCount": len(updated), "totalPages": 1},
            "status": [{"message": f"Updated {len(updated)} samples", "messageType": "INFO"}]
        },
        "result": {"data": [_model_to_brapi(s) for s in updated]}
    }


@router.put("/samples/{sampleDbId}")
async def update_sample(
    sampleDbId: str,
    sample_data: SampleUpdate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """Updates a single sample by its database ID.

    Args:
        sampleDbId: The database ID of the sample to update.
        sample_data: The sample data to update.
        db: The database session.
        current_user: The current authenticated user.

    Returns:
        The updated sample, formatted according to BrAPI v2.1 specification.

    Raises:
        HTTPException: If the sample is not found.
    """
    stmt = select(Sample).where(Sample.sample_db_id == sampleDbId)
    result = await db.execute(stmt)
    sample = result.scalar_one_or_none()

    if not sample:
        raise HTTPException(status_code=404, detail="Sample not found")

    if sample_data.sampleName:
        sample.sample_name = sample_data.sampleName
    if sample_data.sampleType:
        sample.sample_type = sample_data.sampleType
    if sample_data.sampleDescription:
        sample.sample_description = sample_data.sampleDescription
    if sample_data.tissueType:
        sample.tissue_type = sample_data.tissueType
    if sample_data.concentration is not None:
        sample.concentration = sample_data.concentration
    if sample_data.volume is not None:
        sample.volume = sample_data.volume

    await db.commit()
    await db.refresh(sample)

    return {
        "metadata": {
            "datafiles": [],
            "pagination": {"currentPage": 0, "pageSize": 1, "totalCount": 1, "totalPages": 1},
            "status": [{"message": "Sample updated successfully", "messageType": "INFO"}]
        },
        "result": _model_to_brapi(sample)
    }


@router.delete("/samples/{sampleDbId}")
async def delete_sample(
    sampleDbId: str,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """Deletes a sample by its database ID.

    Args:
        sampleDbId: The database ID of the sample to delete.
        db: The database session.
        current_user: The current authenticated user.

    Returns:
        A dictionary containing the ID of the deleted sample.

    Raises:
        HTTPException: If the sample is not found.
    """
    stmt = select(Sample).where(Sample.sample_db_id == sampleDbId)
    result = await db.execute(stmt)
    sample = result.scalar_one_or_none()

    if not sample:
        raise HTTPException(status_code=404, detail="Sample not found")

    await db.delete(sample)
    await db.commit()

    return {
        "metadata": {
            "datafiles": [],
            "pagination": {"currentPage": 0, "pageSize": 1, "totalCount": 1, "totalPages": 1},
            "status": [{"message": "Sample deleted successfully", "messageType": "INFO"}]
        },
        "result": {"sampleDbId": sampleDbId}
    }
