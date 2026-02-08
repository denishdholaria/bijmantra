"""
BrAPI v2.1 Observation Levels Endpoints
Hierarchical levels for observation units

Production-ready: All data from database, no in-memory mock data.
"""

from fastapi import APIRouter, Query, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional

from app.api.deps import get_db
from app.models.brapi_phenotyping import ObservationLevel
from app.core.rls import set_tenant_context

router = APIRouter()


def brapi_response(result, page: int = 0, page_size: int = 1000):
    """Standard BrAPI response wrapper"""
    if isinstance(result, list):
        total = len(result)
        start = page * page_size
        end = start + page_size
        data = result[start:end]
        return {
            "metadata": {
                "datafiles": [],
                "pagination": {
                    "currentPage": page,
                    "pageSize": page_size,
                    "totalCount": total,
                    "totalPages": (total + page_size - 1) // page_size if total > 0 else 1
                },
                "status": [{"message": "Success", "messageType": "INFO"}]
            },
            "result": {"data": data}
        }
    return {
        "metadata": {
            "datafiles": [],
            "pagination": {"currentPage": 0, "pageSize": 1, "totalCount": 1, "totalPages": 1},
            "status": [{"message": "Success", "messageType": "INFO"}]
        },
        "result": result
    }


def level_to_brapi(level: ObservationLevel) -> dict:
    """Convert ObservationLevel model to BrAPI format"""
    return {
        "levelName": level.level_name,
        "levelCode": level.level_code,
        "levelOrder": level.level_order
    }


@router.get("/observationlevels")
async def get_observation_levels(
    request: Request,
    studyDbId: Optional[str] = None,
    trialDbId: Optional[str] = None,
    programDbId: Optional[str] = None,
    page: int = Query(0, ge=0),
    pageSize: int = Query(1000, ge=1, le=10000),
    db: AsyncSession = Depends(get_db)
):
    """Get list of observation levels"""
    org_id = getattr(request.state, "organization_id", None)
    is_superuser = getattr(request.state, "is_superuser", False)
    await set_tenant_context(db, org_id, is_superuser)
    
    # Query observation levels, ordered by level_order
    query = select(ObservationLevel).order_by(ObservationLevel.level_order)
    
    result = await db.execute(query)
    levels = result.scalars().all()
    
    # Convert to BrAPI format
    brapi_levels = [level_to_brapi(level) for level in levels]
    
    return brapi_response(brapi_levels, page, pageSize)
