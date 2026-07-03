"""
Search API Endpoints
Unified search across all BrAPI entities using Meilisearch

Updated Dec 2025:
- Federated multi-index search (v1.10+)
- Similar documents API (v1.9+)
- Geo search for locations
- Ranking score threshold
- Search statistics
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from app.api.deps import get_current_user
from app.models.core import User


logger = logging.getLogger(__name__)
router = APIRouter(dependencies=[Depends(get_current_user)])


def _filter_value(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


def _eq_filter(attribute: str, value: str) -> str:
    return f'{attribute} = "{_filter_value(value)}"'


class SearchResult(BaseModel):
    """Search result item"""

    id: str
    type: str
    title: str
    subtitle: str | None = None
    description: str | None = None
    path: str
    score: float | None = None


class SearchResponse(BaseModel):
    """Search response"""

    query: str
    results: list[SearchResult]
    total: int
    processingTimeMs: int


class FederatedSearchResponse(BaseModel):
    """Federated search response with merged results"""

    query: str
    results: list[SearchResult]
    total: int
    processingTimeMs: int
    indexes: list[str]


class SimilarDocumentsResponse(BaseModel):
    """Similar documents response"""

    documentId: str
    indexName: str
    results: list[SearchResult]
    total: int


class GeoSearchResponse(BaseModel):
    """Geo search response"""

    query: str
    results: list[SearchResult]
    total: int
    center: dict
    radiusKm: float


class SearchStatsResponse(BaseModel):
    """Search service statistics"""

    connected: bool
    version: str | None
    databaseSize: int
    indexes: dict


@router.get("/search", response_model=SearchResponse)
async def unified_search(
    q: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(20, ge=1, le=100, description="Maximum results"),
    types: str | None = Query(None, description="Comma-separated types to search"),
    score_threshold: float | None = Query(
        None, ge=0, le=1, description="Minimum ranking score (0-1)"
    ),
    current_user: User = Depends(get_current_user),
):
    """
    Unified search across all BrAPI entities.

    Searches germplasm, trials, traits, locations, programs, and studies.
    Returns results ranked by relevance with type indicators.

    New in v1.10+: Uses federated search for better cross-index ranking.
    """
    try:
        from app.core.meilisearch import get_meilisearch

        meilisearch = get_meilisearch()

        if not meilisearch.connected:
            raise HTTPException(status_code=503, detail="Search service unavailable")

        # Parse types filter
        type_filter = types.split(",") if types else None

        # Use federated search for better ranking
        raw_results = meilisearch.federated_search(
            q,
            type_filter,
            limit,
            organization_id=current_user.organization_id,
        )

        # Transform results
        results = []
        for hit in raw_results.get("hits", []):
            # Get index from federation metadata or fallback
            index_type = hit.get("_federation", {}).get("indexUid") or hit.get("_index", "unknown")

            result = transform_hit(hit, index_type)
            if result:
                # Apply score threshold if specified
                if score_threshold and hit.get("_rankingScore", 1) < score_threshold:
                    continue
                result.score = hit.get("_rankingScore")
                results.append(result)

        return SearchResponse(
            query=q,
            results=results[:limit],
            total=len(results),
            processingTimeMs=raw_results.get("processingTimeMs", 0),
        )

    except HTTPException:
        raise
    except Exception:
        # Fallback to legacy search if federated fails
        logger.warning("Federated search failed; using legacy search", exc_info=True)
        return await legacy_search(q, limit, types, current_user.organization_id)


async def legacy_search(
    q: str,
    limit: int,
    types: str | None,
    organization_id: int,
) -> SearchResponse:
    """Legacy search fallback"""
    try:
        from app.core.meilisearch import get_meilisearch

        meilisearch = get_meilisearch()

        type_filter = types.split(",") if types else None
        raw_results = meilisearch.search_all(
            q,
            limit=limit,
            organization_id=organization_id,
        )

        results = []
        for hit in raw_results:
            index_type = hit.get("_index", "unknown")
            if type_filter and index_type not in type_filter:
                continue
            result = transform_hit(hit, index_type)
            if result:
                result.score = hit.get("_rankingScore")
                results.append(result)

        return SearchResponse(
            query=q,
            results=results[:limit],
            total=len(results),
            processingTimeMs=0,
        )
    except Exception:
        logger.warning("Legacy search failed", exc_info=True)
        return SearchResponse(query=q, results=[], total=0, processingTimeMs=0)


@router.get("/search/federated", response_model=FederatedSearchResponse)
async def federated_search(
    q: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(20, ge=1, le=100, description="Maximum results"),
    indexes: str | None = Query(None, description="Comma-separated index names"),
    score_threshold: float | None = Query(None, ge=0, le=1, description="Minimum ranking score"),
    current_user: User = Depends(get_current_user),
):
    """
    Federated search across multiple indexes (v1.10+ feature).

    Merges results from specified indexes into a single ranked response.
    Better ranking than searching indexes separately.
    """
    try:
        from app.core.meilisearch import INDEXES, get_meilisearch

        meilisearch = get_meilisearch()

        if not meilisearch.connected:
            raise HTTPException(status_code=503, detail="Search service unavailable")

        # Parse indexes filter
        target_indexes = indexes.split(",") if indexes else list(INDEXES.values())

        raw_results = meilisearch.federated_search(
            q,
            target_indexes,
            limit,
            organization_id=current_user.organization_id,
        )

        results = []
        for hit in raw_results.get("hits", []):
            index_type = hit.get("_federation", {}).get("indexUid") or hit.get("_index", "unknown")
            result = transform_hit(hit, index_type)
            if result:
                if score_threshold and hit.get("_rankingScore", 1) < score_threshold:
                    continue
                result.score = hit.get("_rankingScore")
                results.append(result)

        return FederatedSearchResponse(
            query=q,
            results=results[:limit],
            total=len(results),
            processingTimeMs=raw_results.get("processingTimeMs", 0),
            indexes=target_indexes,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Federated search failed")
        raise HTTPException(status_code=500, detail="Search request failed") from e


@router.get("/search/similar/{index_name}/{document_id}", response_model=SimilarDocumentsResponse)
async def get_similar_documents(
    index_name: str,
    document_id: str,
    limit: int = Query(10, ge=1, le=50, description="Maximum results"),
    filter: str | None = Query(None, description="Filter expression"),
    current_user: User = Depends(get_current_user),
):
    """
    Get similar documents (v1.9+ feature).

    Finds documents similar to the given document based on content.
    Useful for "related items" or "you might also like" features.
    """
    try:
        from app.core.meilisearch import INDEXES, get_meilisearch

        meilisearch = get_meilisearch()

        if not meilisearch.connected:
            raise HTTPException(status_code=503, detail="Search service unavailable")

        # Validate index name
        if index_name not in INDEXES.values():
            raise HTTPException(status_code=400, detail=f"Invalid index: {index_name}")

        raw_results = meilisearch.get_similar_documents(
            index_name,
            document_id,
            limit,
            filter,
            organization_id=current_user.organization_id,
        )

        results = []
        for hit in raw_results.get("hits", []):
            result = transform_hit(hit, index_name)
            if result:
                result.score = hit.get("_rankingScore")
                results.append(result)

        return SimilarDocumentsResponse(
            documentId=document_id,
            indexName=index_name,
            results=results,
            total=len(results),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Similar documents search failed")
        raise HTTPException(status_code=500, detail="Search request failed") from e


@router.get("/search/geo/locations", response_model=GeoSearchResponse)
async def geo_search_locations(
    q: str = Query("", description="Search query (optional)"),
    lat: float = Query(..., ge=-90, le=90, description="Latitude"),
    lng: float = Query(..., ge=-180, le=180, description="Longitude"),
    radius_km: float = Query(100, ge=1, le=20000, description="Search radius in km"),
    limit: int = Query(20, ge=1, le=100, description="Maximum results"),
    current_user: User = Depends(get_current_user),
):
    """
    Geo search for locations within a radius.

    Finds locations within the specified radius of the given coordinates.
    Results are sorted by distance from the center point.
    """
    try:
        from app.core.meilisearch import get_meilisearch

        meilisearch = get_meilisearch()

        if not meilisearch.connected:
            raise HTTPException(status_code=503, detail="Search service unavailable")

        raw_results = meilisearch.geo_search(
            "locations",
            q,
            lat,
            lng,
            radius_km,
            limit,
            organization_id=current_user.organization_id,
        )

        results = []
        for hit in raw_results.get("hits", []):
            result = transform_hit(hit, "locations")
            if result:
                result.score = hit.get("_geoDistance")  # Distance in meters
                results.append(result)

        return GeoSearchResponse(
            query=q,
            results=results,
            total=len(results),
            center={"lat": lat, "lng": lng},
            radiusKm=radius_km,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Geo search failed")
        raise HTTPException(status_code=500, detail="Search request failed") from e


@router.get("/search/stats", response_model=SearchStatsResponse)
async def get_search_stats(current_user: User = Depends(get_current_user)):
    """
    Get search service statistics.

    Returns connection status, version, database size, and index stats.
    """
    try:
        from app.core.meilisearch import get_meilisearch

        meilisearch = get_meilisearch()

        stats = meilisearch.get_stats()

        if not current_user.is_superuser:
            return SearchStatsResponse(
                connected=meilisearch.connected,
                version=stats.get("version"),
                databaseSize=0,
                indexes={},
            )

        return SearchStatsResponse(
            connected=meilisearch.connected,
            version=stats.get("version"),
            databaseSize=stats.get("databaseSize", 0),
            indexes=stats.get("indexes", {}),
        )

    except Exception:
        logger.warning("Search stats failed", exc_info=True)
        return SearchStatsResponse(
            connected=False,
            version=None,
            databaseSize=0,
            indexes={},
        )


@router.get("/search/germplasm")
async def search_germplasm(
    q: str = Query(..., min_length=1),
    limit: int = Query(20, ge=1, le=100),
    species: str | None = Query(None, description="Filter by species"),
    country: str | None = Query(None, description="Filter by country"),
    current_user: User = Depends(get_current_user),
):
    """Search germplasm with optional filters"""
    try:
        from app.core.meilisearch import get_meilisearch

        meilisearch = get_meilisearch()

        if not meilisearch.connected:
            return {"hits": [], "query": q}

        options = {
            "limit": limit,
            "showRankingScore": True,
        }

        # Build filter
        filters = []
        if species:
            filters.append(_eq_filter("species", species))
        if country:
            filters.append(_eq_filter("countryOfOrigin", country))
        if filters:
            options["filter"] = " AND ".join(filters)

        return meilisearch.search(
            "germplasm",
            q,
            options,
            organization_id=current_user.organization_id,
        )
    except Exception:
        logger.warning("Germplasm search failed", exc_info=True)
        return {"hits": [], "query": q}


@router.get("/search/traits")
async def search_traits(
    q: str = Query(..., min_length=1),
    limit: int = Query(20, ge=1, le=100),
    trait_class: str | None = Query(None, description="Filter by trait class"),
    current_user: User = Depends(get_current_user),
):
    """Search traits/observation variables with optional filters"""
    try:
        from app.core.meilisearch import get_meilisearch

        meilisearch = get_meilisearch()

        if not meilisearch.connected:
            return {"hits": [], "query": q}

        options = {
            "limit": limit,
            "showRankingScore": True,
        }

        if trait_class:
            options["filter"] = _eq_filter("trait.traitClass", trait_class)

        return meilisearch.search(
            "traits",
            q,
            options,
            organization_id=current_user.organization_id,
        )
    except Exception:
        logger.warning("Traits search failed", exc_info=True)
        return {"hits": [], "query": q}


@router.get("/search/trials")
async def search_trials(
    q: str = Query(..., min_length=1),
    limit: int = Query(20, ge=1, le=100),
    program_id: str | None = Query(None, description="Filter by program"),
    active: bool | None = Query(None, description="Filter by active status"),
    current_user: User = Depends(get_current_user),
):
    """Search trials with optional filters"""
    try:
        from app.core.meilisearch import get_meilisearch

        meilisearch = get_meilisearch()

        if not meilisearch.connected:
            return {"hits": [], "query": q}

        options = {
            "limit": limit,
            "showRankingScore": True,
        }

        filters = []
        if program_id:
            filters.append(_eq_filter("programDbId", program_id))
        if active is not None:
            filters.append(f"active = {str(active).lower()}")
        if filters:
            options["filter"] = " AND ".join(filters)

        return meilisearch.search(
            "trials",
            q,
            options,
            organization_id=current_user.organization_id,
        )
    except Exception:
        logger.warning("Trials search failed", exc_info=True)
        return {"hits": [], "query": q}


@router.get("/search/programs")
async def search_programs(
    q: str = Query(..., min_length=1),
    limit: int = Query(20, ge=1, le=100),
    crop: str | None = Query(None, description="Filter by crop name"),
    current_user: User = Depends(get_current_user),
):
    """Search breeding programs"""
    try:
        from app.core.meilisearch import get_meilisearch

        meilisearch = get_meilisearch()

        if not meilisearch.connected:
            return {"hits": [], "query": q}

        options = {
            "limit": limit,
            "showRankingScore": True,
        }

        if crop:
            options["filter"] = _eq_filter("commonCropName", crop)

        return meilisearch.search(
            "programs",
            q,
            options,
            organization_id=current_user.organization_id,
        )
    except Exception:
        logger.warning("Programs search failed", exc_info=True)
        return {"hits": [], "query": q}


@router.get("/search/studies")
async def search_studies(
    q: str = Query(..., min_length=1),
    limit: int = Query(20, ge=1, le=100),
    trial_id: str | None = Query(None, description="Filter by trial"),
    study_type: str | None = Query(None, description="Filter by study type"),
    current_user: User = Depends(get_current_user),
):
    """Search studies"""
    try:
        from app.core.meilisearch import get_meilisearch

        meilisearch = get_meilisearch()

        if not meilisearch.connected:
            return {"hits": [], "query": q}

        options = {
            "limit": limit,
            "showRankingScore": True,
        }

        filters = []
        if trial_id:
            filters.append(_eq_filter("trialDbId", trial_id))
        if study_type:
            filters.append(_eq_filter("studyType", study_type))
        if filters:
            options["filter"] = " AND ".join(filters)

        return meilisearch.search(
            "studies",
            q,
            options,
            organization_id=current_user.organization_id,
        )
    except Exception:
        logger.warning("Studies search failed", exc_info=True)
        return {"hits": [], "query": q}


@router.get("/search/locations")
async def search_locations(
    q: str = Query(..., min_length=1),
    limit: int = Query(20, ge=1, le=100),
    country: str | None = Query(None, description="Filter by country code"),
    location_type: str | None = Query(None, description="Filter by location type"),
    current_user: User = Depends(get_current_user),
):
    """Search locations"""
    try:
        from app.core.meilisearch import get_meilisearch

        meilisearch = get_meilisearch()

        if not meilisearch.connected:
            return {"hits": [], "query": q}

        options = {
            "limit": limit,
            "showRankingScore": True,
        }

        filters = []
        if country:
            filters.append(_eq_filter("countryCode", country))
        if location_type:
            filters.append(_eq_filter("locationType", location_type))
        if filters:
            options["filter"] = " AND ".join(filters)

        return meilisearch.search(
            "locations",
            q,
            options,
            organization_id=current_user.organization_id,
        )
    except Exception:
        logger.warning("Locations search failed", exc_info=True)
        return {"hits": [], "query": q}


def transform_hit(hit: dict, index_type: str) -> SearchResult | None:
    """Transform a Meilisearch hit to SearchResult"""

    if index_type == "germplasm":
        return SearchResult(
            id=hit.get("germplasmDbId", ""),
            type="germplasm",
            title=hit.get("germplasmName", "Unknown"),
            subtitle=hit.get("accessionNumber"),
            description=f"{hit.get('species', '')} • {hit.get('countryOfOrigin', '')}".strip(" •"),
            path=f"/germplasm/{hit.get('germplasmDbId')}",
        )

    elif index_type == "traits":
        trait = hit.get("trait", {})
        return SearchResult(
            id=hit.get("observationVariableDbId", ""),
            type="trait",
            title=hit.get("observationVariableName", "Unknown"),
            subtitle=trait.get("traitName"),
            description=trait.get("traitDescription", "")[:100]
            if trait.get("traitDescription")
            else None,
            path=f"/traits/{hit.get('observationVariableDbId')}",
        )

    elif index_type == "trials":
        return SearchResult(
            id=hit.get("trialDbId", ""),
            type="trial",
            title=hit.get("trialName", "Unknown"),
            subtitle=hit.get("programName"),
            description=hit.get("locationName"),
            path=f"/trials/{hit.get('trialDbId')}",
        )

    elif index_type == "locations":
        return SearchResult(
            id=hit.get("locationDbId", ""),
            type="location",
            title=hit.get("locationName", "Unknown"),
            subtitle=hit.get("locationType"),
            description=hit.get("countryName"),
            path=f"/locations/{hit.get('locationDbId')}",
        )

    elif index_type == "programs":
        return SearchResult(
            id=hit.get("programDbId", ""),
            type="program",
            title=hit.get("programName", "Unknown"),
            subtitle=hit.get("commonCropName"),
            description=hit.get("objective"),
            path=f"/programs/{hit.get('programDbId')}",
        )

    elif index_type == "studies":
        return SearchResult(
            id=hit.get("studyDbId", ""),
            type="study",
            title=hit.get("studyName", "Unknown"),
            subtitle=hit.get("studyType"),
            description=hit.get("locationName"),
            path=f"/studies/{hit.get('studyDbId')}",
        )

    return None
