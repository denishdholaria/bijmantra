"""
Field Book API
Digital field book for data collection

Migrated to database: December 25, 2025 (Session 17)

Endpoints:
- GET /api/v2/field-book/studies - List studies with field books
- GET /api/v2/field-book/studies/{id}/entries - Get field book entries
- GET /api/v2/field-book/studies/{id}/traits - Get traits for study
- POST /api/v2/field-book/observations - Record observation
- POST /api/v2/field-book/observations/bulk - Bulk record observations
- GET /api/v2/field-book/studies/{id}/progress - Get collection progress
- GET /api/v2/field-book/studies/{id}/summary - Get collection summary
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, date, timezone
from uuid import UUID
import uuid as uuid_module
from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel, Field, ConfigDict
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.field_operations import (
    FieldBookStudy, FieldBookTrait, FieldBookEntry, FieldBookObservation
)

router = APIRouter(prefix="/field-book", tags=["Field Book"], dependencies=[Depends(get_current_user)])


# ============================================
# SCHEMAS
# ============================================

class ObservationRequest(BaseModel):
    """Request to record an observation"""
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "study_id": "STD-001",
            "plot_id": "A-01-01",
            "trait_id": "plant_height",
            "value": 95,
            "notes": "Measured at maturity",
        }
    })

    study_id: str = Field(..., description="Study ID")
    plot_id: str = Field(..., description="Plot ID")
    trait_id: str = Field(..., description="Trait ID")
    value: Any = Field(..., description="Observation value")
    timestamp: Optional[str] = Field(None, description="Observation timestamp")
    notes: str = Field("", description="Notes")


class BulkObservationRequest(BaseModel):
    """Request to record multiple observations"""
    study_id: str = Field(..., description="Study ID")
    observations: List[Dict[str, Any]] = Field(..., description="List of observations")


# ============================================
# HELPER FUNCTIONS
# ============================================

def study_to_dict(study: FieldBookStudy) -> dict:
    """Convert FieldBookStudy model to API response dict"""
    return {
        "id": study.study_code,
        "db_id": str(study.id),
        "name": study.name,
        "location": study.location,
        "season": study.season,
        "design": study.design,
        "reps": study.replications,
        "entries": study.total_entries,
        "traits": study.total_traits,
        "is_active": study.is_active,
    }


def trait_to_dict(trait: FieldBookTrait) -> dict:
    """Convert FieldBookTrait model to API response dict"""
    return {
        "id": trait.trait_code,
        "db_id": str(trait.id),
        "name": trait.name,
        "unit": trait.unit,
        "data_type": trait.data_type,
        "min": trait.min_value,
        "max": trait.max_value,
        "step": trait.step,
        "categories": trait.categories,
        "is_required": trait.is_required,
    }


async def get_study_by_code(db: AsyncSession, study_id: str) -> Optional[FieldBookStudy]:
    """Get study by code or UUID"""
    query = select(FieldBookStudy).where(
        (FieldBookStudy.study_code == study_id) |
        (FieldBookStudy.id == study_id if len(study_id) == 36 else False)
    )
    result = await db.execute(query)
    return result.scalar_one_or_none()


# ============================================
# ENDPOINTS
# ============================================

@router.get("/studies")
async def list_studies(db: AsyncSession = Depends(get_db)):
    """List studies with field books"""
    query = select(FieldBookStudy).where(FieldBookStudy.is_active == True)

    result = await db.execute(query.order_by(FieldBookStudy.name))
    studies = result.scalars().all()

    return {
        "success": True,
        "count": len(studies),
        "studies": [study_to_dict(s) for s in studies],
    }


@router.get("/studies/{study_id}/entries")
async def get_study_entries(
    study_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get field book entries for a study"""
    study = await get_study_by_code(db, study_id)
    if not study:
        raise HTTPException(404, f"Study {study_id} not found")

    # Get entries with their observations
    entries_query = select(FieldBookEntry).where(
        FieldBookEntry.study_id == study.id
    ).options(
        selectinload(FieldBookEntry.observations).selectinload(FieldBookObservation.trait)
    )

    entries_result = await db.execute(entries_query.order_by(
        FieldBookEntry.replication, FieldBookEntry.row, FieldBookEntry.column
    ))
    entries = entries_result.scalars().all()

    # Get traits for this study
    traits_query = select(FieldBookTrait).where(
        FieldBookTrait.study_id == study.id
    ).order_by(FieldBookTrait.display_order)
    traits_result = await db.execute(traits_query)
    traits = traits_result.scalars().all()

    # Build response with trait values
    entries_data = []
    for entry in entries:
        # Build traits dict from observations
        traits_dict = {t.trait_code: None for t in traits}
        for obs in entry.observations:
            if obs.trait:
                value = obs.value_numeric if obs.value_numeric is not None else obs.value_text
                traits_dict[obs.trait.trait_code] = value

        entries_data.append({
            "plot_id": entry.plot_id,
            "germplasm": entry.germplasm_name,
            "rep": entry.replication,
            "block": entry.block,
            "row": entry.row,
            "col": entry.column,
            "is_check": entry.is_check,
            "traits": traits_dict,
        })

    return {
        "success": True,
        "study_id": study.study_code,
        "study_name": study.name,
        "count": len(entries_data),
        "entries": entries_data,
    }


@router.get("/studies/{study_id}/traits")
async def get_study_traits(
    study_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get traits for a study"""
    study = await get_study_by_code(db, study_id)
    if not study:
        raise HTTPException(404, f"Study {study_id} not found")

    query = select(FieldBookTrait).where(
        FieldBookTrait.study_id == study.id
    ).order_by(FieldBookTrait.display_order)

    result = await db.execute(query)
    traits = result.scalars().all()

    return {
        "success": True,
        "study_id": study.study_code,
        "traits": [trait_to_dict(t) for t in traits],
    }


@router.post("/observations")
async def record_observation(
    request: ObservationRequest,
    db: AsyncSession = Depends(get_db),
):
    """Record a single observation"""
    # Validate study
    study = await get_study_by_code(db, request.study_id)
    if not study:
        raise HTTPException(404, f"Study {request.study_id} not found")

    # Find entry by plot_id
    entry_query = select(FieldBookEntry).where(
        (FieldBookEntry.study_id == study.id) &
        (FieldBookEntry.plot_id == request.plot_id)
    )
    entry_result = await db.execute(entry_query)
    entry = entry_result.scalar_one_or_none()

    if not entry:
        raise HTTPException(404, f"Entry {request.plot_id} not found in study")

    # Find trait by code
    trait_query = select(FieldBookTrait).where(
        (FieldBookTrait.study_id == study.id) &
        (FieldBookTrait.trait_code == request.trait_id)
    )
    trait_result = await db.execute(trait_query)
    trait = trait_result.scalar_one_or_none()

    if not trait:
        raise HTTPException(404, f"Trait {request.trait_id} not found in study")

    # Check if observation already exists (upsert)
    existing_query = select(FieldBookObservation).where(
        (FieldBookObservation.entry_id == entry.id) &
        (FieldBookObservation.trait_id == trait.id)
    )
    existing_result = await db.execute(existing_query)
    existing = existing_result.scalar_one_or_none()

    timestamp = datetime.fromisoformat(request.timestamp) if request.timestamp else datetime.now(timezone.utc)

    if existing:
        # Update existing observation
        if isinstance(request.value, (int, float)):
            existing.value_numeric = float(request.value)
            existing.value_text = None
        else:
            existing.value_text = str(request.value)
            existing.value_numeric = None
        existing.observation_timestamp = timestamp
        existing.notes = request.notes
    else:
        # Create new observation
        obs = FieldBookObservation(
            id=uuid_module.uuid4(),
            organization_id=study.organization_id,
            study_id=study.id,
            entry_id=entry.id,
            trait_id=trait.id,
            value_numeric=float(request.value) if isinstance(request.value, (int, float)) else None,
            value_text=str(request.value) if not isinstance(request.value, (int, float)) else None,
            observation_timestamp=timestamp,
            notes=request.notes,
        )
        db.add(obs)

    await db.commit()

    return {
        "success": True,
        "message": f"Observation recorded for {request.plot_id}",
        "study_id": request.study_id,
        "plot_id": request.plot_id,
        "trait_id": request.trait_id,
        "value": request.value,
        "timestamp": timestamp.isoformat(),
    }


@router.post("/observations/bulk")
async def record_bulk_observations(
    request: BulkObservationRequest,
    db: AsyncSession = Depends(get_db),
):
    """Record multiple observations at once"""
    study = await get_study_by_code(db, request.study_id)
    if not study:
        raise HTTPException(404, f"Study {request.study_id} not found")

    # Pre-fetch entries and traits for efficiency
    entries_query = select(FieldBookEntry).where(FieldBookEntry.study_id == study.id)
    entries_result = await db.execute(entries_query)
    entries_map = {e.plot_id: e for e in entries_result.scalars().all()}

    traits_query = select(FieldBookTrait).where(FieldBookTrait.study_id == study.id)
    traits_result = await db.execute(traits_query)
    traits_map = {t.trait_code: t for t in traits_result.scalars().all()}

    recorded = 0
    for obs_data in request.observations:
        plot_id = obs_data.get("plot_id")
        trait_id = obs_data.get("trait_id")
        value = obs_data.get("value")

        if not plot_id or not trait_id or value is None:
            continue

        entry = entries_map.get(plot_id)
        trait = traits_map.get(trait_id)

        if not entry or not trait:
            continue

        # Check for existing observation
        existing_query = select(FieldBookObservation).where(
            (FieldBookObservation.entry_id == entry.id) &
            (FieldBookObservation.trait_id == trait.id)
        )
        existing_result = await db.execute(existing_query)
        existing = existing_result.scalar_one_or_none()

        if existing:
            if isinstance(value, (int, float)):
                existing.value_numeric = float(value)
                existing.value_text = None
            else:
                existing.value_text = str(value)
                existing.value_numeric = None
            existing.observation_timestamp = datetime.now(timezone.utc)
        else:
            obs = FieldBookObservation(
                id=uuid_module.uuid4(),
                organization_id=study.organization_id,
                study_id=study.id,
                entry_id=entry.id,
                trait_id=trait.id,
                value_numeric=float(value) if isinstance(value, (int, float)) else None,
                value_text=str(value) if not isinstance(value, (int, float)) else None,
                observation_timestamp=datetime.now(timezone.utc),
            )
            db.add(obs)

        recorded += 1

    await db.commit()

    return {
        "success": True,
        "message": f"Recorded {recorded} observations",
        "study_id": request.study_id,
        "observations_recorded": recorded,
    }


@router.get("/studies/{study_id}/progress")
async def get_collection_progress(
    study_id: str,
    trait_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """Get data collection progress for a study"""
    study = await get_study_by_code(db, study_id)
    if not study:
        raise HTTPException(404, f"Study {study_id} not found")

    # Get traits
    traits_query = select(FieldBookTrait).where(FieldBookTrait.study_id == study.id)
    traits_result = await db.execute(traits_query)
    traits = traits_result.scalars().all()

    # Get total entries
    entries_count = await db.execute(
        select(func.count(FieldBookEntry.id)).where(FieldBookEntry.study_id == study.id)
    )
    total_entries = entries_count.scalar() or 0

    # Calculate progress per trait
    progress = {}
    for trait in traits:
        obs_count = await db.execute(
            select(func.count(FieldBookObservation.id)).where(
                (FieldBookObservation.study_id == study.id) &
                (FieldBookObservation.trait_id == trait.id)
            )
        )
        collected = obs_count.scalar() or 0

        progress[trait.trait_code] = {
            "trait_name": trait.name,
            "collected": collected,
            "total": total_entries,
            "percentage": round((collected / total_entries) * 100, 1) if total_entries > 0 else 0,
        }

    # Overall progress
    total_obs = total_entries * len(traits)
    collected_obs = sum(p["collected"] for p in progress.values())

    return {
        "success": True,
        "study_id": study.study_code,
        "overall": {
            "collected": collected_obs,
            "total": total_obs,
            "percentage": round((collected_obs / total_obs) * 100, 1) if total_obs > 0 else 0,
        },
        "by_trait": progress if not trait_id else {trait_id: progress.get(trait_id)},
    }


@router.get("/studies/{study_id}/summary")
async def get_collection_summary(
    study_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get collection summary statistics"""
    study = await get_study_by_code(db, study_id)
    if not study:
        raise HTTPException(404, f"Study {study_id} not found")

    # Get traits
    traits_query = select(FieldBookTrait).where(FieldBookTrait.study_id == study.id)
    traits_result = await db.execute(traits_query)
    traits = traits_result.scalars().all()

    # Get total entries
    entries_count = await db.execute(
        select(func.count(FieldBookEntry.id)).where(FieldBookEntry.study_id == study.id)
    )
    total_entries = entries_count.scalar() or 0

    # Calculate summary stats per trait
    summaries = {}
    for trait in traits:
        # Get numeric observations for this trait
        obs_query = select(FieldBookObservation.value_numeric).where(
            (FieldBookObservation.study_id == study.id) &
            (FieldBookObservation.trait_id == trait.id) &
            (FieldBookObservation.value_numeric != None)
        )
        obs_result = await db.execute(obs_query)
        values = [row[0] for row in obs_result.all() if row[0] is not None]

        if values:
            summaries[trait.trait_code] = {
                "trait_name": trait.name,
                "unit": trait.unit,
                "count": len(values),
                "mean": round(sum(values) / len(values), 2),
                "min": min(values),
                "max": max(values),
                "range": max(values) - min(values),
            }
        else:
            summaries[trait.trait_code] = {
                "trait_name": trait.name,
                "unit": trait.unit,
                "count": 0,
                "mean": None,
                "min": None,
                "max": None,
                "range": None,
            }

    return {
        "success": True,
        "study_id": study.study_code,
        "study_name": study.name,
        "total_entries": total_entries,
        "total_traits": len(traits),
        "summaries": summaries,
    }


@router.delete("/observations/{study_id}/{plot_id}/{trait_id}")
async def delete_observation(
    study_id: str,
    plot_id: str,
    trait_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Delete an observation"""
    study = await get_study_by_code(db, study_id)
    if not study:
        raise HTTPException(404, f"Study {study_id} not found")

    # Find entry
    entry_query = select(FieldBookEntry).where(
        (FieldBookEntry.study_id == study.id) &
        (FieldBookEntry.plot_id == plot_id)
    )
    entry_result = await db.execute(entry_query)
    entry = entry_result.scalar_one_or_none()

    if not entry:
        raise HTTPException(404, f"Entry {plot_id} not found")

    # Find trait
    trait_query = select(FieldBookTrait).where(
        (FieldBookTrait.study_id == study.id) &
        (FieldBookTrait.trait_code == trait_id)
    )
    trait_result = await db.execute(trait_query)
    trait = trait_result.scalar_one_or_none()

    if not trait:
        raise HTTPException(404, f"Trait {trait_id} not found")

    # Find and delete observation
    obs_query = select(FieldBookObservation).where(
        (FieldBookObservation.entry_id == entry.id) &
        (FieldBookObservation.trait_id == trait.id)
    )
    obs_result = await db.execute(obs_query)
    obs = obs_result.scalar_one_or_none()

    if not obs:
        raise HTTPException(404, "Observation not found")

    await db.delete(obs)
    await db.commit()

    return {
        "success": True,
        "message": f"Observation deleted for {plot_id}/{trait_id}",
    }
