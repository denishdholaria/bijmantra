"""
BrAPI v2.1 Markers Endpoints
Genetic marker catalog backed by existing variant records.
"""


from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.middleware.tenant_context import get_tenant_db
from app.models.genotyping import Variant
from app.modules.genomics.services.genotyping_service import genotyping_service


router = APIRouter()


# DEPRECATED (ADR-005): Use schemas.brapi.BrAPIResponse[T] instead of this local helper.
def brapi_response(result, page: int = 0, page_size: int = 1000, total: int | None = None):
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


def marker_to_brapi(variant: Variant) -> dict:
    """Convert a Variant record into the marker shape the frontend consumes."""
    marker_name = variant.variant_name or variant.variant_db_id
    return {
        "markerDbId": variant.variant_db_id,
        "markerName": marker_name,
        "defaultDisplayName": marker_name,
        "markerType": variant.variant_type,
        "refAlt": [value for value in [variant.reference_bases, *(variant.alternate_bases or [])] if value],
        "analysisMethods": [],
        "synonyms": [],
        "additionalInfo": variant.additional_info or {},
    }


@router.get("/markers")
async def get_markers(
    markerDbId: str | None = None,
    name: str | None = None,
    page: int = Query(0, ge=0),
    pageSize: int = Query(1000, ge=1, le=10000),
    db: AsyncSession = Depends(get_tenant_db),
):
    """Get a filtered list of markers from variant records."""
    variants, total = await genotyping_service.list_variants(
        db,
        variant_db_id=markerDbId,
        page=page,
        page_size=pageSize,
    )

    if name:
        filtered = [variant for variant in variants if (variant.variant_name or "").lower().find(name.lower()) >= 0]
        return brapi_response([marker_to_brapi(variant) for variant in filtered], page, pageSize, len(filtered))

    return brapi_response([marker_to_brapi(variant) for variant in variants], page, pageSize, total)


@router.get("/markers/{markerDbId}")
async def get_marker(
    markerDbId: str,
    db: AsyncSession = Depends(get_tenant_db),
):
    """Get a single marker by ID."""
    variant = await genotyping_service.get_variant(db, markerDbId)

    if not variant:
        return {
            "metadata": {
                "status": [{"message": f"Marker {markerDbId} not found", "messageType": "ERROR"}],
            },
            "result": None,
        }

    return brapi_response(marker_to_brapi(variant))