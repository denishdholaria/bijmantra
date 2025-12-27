"""
Search API Endpoints
Unified search across all BrAPI entities using Meilisearch
"""

from fastapi import APIRouter, Query, Depends, HTTPException
from typing import List, Optional
from pydantic import BaseModel

router = APIRouter()


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


@router.get("/search", response_model=SearchResponse)
async def unified_search(
    q: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(20, ge=1, le=100, description="Maximum results"),
    types: Optional[str] = Query(None, description="Comma-separated types to search"),
):
    """
    Unified search across all BrAPI entities.
    
    Searches germplasm, trials, traits, locations, and observations.
    Returns results ranked by relevance with type indicators.
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
        
        # Search all indexes
        raw_results = meilisearch.search_all(q, limit=limit)
        
        # Transform results
        results = []
        for hit in raw_results:
            index_type = hit.get('_index', 'unknown')
            
            # Skip if type filter is set and doesn't match
            if type_filter and index_type not in type_filter:
                continue
            
            result = transform_hit(hit, index_type)
            if result:
                results.append(result)
        
        return SearchResponse(
            query=q,
            results=results[:limit],
            total=len(results),
            processingTimeMs=0,  # Meilisearch is fast enough
        )
        
    except HTTPException:
        raise
    except Exception as e:
        # Fallback to empty results if search fails
        print(f"[Search] Error: {e}")
        return SearchResponse(
            query=q,
            results=[],
            total=0,
            processingTimeMs=0,
        )


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
    
    return None


@router.get("/search/germplasm")
async def search_germplasm(
    q: str = Query(..., min_length=1),
    limit: int = Query(20, ge=1, le=100),
):
    """Search germplasm only"""
    try:
        from app.core.meilisearch import get_meilisearch
        meilisearch = get_meilisearch()
        
        if not meilisearch.connected:
            return {"hits": [], "query": q}
        
        return meilisearch.search('germplasm', q, {'limit': limit})
    except Exception as e:
        print(f"[Search] Germplasm search error: {e}")
        return {"hits": [], "query": q}


@router.get("/search/traits")
async def search_traits(
    q: str = Query(..., min_length=1),
    limit: int = Query(20, ge=1, le=100),
):
    """Search traits/observation variables only"""
    try:
        from app.core.meilisearch import get_meilisearch
        meilisearch = get_meilisearch()
        
        if not meilisearch.connected:
            return {"hits": [], "query": q}
        
        return meilisearch.search('traits', q, {'limit': limit})
    except Exception as e:
        print(f"[Search] Traits search error: {e}")
        return {"hits": [], "query": q}


@router.get("/search/trials")
async def search_trials(
    q: str = Query(..., min_length=1),
    limit: int = Query(20, ge=1, le=100),
):
    """Search trials only"""
    try:
        from app.core.meilisearch import get_meilisearch
        meilisearch = get_meilisearch()
        
        if not meilisearch.connected:
            return {"hits": [], "query": q}
        
        return meilisearch.search('trials', q, {'limit': limit})
    except Exception as e:
        print(f"[Search] Trials search error: {e}")
        return {"hits": [], "query": q}
