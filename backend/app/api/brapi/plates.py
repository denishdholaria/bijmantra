"""
BrAPI v2.1 Plates Endpoints
Sample plates for genotyping

Database-backed implementation (no in-memory stores)
"""

from fastapi import APIRouter, Query, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from typing import Optional, List
import uuid

from app.core.database import get_db
from app.models.genotyping import Plate
from app.models.phenotyping import Sample

router = APIRouter()


def brapi_response(result, page: int = 0, page_size: int = 1000, total: int = None):
    """Standard BrAPI response wrapper"""
    if isinstance(result, list):
        total = total if total is not None else len(result)
        return {
            "metadata": {
                "datafiles": [],
                "pagination": {
                    "currentPage": page,
                    "pageSize": page_size,
                    "totalCount": total,
                    "totalPages": (total + page_size - 1) // page_size if total > 0 else 0
                },
                "status": [{"message": "Success", "messageType": "INFO"}]
            },
            "result": {"data": result}
        }
    return {
        "metadata": {
            "datafiles": [],
            "pagination": {"currentPage": 0, "pageSize": 1, "totalCount": 1, "totalPages": 1},
            "status": [{"message": "Success", "messageType": "INFO"}]
        },
        "result": result
    }


def plate_to_brapi(plate: Plate, samples: List[Sample] = None) -> dict:
    """Convert Plate model to BrAPI format"""
    sample_data = []
    if samples:
        for s in samples:
            sample_data.append({
                "sampleDbId": s.sample_db_id,
                "well": s.well,
                "row": s.row,
                "column": s.column
            })
    
    return {
        "plateDbId": plate.plate_db_id,
        "plateName": plate.plate_name,
        "plateBarcode": plate.plate_barcode,
        "plateFormat": plate.plate_format,
        "sampleType": plate.sample_type,
        "studyDbId": plate.study.study_db_id if plate.study else None,
        "trialDbId": plate.trial.trial_db_id if plate.trial else None,
        "programDbId": plate.program.program_db_id if plate.program else None,
        "clientPlateDbId": plate.client_plate_db_id,
        "clientPlateBarcode": plate.client_plate_barcode,
        "statusTimeStamp": plate.status_time_stamp,
        "samples": sample_data,
        "additionalInfo": plate.additional_info or {}
    }


@router.get("/plates")
async def get_plates(
    plateDbId: Optional[str] = None,
    plateName: Optional[str] = None,
    plateBarcode: Optional[str] = None,
    sampleDbId: Optional[str] = None,
    sampleName: Optional[str] = None,
    sampleGroupDbId: Optional[str] = None,
    germplasmDbId: Optional[str] = None,
    observationUnitDbId: Optional[str] = None,
    studyDbId: Optional[str] = None,
    trialDbId: Optional[str] = None,
    programDbId: Optional[str] = None,
    externalReferenceId: Optional[str] = None,
    externalReferenceSource: Optional[str] = None,
    page: int = Query(0, ge=0),
    pageSize: int = Query(1000, ge=1, le=10000),
    db: AsyncSession = Depends(get_db)
):
    """Get list of plates"""
    # Build query
    query = select(Plate).options(
        selectinload(Plate.study),
        selectinload(Plate.trial),
        selectinload(Plate.program)
    )
    
    # Apply filters
    if plateDbId:
        query = query.where(Plate.plate_db_id == plateDbId)
    if plateName:
        query = query.where(Plate.plate_name.ilike(f"%{plateName}%"))
    if plateBarcode:
        query = query.where(Plate.plate_barcode == plateBarcode)
    
    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0
    
    # Apply pagination
    query = query.offset(page * pageSize).limit(pageSize)
    
    # Execute query
    result = await db.execute(query)
    plates = result.scalars().all()
    
    # Get samples for each plate
    data = []
    for plate in plates:
        samples_query = select(Sample).where(Sample.plate_db_id == plate.plate_db_id)
        samples_result = await db.execute(samples_query)
        samples = samples_result.scalars().all()
        data.append(plate_to_brapi(plate, samples))
    
    return brapi_response(data, page, pageSize, total)


@router.get("/plates/{plateDbId}")
async def get_plate(
    plateDbId: str,
    db: AsyncSession = Depends(get_db)
):
    """Get a single plate by ID"""
    query = select(Plate).options(
        selectinload(Plate.study),
        selectinload(Plate.trial),
        selectinload(Plate.program)
    ).where(Plate.plate_db_id == plateDbId)
    
    result = await db.execute(query)
    plate = result.scalar_one_or_none()
    
    if not plate:
        return {
            "metadata": {
                "status": [{"message": f"Plate {plateDbId} not found", "messageType": "ERROR"}]
            },
            "result": None
        }
    
    # Get samples
    samples_query = select(Sample).where(Sample.plate_db_id == plateDbId)
    samples_result = await db.execute(samples_query)
    samples = samples_result.scalars().all()
    
    return brapi_response(plate_to_brapi(plate, samples))


@router.post("/plates")
async def create_plates(
    plates: List[dict],
    db: AsyncSession = Depends(get_db)
):
    """Create new plates"""
    created = []
    
    for plate_data in plates:
        plate_db_id = plate_data.get("plateDbId") or f"plate-{uuid.uuid4().hex[:8]}"
        
        plate = Plate(
            organization_id=1,  # Default org, should come from auth context
            plate_db_id=plate_db_id,
            plate_name=plate_data.get("plateName", ""),
            plate_barcode=plate_data.get("plateBarcode"),
            plate_format=plate_data.get("plateFormat", "PLATE_96"),
            sample_type=plate_data.get("sampleType", "DNA"),
            client_plate_db_id=plate_data.get("clientPlateDbId"),
            client_plate_barcode=plate_data.get("clientPlateBarcode"),
            additional_info=plate_data.get("additionalInfo", {})
        )
        db.add(plate)
        created.append(plate_to_brapi(plate))
    
    await db.commit()
    
    return brapi_response(created)


@router.put("/plates")
async def update_plates(
    plates: List[dict],
    db: AsyncSession = Depends(get_db)
):
    """Update existing plates"""
    updated = []
    
    for plate_data in plates:
        plate_db_id = plate_data.get("plateDbId")
        if not plate_db_id:
            continue
        
        query = select(Plate).where(Plate.plate_db_id == plate_db_id)
        result = await db.execute(query)
        plate = result.scalar_one_or_none()
        
        if plate:
            if "plateName" in plate_data:
                plate.plate_name = plate_data["plateName"]
            if "plateBarcode" in plate_data:
                plate.plate_barcode = plate_data["plateBarcode"]
            if "plateFormat" in plate_data:
                plate.plate_format = plate_data["plateFormat"]
            if "sampleType" in plate_data:
                plate.sample_type = plate_data["sampleType"]
            if "additionalInfo" in plate_data:
                plate.additional_info = plate_data["additionalInfo"]
            
            updated.append(plate_to_brapi(plate))
    
    await db.commit()
    
    return brapi_response(updated)


@router.delete("/plates/{plateDbId}")
async def delete_plate(
    plateDbId: str,
    db: AsyncSession = Depends(get_db)
):
    """Delete a plate by ID"""
    query = select(Plate).where(Plate.plate_db_id == plateDbId)
    result = await db.execute(query)
    plate = result.scalar_one_or_none()
    
    if not plate:
        return {
            "metadata": {
                "status": [{"message": f"Plate {plateDbId} not found", "messageType": "ERROR"}]
            },
            "result": None
        }
    
    await db.delete(plate)
    await db.commit()
    
    return {
        "metadata": {
            "datafiles": [],
            "pagination": {"currentPage": 0, "pageSize": 0, "totalCount": 0, "totalPages": 0},
            "status": [{"message": "Plate deleted successfully", "messageType": "INFO"}]
        },
        "result": None
    }
