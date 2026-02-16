"""
BrAPI v2.1 ReferenceSets Endpoints
Reference sets (genome assemblies)

Database-backed implementation (no in-memory stores)
"""

from fastapi import APIRouter, Query, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from typing import Optional, List

from app.core.database import get_db
from app.models.genotyping import ReferenceSet, Reference

router = APIRouter()


def brapi_response(result, page: int = 0, page_size: int = 1000, total: int = None):
    """Wraps a result in the standard BrAPI response format.

    Args:
        result (any): The result data to be returned.
        page (int): The current page number.
        page_size (int): The number of items per page.
        total (Optional[int]): The total number of items.

    Returns:
        dict: A dictionary representing the BrAPI response.
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


def referenceset_to_brapi(rs: ReferenceSet) -> dict:
    """Converts a ReferenceSet SQLAlchemy model to a BrAPI dictionary.

    Args:
        rs (ReferenceSet): The ReferenceSet model instance.

    Returns:
        dict: A dictionary representing the ReferenceSet in BrAPI format.
    """
    return {
        "referenceSetDbId": rs.reference_set_db_id,
        "referenceSetName": rs.reference_set_name,
        "description": rs.description,
        "assemblyPUI": rs.assembly_pui,
        "sourceURI": rs.source_uri,
        "sourceAccessions": rs.source_accessions or [],
        "sourceGermplasm": rs.source_germplasm or [],
        "species": rs.species,
        "isDerived": rs.is_derived,
        "md5checksum": rs.md5checksum,
        "additionalInfo": rs.additional_info or {}
    }


@router.get("/referencesets")
async def get_referencesets(
    referenceSetDbId: Optional[str] = None,
    accession: Optional[str] = None,
    assemblyPUI: Optional[str] = None,
    md5checksum: Optional[str] = None,
    page: int = Query(0, ge=0),
    pageSize: int = Query(1000, ge=1, le=10000),
    db: AsyncSession = Depends(get_db)
):
    """Retrieve a list of reference sets.

    Args:
        referenceSetDbId (Optional[str]): The database ID of the reference set.
        accession (Optional[str]): An accession number to search for.
        assemblyPUI (Optional[str]): An assembly PUI to search for.
        md5checksum (Optional[str]): An md5checksum to search for.
        page (int): The page number to return.
        pageSize (int): The number of items to return per page.
        db (AsyncSession): An SQLAlchemy asynchronous session.

    Returns:
        dict: A BrAPI response containing a list of reference sets.
    """
    # Build query
    query = select(ReferenceSet)

    # Apply filters
    if referenceSetDbId:
        query = query.where(ReferenceSet.reference_set_db_id == referenceSetDbId)
    if assemblyPUI:
        query = query.where(ReferenceSet.assembly_pui == assemblyPUI)
    if md5checksum:
        query = query.where(ReferenceSet.md5checksum == md5checksum)

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Apply pagination
    query = query.offset(page * pageSize).limit(pageSize)

    # Execute query
    result = await db.execute(query)
    referencesets = result.scalars().all()

    # Convert to BrAPI format
    data = [referenceset_to_brapi(rs) for rs in referencesets]

    return brapi_response(data, page, pageSize, total)


@router.get("/referencesets/{referenceSetDbId}")
async def get_referenceset(
    referenceSetDbId: str,
    db: AsyncSession = Depends(get_db)
):
    """Get a single reference set by ID.

    Args:
        referenceSetDbId (str): The database ID of the reference set.
        db (AsyncSession): An SQLAlchemy asynchronous session.

    Returns:
        dict: A BrAPI response containing the requested reference set, or an
        error message if not found.
    """
    query = select(ReferenceSet).where(ReferenceSet.reference_set_db_id == referenceSetDbId)
    result = await db.execute(query)
    referenceset = result.scalar_one_or_none()

    if not referenceset:
        return {
            "metadata": {
                "status": [{"message": f"ReferenceSet {referenceSetDbId} not found", "messageType": "ERROR"}]
            },
            "result": None
        }

    return brapi_response(referenceset_to_brapi(referenceset))
