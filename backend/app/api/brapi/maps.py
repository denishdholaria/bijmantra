"""
BrAPI v2.1 Maps Endpoints
Genome maps and linkage groups

Database-backed implementation (no in-memory stores)
"""

from fastapi import APIRouter, Query, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from typing import Optional, List

from app.core.database import get_db
from app.models.genotyping import GenomeMap, LinkageGroup

router = APIRouter()


def brapi_response(result, page: int = 0, page_size: int = 1000, total: int = None):
    """Wraps a result in the standard BrAPI response format.

    Args:
        result: The result data to be wrapped. Can be a list or a single object.
        page: The current page number for paginated results.
        page_size: The number of items per page for paginated results.
        total: The total number of items across all pages. If not provided for a list
               result, it will be calculated as the length of the list.

    Returns:
        A dictionary formatted as a standard BrAPI response.
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


def map_to_brapi(gmap: GenomeMap) -> dict:
    """Converts a GenomeMap SQLAlchemy model to a BrAPI-compliant dictionary.

    Args:
        gmap: The GenomeMap SQLAlchemy model instance.

    Returns:
        A dictionary representing the genome map in BrAPI format.
    """
    return {
        "mapDbId": gmap.map_db_id,
        "mapName": gmap.map_name,
        "mapPUI": gmap.map_pui,
        "commonCropName": gmap.common_crop_name,
        "type": gmap.type,
        "unit": gmap.unit,
        "scientificName": gmap.scientific_name,
        "publishedDate": gmap.published_date,
        "comments": gmap.comments,
        "documentationURL": gmap.documentation_url,
        "linkageGroupCount": gmap.linkage_group_count,
        "markerCount": gmap.marker_count,
        "additionalInfo": gmap.additional_info or {}
    }


def linkage_group_to_brapi(lg: LinkageGroup, map_db_id: str) -> dict:
    """Converts a LinkageGroup SQLAlchemy model to a BrAPI-compliant dictionary.

    Args:
        lg: The LinkageGroup SQLAlchemy model instance.
        map_db_id: The database ID of the map this linkage group belongs to.

    Returns:
        A dictionary representing the linkage group in BrAPI format.
    """
    return {
        "linkageGroupName": lg.linkage_group_name,
        "mapDbId": map_db_id,
        "maxPosition": lg.max_position,
        "markerCount": lg.marker_count,
        "additionalInfo": lg.additional_info or {}
    }


@router.get("/maps")
async def get_maps(
    mapDbId: Optional[str] = None,
    mapPUI: Optional[str] = None,
    commonCropName: Optional[str] = None,
    scientificName: Optional[str] = None,
    type: Optional[str] = None,
    programDbId: Optional[str] = None,
    trialDbId: Optional[str] = None,
    studyDbId: Optional[str] = None,
    page: int = Query(0, ge=0),
    pageSize: int = Query(1000, ge=1, le=10000),
    db: AsyncSession = Depends(get_db)
):
    """Retrieves a list of genome maps, optionally filtered by various criteria.

    Args:
        mapDbId: The database ID of the map to retrieve.
        mapPUI: The PUI of the map to retrieve.
        commonCropName: The common crop name to filter by.
        scientificName: The scientific name to filter by.
        type: The type of map to filter by.
        programDbId: The program database ID to filter by (not implemented).
        trialDbId: The trial database ID to filter by (not implemented).
        studyDbId: The study database ID to filter by (not implemented).
        page: The page number to retrieve.
        pageSize: The number of items per page.
        db: The asynchronous database session.

    Returns:
        A BrAPI-formatted response containing a list of genome maps.
    """
    # Build query
    query = select(GenomeMap)
    
    # Apply filters
    if mapDbId:
        query = query.where(GenomeMap.map_db_id == mapDbId)
    if mapPUI:
        query = query.where(GenomeMap.map_pui == mapPUI)
    if commonCropName:
        query = query.where(GenomeMap.common_crop_name.ilike(f"%{commonCropName}%"))
    if scientificName:
        query = query.where(GenomeMap.scientific_name.ilike(f"%{scientificName}%"))
    if type:
        query = query.where(GenomeMap.type == type)
    
    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0
    
    # Apply pagination
    query = query.offset(page * pageSize).limit(pageSize)
    
    # Execute query
    result = await db.execute(query)
    maps = result.scalars().all()
    
    # Convert to BrAPI format
    data = [map_to_brapi(m) for m in maps]
    
    return brapi_response(data, page, pageSize, total)


@router.get("/maps/{mapDbId}")
async def get_map(
    mapDbId: str,
    db: AsyncSession = Depends(get_db)
):
    """Retrieves a single genome map by its database ID.

    Args:
        mapDbId: The database ID of the map to retrieve.
        db: The asynchronous database session.

    Returns:
        A BrAPI-formatted response containing the requested genome map,
        or a BrAPI-formatted error response if the map is not found.
    """
    query = select(GenomeMap).where(GenomeMap.map_db_id == mapDbId)
    
    result = await db.execute(query)
    gmap = result.scalar_one_or_none()
    
    if not gmap:
        return {
            "metadata": {
                "status": [{"message": f"Map {mapDbId} not found", "messageType": "ERROR"}]
            },
            "result": None
        }
    
    return brapi_response(map_to_brapi(gmap))


@router.get("/maps/{mapDbId}/linkagegroups")
async def get_map_linkage_groups(
    mapDbId: str,
    page: int = Query(0, ge=0),
    pageSize: int = Query(1000, ge=1, le=10000),
    db: AsyncSession = Depends(get_db)
):
    """Retrieves the linkage groups for a specific genome map.

    Args:
        mapDbId: The database ID of the map for which to retrieve linkage groups.
        page: The page number to retrieve.
        pageSize: The number of items per page.
        db: The asynchronous database session.

    Returns:
        A BrAPI-formatted response containing a list of linkage groups for the
        specified map, or an empty data list if the map is not found.
    """
    # Get map
    map_query = select(GenomeMap).where(GenomeMap.map_db_id == mapDbId)
    map_result = await db.execute(map_query)
    gmap = map_result.scalar_one_or_none()
    
    if not gmap:
        return {
            "metadata": {
                "status": [{"message": f"Map {mapDbId} not found", "messageType": "ERROR"}]
            },
            "result": {"data": []}
        }
    
    # Get linkage groups
    query = select(LinkageGroup).where(LinkageGroup.map_id == gmap.id)
    
    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0
    
    # Apply pagination
    query = query.offset(page * pageSize).limit(pageSize)
    
    result = await db.execute(query)
    linkage_groups = result.scalars().all()
    
    # Convert to BrAPI format
    data = [linkage_group_to_brapi(lg, mapDbId) for lg in linkage_groups]
    
    return brapi_response(data, page, pageSize, total)
