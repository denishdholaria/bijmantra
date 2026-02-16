"""
BrAPI v2.1 Calls Endpoints
Genotype calls for variants

Database-backed implementation using GenotypingService
"""

from fastapi import APIRouter, Query, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List, Dict

from app.core.database import get_db
from app.services.genotyping import genotyping_service

router = APIRouter()


from app.models.genotyping import Call

def brapi_response(result, page: int = 0, page_size: int = 1000, total: int = None):
    """Standard BrAPI response wrapper."""
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

def call_to_brapi(call: Call) -> dict:
    return {
        "callSetDbId": call.call_set.call_set_db_id if call.call_set else None,
        "callSetName": call.call_set.call_set_name if call.call_set else None,
        "variantDbId": call.variant.variant_db_id if call.variant else None,
        "variantName": call.variant.variant_name if call.variant else None,
        "genotype": call.genotype,
        "genotypeValue": call.genotype_value,
        "genotypeLikelihood": call.genotype_likelihood,
        "phaseSet": call.phase_set if hasattr(call, 'phase_set') else call.phaseSet, # Handle naming diff
        "additionalInfo": call.additional_info or {}
    }

@router.get("/calls")
async def get_calls(
    callSetDbId: Optional[str] = None,
    variantDbId: Optional[str] = None,
    variantSetDbId: Optional[str] = None,
    expandHomozygotes: Optional[bool] = None,
    unknownString: Optional[str] = None,
    sepPhased: Optional[str] = None,
    sepUnphased: Optional[str] = None,
    page: int = Query(0, ge=0),
    pageSize: int = Query(1000, ge=1, le=10000),
    db: AsyncSession = Depends(get_db)
):
    """Retrieves a filtered list of genotype calls."""
    calls, total = await genotyping_service.list_calls(
        db=db,
        call_set_db_id=callSetDbId,
        variant_db_id=variantDbId,
        variant_set_db_id=variantSetDbId,
        page=page,
        page_size=pageSize
    )

    data = [call_to_brapi(call) for call in calls]
    return brapi_response(data, page, pageSize, total)


@router.put("/calls")
async def update_calls(
    calls: List[dict],
    db: AsyncSession = Depends(get_db)
):
    """Updates existing genotype calls in bulk."""
    updated = await genotyping_service.update_calls(db, calls)

    return {
        "metadata": {
            "datafiles": [],
            "pagination": {"currentPage": 0, "pageSize": len(updated), "totalCount": len(updated), "totalPages": 1},
            "status": [{"message": "Success", "messageType": "INFO"}]
        },
        "result": {"data": updated}
    }
