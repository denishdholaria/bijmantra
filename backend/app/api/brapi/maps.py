"""
BrAPI v2.1 Maps Endpoints
Genome maps and linkage groups

Database-backed implementation
"""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user
from app.core.database import get_db
from app.models.core import User
from app.models.genotyping import GenomeMap, LinkageGroup
from app.schemas.genotyping import GenomeMap as GenomeMapSchema
from app.schemas.genotyping import GenomeMapCreate, GenomeMapUpdate
from app.schemas.genotyping import LinkageGroup as LinkageGroupSchema
from app.services.maps_service import maps_service


router = APIRouter()


def brapi_response(result: Any, page: int = 0, page_size: int = 1000, total: int = None) -> dict:
    """Wraps a result in the standard BrAPI response format."""
    if isinstance(result, list):
        total = total if total is not None else len(result)
        return {
            "metadata": {
                "datafiles": [],
                "pagination": {
                    "currentPage": page,
                    "pageSize": page_size,
                    "totalCount": total,
                    "totalPages": (total + page_size - 1) // page_size if total > 0 else 0,
                },
                "status": [{"message": "Success", "messageType": "INFO"}],
            },
            "result": {"data": result},
        }
    return {
        "metadata": {
            "datafiles": [],
            "pagination": {"currentPage": 0, "pageSize": 1, "totalCount": 1, "totalPages": 1},
            "status": [{"message": "Success", "messageType": "INFO"}],
        },
        "result": result,
    }


def map_to_brapi(gmap: GenomeMap) -> dict:
    """Converts a GenomeMap SQLAlchemy model to a BrAPI-compliant dictionary."""
    return GenomeMapSchema.model_validate(gmap).model_dump(by_alias=True)


def linkage_group_to_brapi(lg: LinkageGroup, map_db_id: str) -> dict:
    """Converts a LinkageGroup SQLAlchemy model to a BrAPI-compliant dictionary."""
    # Construct schema manually because map_db_id is not on the ORM object
    schema = LinkageGroupSchema(
        linkage_group_name=lg.linkage_group_name,
        max_position=lg.max_position,
        marker_count=lg.marker_count,
        additional_info=lg.additional_info,
        map_db_id=map_db_id,
    )
    return schema.model_dump(by_alias=True)


@router.get("/maps")
async def get_maps(
    mapDbId: str | None = None,
    mapPUI: str | None = None,
    commonCropName: str | None = None,
    scientificName: str | None = None,
    type: str | None = None,
    programDbId: str | None = None,
    trialDbId: str | None = None,
    studyDbId: str | None = None,
    page: int = Query(0, ge=0),
    pageSize: int = Query(1000, ge=1, le=10000),
    db: AsyncSession = Depends(get_db),
):
    """Retrieves a list of genome maps."""
    maps, total = await maps_service.list_maps(
        db,
        map_db_id=mapDbId,
        map_pui=mapPUI,
        common_crop_name=commonCropName,
        scientific_name=scientificName,
        type=type,
        page=page,
        page_size=pageSize,
    )

    data = [map_to_brapi(m) for m in maps]
    return brapi_response(data, page, pageSize, total)


@router.get("/maps/{mapDbId}")
async def get_map(mapDbId: str, db: AsyncSession = Depends(get_db)):
    """Retrieves a single genome map by ID."""
    gmap = await maps_service.get_map(db, mapDbId)

    if not gmap:
        return {
            "metadata": {
                "status": [{"message": f"Map {mapDbId} not found", "messageType": "ERROR"}]
            },
            "result": None,
        }

    return brapi_response(map_to_brapi(gmap))


@router.post("/maps")
async def create_map(
    map_data: GenomeMapCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Create a new genome map."""
    gmap = await maps_service.create_map(db, map_data, current_user.organization_id)
    return brapi_response(map_to_brapi(gmap))


@router.put("/maps/{mapDbId}")
async def update_map(
    mapDbId: str,
    map_data: GenomeMapUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Update an existing genome map."""
    gmap = await maps_service.update_map(db, mapDbId, map_data)

    if not gmap:
        raise HTTPException(status_code=404, detail=f"Map {mapDbId} not found")

    return brapi_response(map_to_brapi(gmap))


@router.delete("/maps/{mapDbId}")
async def delete_map(
    mapDbId: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Delete a genome map."""
    success = await maps_service.delete_map(db, mapDbId)

    if not success:
        raise HTTPException(status_code=404, detail=f"Map {mapDbId} not found")

    return {
        "metadata": {
            "datafiles": [],
            "pagination": {"currentPage": 0, "pageSize": 1, "totalCount": 1, "totalPages": 1},
            "status": [{"message": f"Map {mapDbId} deleted", "messageType": "INFO"}],
        },
        "result": None,
    }


@router.get("/maps/{mapDbId}/linkagegroups")
async def get_map_linkage_groups(
    mapDbId: str,
    page: int = Query(0, ge=0),
    pageSize: int = Query(1000, ge=1, le=10000),
    db: AsyncSession = Depends(get_db),
):
    """Retrieves the linkage groups for a specific genome map."""
    linkage_groups, total = await maps_service.list_linkage_groups(db, mapDbId, page, pageSize)

    data = [linkage_group_to_brapi(lg, mapDbId) for lg in linkage_groups]
    return brapi_response(data, page, pageSize, total)
