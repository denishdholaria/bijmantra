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

from fastapi import APIRouter, Query, Depends, HTTPException
from typing import List, Optional
from pydantic import BaseModel
from app.api.deps import get_current_user

router = APIRouter(dependencies=[Depends(get_current_user)])


class SearchResult(BaseModel):
    """Search result item"""
    id: str
    type: str
    title: str
    subtitle: Optional[str] = None
    description: Optional[str] = None
    path: str
    score: Optional[float] = None


class SearchResponse(BaseModel):
    """Search response"""
    query: str
    results: List[SearchResult]
    total: int
    processingTimeMs: int


class FederatedSearchResponse(BaseModel):
    """Federated search response with merged results"""
    query: str
    results: List[SearchResult]
    total: int
    processingTimeMs: int
    indexes: List[str]


class SimilarDocumentsResponse(BaseModel):
    """Similar documents response"""
    documentId: str
    indexName: str
    results: List[SearchResult]
    total: int


class GeoSearchResponse(BaseModel):
    """Geo search response"""
    query: str
    results: List[SearchResult]
    total: int
    center: dict
    radiusKm: float


class SearchStatsResponse(BaseModel):
    """Search service statistics"""
    connected: bool
    version: Optional[str]
    databaseSize: int
    indexes: dict


@router.get("/search", response_model=SearchResponse)
async def unified_search(
    q: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(20, ge=1, le=100, description="Maximum results"),
    types: Optional[str] = Query(None, description="Comma-separated types to search"),
    score_threshold: Optional[float] = Query(None, ge=0, le=1, description="Minimum ranking score (0-1)"),
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
            raise HTTPException(
                status_code=503,
                detail="Search service unavailable"
            )

        # Parse types filter
        type_filter = types.split(',') if types else None

        # Use federated search for better ranking
        raw_results = meilisearch.federated_search(q, type_filter, limit)

        # Transform results
        results = []
        for hit in raw_results.get('hits', []):
            # Get index from federation metadata or fallback
            index_type = hit.get('_federation', {}).get('indexUid') or hit.get('_index', 'unknown')

            result = transform_hit(hit, index_type)
            if result:
                # Apply score threshold if specified
                if score_threshold and hit.get('_rankingScore', 1) < score_threshold:
                    continue
                result.score = hit.get('_rankingScore')
                results.append(result)

        return SearchResponse(
            query=q,
            results=results[:limit],
            total=len(results),
            processingTimeMs=raw_results.get('processingTimeMs', 0),
        )

    except HTTPException:
        raise
    except Exception as e:
        # Fallback to legacy search if federated fails
        print(f"[Search] Federated search failed, using legacy: {e}")
        return await legacy_search(q, limit, types)


async def legacy_search(q: str, limit: int, types: Optional[str]) -> SearchResponse:
    """Legacy search fallback"""
    try:
        from app.core.meilisearch import get_meilisearch
        meilisearch = get_meilisearch()

        type_filter = types.split(',') if types else None
        raw_results = meilisearch.search_all(q, limit=limit)

        results = []
        for hit in raw_results:
            index_type = hit.get('_index', 'unknown')
            if type_filter and index_type not in type_filter:
                continue
            result = transform_hit(hit, index_type)
            if result:
                result.score = hit.get('_rankingScore')
                results.append(result)

        return SearchResponse(
            query=q,
            results=results[:limit],
            total=len(results),
            processingTimeMs=0,
        )
    except Exception as e:
        print(f"[Search] Legacy search error: {e}")
        return SearchResponse(query=q, results=[], total=0, processingTimeMs=0)


@router.get("/search/federated", response_model=FederatedSearchResponse)
async def federated_search(
    q: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(20, ge=1, le=100, description="Maximum results"),
    indexes: Optional[str] = Query(None, description="Comma-separated index names"),
    score_threshold: Optional[float] = Query(None, ge=0, le=1, description="Minimum ranking score"),
):
    """
    Federated search across multiple indexes (v1.10+ feature).
    
    Merges results from specified indexes into a single ranked response.
    Better ranking than searching indexes separately.
    """
    try:
        from app.core.meilisearch import get_meilisearch, INDEXES
        meilisearch = get_meilisearch()

        if not meilisearch.connected:
            raise HTTPException(status_code=503, detail="Search service unavailable")

        # Parse indexes filter
        target_indexes = indexes.split(',') if indexes else list(INDEXES.values())

        raw_results = meilisearch.federated_search(q, target_indexes, limit)

        results = []
        for hit in raw_results.get('hits', []):
            index_type = hit.get('_federation', {}).get('indexUid') or hit.get('_index', 'unknown')
            result = transform_hit(hit, index_type)
            if result:
                if score_threshold and hit.get('_rankingScore', 1) < score_threshold:
                    continue
                result.score = hit.get('_rankingScore')
                results.append(result)

        return FederatedSearchResponse(
            query=q,
            results=results[:limit],
            total=len(results),
            processingTimeMs=raw_results.get('processingTimeMs', 0),
            indexes=target_indexes,
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"[Search] Federated search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search/similar/{index_name}/{document_id}", response_model=SimilarDocumentsResponse)
async def get_similar_documents(
    index_name: str,
    document_id: str,
    limit: int = Query(10, ge=1, le=50, description="Maximum results"),
    filter: Optional[str] = Query(None, description="Filter expression"),
):
    """
    Get similar documents (v1.9+ feature).
    
    Finds documents similar to the given document based on content.
    Useful for "related items" or "you might also like" features.
    """
    try:
        from app.core.meilisearch import get_meilisearch, INDEXES
        meilisearch = get_meilisearch()

        if not meilisearch.connected:
            raise HTTPException(status_code=503, detail="Search service unavailable")

        # Validate index name
        if index_name not in INDEXES.values():
            raise HTTPException(status_code=400, detail=f"Invalid index: {index_name}")

        raw_results = meilisearch.get_similar_documents(index_name, document_id, limit, filter)

        results = []
        for hit in raw_results.get('hits', []):
            result = transform_hit(hit, index_name)
            if result:
                result.score = hit.get('_rankingScore')
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
        print(f"[Search] Similar documents error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search/geo/locations", response_model=GeoSearchResponse)
async def geo_search_locations(
    q: str = Query("", description="Search query (optional)"),
    lat: float = Query(..., ge=-90, le=90, description="Latitude"),
    lng: float = Query(..., ge=-180, le=180, description="Longitude"),
    radius_km: float = Query(100, ge=1, le=20000, description="Search radius in km"),
    limit: int = Query(20, ge=1, le=100, description="Maximum results"),
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

        raw_results = meilisearch.geo_search('locations', q, lat, lng, radius_km, limit)

        results = []
        for hit in raw_results.get('hits', []):
            result = transform_hit(hit, 'locations')
            if result:
                result.score = hit.get('_geoDistance')  # Distance in meters
                results.append(result)

        return GeoSearchResponse(
            query=q,
            results=results,
            total=len(results),
            center={'lat': lat, 'lng': lng},
            radiusKm=radius_km,
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"[Search] Geo search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search/stats", response_model=SearchStatsResponse)
async def get_search_stats():
    """
    Get search service statistics.
    
    Returns connection status, version, database size, and index stats.
    """
    try:
        from app.core.meilisearch import get_meilisearch
        meilisearch = get_meilisearch()

        stats = meilisearch.get_stats()

        return SearchStatsResponse(
            connected=meilisearch.connected,
            version=stats.get('version'),
            databaseSize=stats.get('databaseSize', 0),
            indexes=stats.get('indexes', {}),
        )

    except Exception as e:
        print(f"[Search] Stats error: {e}")
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
    species: Optional[str] = Query(None, description="Filter by species"),
    country: Optional[str] = Query(None, description="Filter by country"),
):
    """Search germplasm with optional filters"""
    try:
        from app.core.meilisearch import get_meilisearch
        meilisearch = get_meilisearch()

        if not meilisearch.connected:
            return {"hits": [], "query": q}

        options = {
            'limit': limit,
            'showRankingScore': True,
        }

        # Build filter
        filters = []
        if species:
            filters.append(f'species = "{species}"')
        if country:
            filters.append(f'countryOfOrigin = "{country}"')
        if filters:
            options['filter'] = ' AND '.join(filters)

        return meilisearch.search('germplasm', q, options)
    except Exception as e:
        print(f"[Search] Germplasm search error: {e}")
        return {"hits": [], "query": q}


@router.get("/search/traits")
async def search_traits(
    q: str = Query(..., min_length=1),
    limit: int = Query(20, ge=1, le=100),
    trait_class: Optional[str] = Query(None, description="Filter by trait class"),
):
    """Search traits/observation variables with optional filters"""
    try:
        from app.core.meilisearch import get_meilisearch
        meilisearch = get_meilisearch()

        if not meilisearch.connected:
            return {"hits": [], "query": q}

        options = {
            'limit': limit,
            'showRankingScore': True,
        }

        if trait_class:
            options['filter'] = f'trait.traitClass = "{trait_class}"'

        return meilisearch.search('traits', q, options)
    except Exception as e:
        print(f"[Search] Traits search error: {e}")
        return {"hits": [], "query": q}


@router.get("/search/trials")
async def search_trials(
    q: str = Query(..., min_length=1),
    limit: int = Query(20, ge=1, le=100),
    program_id: Optional[str] = Query(None, description="Filter by program"),
    active: Optional[bool] = Query(None, description="Filter by active status"),
):
    """Search trials with optional filters"""
    try:
        from app.core.meilisearch import get_meilisearch
        meilisearch = get_meilisearch()

        if not meilisearch.connected:
            return {"hits": [], "query": q}

        options = {
            'limit': limit,
            'showRankingScore': True,
        }

        filters = []
        if program_id:
            filters.append(f'programDbId = "{program_id}"')
        if active is not None:
            filters.append(f'active = {str(active).lower()}')
        if filters:
            options['filter'] = ' AND '.join(filters)

        return meilisearch.search('trials', q, options)
    except Exception as e:
        print(f"[Search] Trials search error: {e}")
        return {"hits": [], "query": q}


@router.get("/search/programs")
async def search_programs(
    q: str = Query(..., min_length=1),
    limit: int = Query(20, ge=1, le=100),
    crop: Optional[str] = Query(None, description="Filter by crop name"),
):
    """Search breeding programs"""
    try:
        from app.core.meilisearch import get_meilisearch
        meilisearch = get_meilisearch()

        if not meilisearch.connected:
            return {"hits": [], "query": q}

        options = {
            'limit': limit,
            'showRankingScore': True,
        }

        if crop:
            options['filter'] = f'commonCropName = "{crop}"'

        return meilisearch.search('programs', q, options)
    except Exception as e:
        print(f"[Search] Programs search error: {e}")
        return {"hits": [], "query": q}


@router.get("/search/studies")
async def search_studies(
    q: str = Query(..., min_length=1),
    limit: int = Query(20, ge=1, le=100),
    trial_id: Optional[str] = Query(None, description="Filter by trial"),
    study_type: Optional[str] = Query(None, description="Filter by study type"),
):
    """Search studies"""
    try:
        from app.core.meilisearch import get_meilisearch
        meilisearch = get_meilisearch()

        if not meilisearch.connected:
            return {"hits": [], "query": q}

        options = {
            'limit': limit,
            'showRankingScore': True,
        }

        filters = []
        if trial_id:
            filters.append(f'trialDbId = "{trial_id}"')
        if study_type:
            filters.append(f'studyType = "{study_type}"')
        if filters:
            options['filter'] = ' AND '.join(filters)

        return meilisearch.search('studies', q, options)
    except Exception as e:
        print(f"[Search] Studies search error: {e}")
        return {"hits": [], "query": q}


@router.get("/search/locations")
async def search_locations(
    q: str = Query(..., min_length=1),
    limit: int = Query(20, ge=1, le=100),
    country: Optional[str] = Query(None, description="Filter by country code"),
    location_type: Optional[str] = Query(None, description="Filter by location type"),
):
    """Search locations"""
    try:
        from app.core.meilisearch import get_meilisearch
        meilisearch = get_meilisearch()

        if not meilisearch.connected:
            return {"hits": [], "query": q}

        options = {
            'limit': limit,
            'showRankingScore': True,
        }

        filters = []
        if country:
            filters.append(f'countryCode = "{country}"')
        if location_type:
            filters.append(f'locationType = "{location_type}"')
        if filters:
            options['filter'] = ' AND '.join(filters)

        return meilisearch.search('locations', q, options)
    except Exception as e:
        print(f"[Search] Locations search error: {e}")
        return {"hits": [], "query": q}


def transform_hit(hit: dict, index_type: str) -> Optional[SearchResult]:
    """Transform a Meilisearch hit to SearchResult"""

    if index_type == 'germplasm':
        return SearchResult(
            id=hit.get('germplasmDbId', ''),
            type='germplasm',
            title=hit.get('germplasmName', 'Unknown'),
            subtitle=hit.get('accessionNumber'),
            description=f"{hit.get('species', '')} • {hit.get('countryOfOrigin', '')}".strip(' •'),
            path=f"/germplasm/{hit.get('germplasmDbId')}",
        )

    elif index_type == 'traits':
        trait = hit.get('trait', {})
        return SearchResult(
            id=hit.get('observationVariableDbId', ''),
            type='trait',
            title=hit.get('observationVariableName', 'Unknown'),
            subtitle=trait.get('traitName'),
            description=trait.get('traitDescription', '')[:100] if trait.get('traitDescription') else None,
            path=f"/traits/{hit.get('observationVariableDbId')}",
        )

    elif index_type == 'trials':
        return SearchResult(
            id=hit.get('trialDbId', ''),
            type='trial',
            title=hit.get('trialName', 'Unknown'),
            subtitle=hit.get('programName'),
            description=hit.get('locationName'),
            path=f"/trials/{hit.get('trialDbId')}",
        )

    elif index_type == 'locations':
        return SearchResult(
            id=hit.get('locationDbId', ''),
            type='location',
            title=hit.get('locationName', 'Unknown'),
            subtitle=hit.get('locationType'),
            description=hit.get('countryName'),
            path=f"/locations/{hit.get('locationDbId')}",
        )

    elif index_type == 'programs':
        return SearchResult(
            id=hit.get('programDbId', ''),
            type='program',
            title=hit.get('programName', 'Unknown'),
            subtitle=hit.get('commonCropName'),
            description=hit.get('objective'),
            path=f"/programs/{hit.get('programDbId')}",
        )

    elif index_type == 'studies':
        return SearchResult(
            id=hit.get('studyDbId', ''),
            type='study',
            title=hit.get('studyName', 'Unknown'),
            subtitle=hit.get('studyType'),
            description=hit.get('locationName'),
            path=f"/studies/{hit.get('studyDbId')}",
        )

    return None
