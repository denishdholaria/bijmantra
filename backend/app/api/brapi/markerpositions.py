"""
BrAPI v2.1 MarkerPositions Endpoints
Marker positions on genome maps

Database-backed implementation (no in-memory stores)
"""

from fastapi import APIRouter, Query, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from typing import Optional, List

from app.core.database import get_db
from app.models.genotyping import MarkerPosition, GenomeMap

router = APIRouter()


def brapi_response(result, page: int = 0, page_size: int = 1000, total: int = None):
    """Wraps results in the standard BrAPI response format.

    Args:
        result (list | dict): The data to be returned.
        page (int): The current page number.
        page_size (int): The number of items per page.
        total (int | None): The total number of items. If not provided, it will be
               calculated from the length of the result.

    Returns:
        dict: A dictionary in the BrAPI response format.
    """
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


def marker_position_to_brapi(mp: MarkerPosition) -> dict:
    """Converts a MarkerPosition SQLAlchemy model to a BrAPI-compliant dictionary.

    Args:
        mp (MarkerPosition): The MarkerPosition SQLAlchemy model instance.

    Returns:
        dict: A dictionary representing the marker position in BrAPI format.
    """
    return {
        "markerPositionDbId": mp.marker_position_db_id,
        "variantDbId": mp.variant_db_id,
        "variantName": mp.variant_name,
        "mapDbId": mp.genome_map.map_db_id if mp.genome_map else None,
        "mapName": mp.genome_map.map_name if mp.genome_map else None,
        "linkageGroupName": mp.linkage_group_name,
        "position": mp.position,
        "additionalInfo": mp.additional_info or {}
    }


@router.get("/markerpositions")
async def get_marker_positions(
    mapDbId: Optional[str] = None,
    linkageGroupName: Optional[str] = None,
    variantDbId: Optional[str] = None,
    minPosition: Optional[float] = None,
    maxPosition: Optional[float] = None,
    page: int = Query(0, ge=0),
    pageSize: int = Query(1000, ge=1, le=10000),
    db: AsyncSession = Depends(get_db)
):
    """Retrieves a filtered list of marker positions.

    Args:
        mapDbId (str | None): The database ID of the map to filter by.
        linkageGroupName (str | None): The name of the linkage group to filter by.
        variantDbId (str | None): The database ID of the variant to filter by.
        minPosition (float | None): The minimum position to filter by.
        maxPosition (float | None): The maximum position to filter by.
        page (int): The page number to return.
        pageSize (int): The number of items to return per page.
        db (AsyncSession): The database session.

    Returns:
        dict: A BrAPI-formatted response containing a list of marker positions.
    """
    # Build query
    query = select(MarkerPosition).options(selectinload(MarkerPosition.genome_map))

    # Apply filters
    if mapDbId:
        query = query.join(GenomeMap).where(GenomeMap.map_db_id == mapDbId)
    if linkageGroupName:
        query = query.where(MarkerPosition.linkage_group_name == linkageGroupName)
    if variantDbId:
        query = query.where(MarkerPosition.variant_db_id == variantDbId)
    if minPosition is not None:
        query = query.where(MarkerPosition.position >= minPosition)
    if maxPosition is not None:
        query = query.where(MarkerPosition.position <= maxPosition)

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Apply pagination
    query = query.offset(page * pageSize).limit(pageSize)

    # Execute query
    result = await db.execute(query)
    positions = result.scalars().all()

    # Convert to BrAPI format
    data = [marker_position_to_brapi(mp) for mp in positions]

    return brapi_response(data, page, pageSize, total)
