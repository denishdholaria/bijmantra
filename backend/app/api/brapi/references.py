"""
BrAPI v2.1 References Endpoints
References (chromosomes/contigs)

Database-backed implementation (no in-memory stores)
"""

from fastapi import APIRouter, Query, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from typing import Optional, List

from app.core.database import get_db
from app.models.genotyping import Reference, ReferenceSet

router = APIRouter()


def brapi_response(result, page: int = 0, page_size: int = 1000, total: int = None):
    """Wraps a result in the standard BrAPI v2 response format.

    Args:
        result: The result data to be returned. Can be a list or a single object.
        page: The current page number for paginated results.
        page_size: The number of items per page for paginated results.
        total: The total number of items across all pages. If not provided for a list
               result, it will be calculated as the length of the list.

    Returns:
        A dictionary formatted as a standard BrAPI v2 response.
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


def reference_to_brapi(ref: Reference) -> dict:
    """Converts a Reference SQLAlchemy model to a BrAPI v2 dictionary.

    Args:
        ref: The Reference SQLAlchemy model object.

    Returns:
        A dictionary representing the reference in BrAPI v2 format.
    """
    return {
        "referenceDbId": ref.reference_db_id,
        "referenceName": ref.reference_name,
        "referenceSetDbId": ref.reference_set.reference_set_db_id if ref.reference_set else None,
        "length": ref.length,
        "md5checksum": ref.md5checksum,
        "sourceURI": ref.source_uri,
        "sourceAccessions": ref.source_accessions or [],
        "sourceDivergence": ref.source_divergence,
        "species": ref.species,
        "isDerived": ref.is_derived,
        "additionalInfo": ref.additional_info or {}
    }


@router.get("/references")
async def get_references(
    referenceDbId: Optional[str] = None,
    referenceSetDbId: Optional[str] = None,
    accession: Optional[str] = None,
    md5checksum: Optional[str] = None,
    isDerived: Optional[bool] = None,
    minLength: Optional[int] = None,
    maxLength: Optional[int] = None,
    page: int = Query(0, ge=0),
    pageSize: int = Query(1000, ge=1, le=10000),
    db: AsyncSession = Depends(get_db)
):
    """Retrieves a list of references based on specified filter criteria.

    Args:
        referenceDbId: The unique identifier for a reference.
        referenceSetDbId: The unique identifier for a reference set to which the
                          references belong.
        accession: A specific accession to search for.
        md5checksum: The MD5 checksum of the reference sequence.
        isDerived: Whether to filter for derived references.
        minLength: The minimum length of the reference.
        maxLength: The maximum length of the reference.
        page: The page number for pagination.
        pageSize: The number of items per page for pagination.
        db: The database session dependency.

    Returns:
        A BrAPI v2 compliant response containing a list of references.
    """
    # Build query
    query = select(Reference).options(selectinload(Reference.reference_set))
    
    # Apply filters
    if referenceDbId:
        query = query.where(Reference.reference_db_id == referenceDbId)
    if referenceSetDbId:
        query = query.join(ReferenceSet).where(ReferenceSet.reference_set_db_id == referenceSetDbId)
    if md5checksum:
        query = query.where(Reference.md5checksum == md5checksum)
    if isDerived is not None:
        query = query.where(Reference.is_derived == isDerived)
    if minLength is not None:
        query = query.where(Reference.length >= minLength)
    if maxLength is not None:
        query = query.where(Reference.length <= maxLength)
    
    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0
    
    # Apply pagination
    query = query.offset(page * pageSize).limit(pageSize)
    
    # Execute query
    result = await db.execute(query)
    references = result.scalars().all()
    
    # Convert to BrAPI format
    data = [reference_to_brapi(ref) for ref in references]
    
    return brapi_response(data, page, pageSize, total)


@router.get("/references/{referenceDbId}")
async def get_reference(
    referenceDbId: str,
    db: AsyncSession = Depends(get_db)
):
    """Retrieves a single reference by its unique identifier.

    Args:
        referenceDbId: The unique identifier for a reference.
        db: The database session dependency.

    Returns:
        A BrAPI v2 compliant response containing the reference. If the reference
        is not found, the response metadata will contain an error message.
    """
    query = select(Reference).options(
        selectinload(Reference.reference_set)
    ).where(Reference.reference_db_id == referenceDbId)
    
    result = await db.execute(query)
    reference = result.scalar_one_or_none()
    
    if not reference:
        return {
            "metadata": {
                "status": [{"message": f"Reference {referenceDbId} not found", "messageType": "ERROR"}]
            },
            "result": None
        }
    
    return brapi_response(reference_to_brapi(reference))


@router.get("/references/{referenceDbId}/bases")
async def get_reference_bases(
    referenceDbId: str,
    start: Optional[int] = Query(None, ge=0),
    end: Optional[int] = Query(None, ge=0),
    pageToken: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """Retrieves the base sequence for a given reference.

    Note:
        This is a placeholder implementation. In a production environment, this
        endpoint would fetch and return actual sequence data from a sequence
        store.

    Args:
        referenceDbId: The unique identifier for a reference.
        start: The starting position of the sequence to retrieve (0-based).
        end: The ending position of the sequence to retrieve.
        pageToken: A token for paginating through large sequence results.
        db: The database session dependency.

    Returns:
        A BrAPI v2 compliant response containing the reference sequence data.
        If the reference is not found, the response metadata will contain an
        error message.
    """
    query = select(Reference).where(Reference.reference_db_id == referenceDbId)
    result = await db.execute(query)
    reference = result.scalar_one_or_none()
    
    if not reference:
        return {
            "metadata": {
                "status": [{"message": f"Reference {referenceDbId} not found", "messageType": "ERROR"}]
            },
            "result": None
        }
    
    # In production, this would fetch actual sequence data
    # For now, return metadata about the request
    return {
        "metadata": {
            "datafiles": [],
            "pagination": {"currentPage": 0, "pageSize": 1, "totalCount": 1, "totalPages": 1},
            "status": [{"message": "Sequence data not available in demo mode", "messageType": "INFO"}]
        },
        "result": {
            "referenceDbId": referenceDbId,
            "referenceName": reference.reference_name,
            "length": reference.length,
            "start": start or 0,
            "end": end or reference.length,
            "sequence": None,
            "nextPageToken": None
        }
    }
