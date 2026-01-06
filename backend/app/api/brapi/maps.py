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


def map_to_brapi(gmap: GenomeMap) -> dict:
    """Convert GenomeMap model to BrAPI format"""
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
    """Convert LinkageGroup model to BrAPI format"""
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
    """Get list of genome maps"""
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
    """Get a single map by ID"""
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
    """Get linkage groups for a map"""
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
