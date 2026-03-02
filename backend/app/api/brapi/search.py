"""
BrAPI v2.1 Search Endpoints

Implements all BrAPI search endpoints following the async search pattern:
1. POST /search/{entity} - Submit search request, returns searchResultsDbId
2. GET /search/{entity}/{searchResultsDbId} - Retrieve search results

BrAPI v2.1 Spec: https://brapi.org/specification

Production-ready: Uses Redis for search result caching with in-memory fallback.
Search results auto-expire after 30 minutes.
"""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_optional_user
from app.core.database import get_db
from app.models.core import List as ListModel
from app.models.core import Location, Program, Study, Trial

# Core models
from app.models.core import Person as PersonModel

# Genotyping models
from app.models.genotyping import (
    Call,
    CallSet,
    GenomeMap,
    MarkerPosition,
    Plate,
    Reference,
    ReferenceSet,
    Variant,
    VariantSet,
)

# Germplasm models
from app.models.germplasm import Germplasm, GermplasmAttribute

# Phenotyping models
from app.models.phenotyping import Image, Observation, ObservationUnit, ObservationVariable, Sample
from app.services.job_service import job_service


router = APIRouter()


class SearchRequestBase(BaseModel):
    """Base search request with common pagination"""
    page: int | None = 0
    pageSize: int | None = 1000


class GermplasmSearchRequest(SearchRequestBase):
    germplasmDbIds: list[str] | None = None
    germplasmNames: list[str] | None = None
    germplasmPUIs: list[str] | None = None
    accessionNumbers: list[str] | None = None
    commonCropNames: list[str] | None = None
    species: list[str] | None = None
    genus: list[str] | None = None
    studyDbIds: list[str] | None = None
    programDbIds: list[str] | None = None
    trialDbIds: list[str] | None = None
    externalReferenceIds: list[str] | None = None
    externalReferenceSources: list[str] | None = None


class StudySearchRequest(SearchRequestBase):
    studyDbIds: list[str] | None = None
    studyNames: list[str] | None = None
    studyTypes: list[str] | None = None
    studyCodes: list[str] | None = None
    commonCropNames: list[str] | None = None
    programDbIds: list[str] | None = None
    programNames: list[str] | None = None
    trialDbIds: list[str] | None = None
    trialNames: list[str] | None = None
    locationDbIds: list[str] | None = None
    locationNames: list[str] | None = None
    seasonDbIds: list[str] | None = None
    active: bool | None = None
    sortBy: str | None = None
    sortOrder: str | None = None


class TrialSearchRequest(SearchRequestBase):
    trialDbIds: list[str] | None = None
    trialNames: list[str] | None = None
    trialPUIs: list[str] | None = None
    commonCropNames: list[str] | None = None
    programDbIds: list[str] | None = None
    programNames: list[str] | None = None
    locationDbIds: list[str] | None = None
    locationNames: list[str] | None = None
    contactDbIds: list[str] | None = None
    active: bool | None = None
    sortBy: str | None = None
    sortOrder: str | None = None


class ProgramSearchRequest(SearchRequestBase):
    programDbIds: list[str] | None = None
    programNames: list[str] | None = None
    programTypes: list[str] | None = None
    commonCropNames: list[str] | None = None
    abbreviations: list[str] | None = None
    leadPersonDbIds: list[str] | None = None
    leadPersonNames: list[str] | None = None


class LocationSearchRequest(SearchRequestBase):
    locationDbIds: list[str] | None = None
    locationNames: list[str] | None = None
    locationTypes: list[str] | None = None
    countryCodes: list[str] | None = None
    countryNames: list[str] | None = None
    instituteAddresses: list[str] | None = None
    instituteNames: list[str] | None = None
    abbreviations: list[str] | None = None
    altitudeMin: float | None = None
    altitudeMax: float | None = None
    coordinates: dict | None = None


class ObservationSearchRequest(SearchRequestBase):
    observationDbIds: list[str] | None = None
    observationUnitDbIds: list[str] | None = None
    germplasmDbIds: list[str] | None = None
    germplasmNames: list[str] | None = None
    studyDbIds: list[str] | None = None
    studyNames: list[str] | None = None
    trialDbIds: list[str] | None = None
    trialNames: list[str] | None = None
    programDbIds: list[str] | None = None
    seasonDbIds: list[str] | None = None
    locationDbIds: list[str] | None = None
    observationVariableDbIds: list[str] | None = None
    observationVariableNames: list[str] | None = None
    observationTimeStampRangeStart: str | None = None
    observationTimeStampRangeEnd: str | None = None
    observationLevelRelationships: list[dict] | None = None
    observationLevels: list[dict] | None = None


class ObservationUnitSearchRequest(SearchRequestBase):
    observationUnitDbIds: list[str] | None = None
    observationUnitNames: list[str] | None = None
    germplasmDbIds: list[str] | None = None
    germplasmNames: list[str] | None = None
    studyDbIds: list[str] | None = None
    studyNames: list[str] | None = None
    trialDbIds: list[str] | None = None
    trialNames: list[str] | None = None
    programDbIds: list[str] | None = None
    seasonDbIds: list[str] | None = None
    locationDbIds: list[str] | None = None
    observationLevelRelationships: list[dict] | None = None
    observationLevels: list[dict] | None = None
    includeObservations: bool | None = None


class VariableSearchRequest(SearchRequestBase):
    observationVariableDbIds: list[str] | None = None
    observationVariableNames: list[str] | None = None
    observationVariablePUIs: list[str] | None = None
    traitDbIds: list[str] | None = None
    traitNames: list[str] | None = None
    traitClasses: list[str] | None = None
    methodDbIds: list[str] | None = None
    methodNames: list[str] | None = None
    scaleDbIds: list[str] | None = None
    scaleNames: list[str] | None = None
    ontologyDbIds: list[str] | None = None
    commonCropNames: list[str] | None = None
    studyDbIds: list[str] | None = None
    dataTypes: list[str] | None = None


class ImageSearchRequest(SearchRequestBase):
    imageDbIds: list[str] | None = None
    imageNames: list[str] | None = None
    imageFileNames: list[str] | None = None
    imageFileSizeMin: int | None = None
    imageFileSizeMax: int | None = None
    imageHeightMin: int | None = None
    imageHeightMax: int | None = None
    imageWidthMin: int | None = None
    imageWidthMax: int | None = None
    mimeTypes: list[str] | None = None
    observationUnitDbIds: list[str] | None = None
    observationDbIds: list[str] | None = None
    descriptiveOntologyTerms: list[str] | None = None
    imageTimeStampRangeStart: str | None = None
    imageTimeStampRangeEnd: str | None = None


class SampleSearchRequest(SearchRequestBase):
    sampleDbIds: list[str] | None = None
    sampleNames: list[str] | None = None
    sampleGroupDbIds: list[str] | None = None
    germplasmDbIds: list[str] | None = None
    germplasmNames: list[str] | None = None
    observationUnitDbIds: list[str] | None = None
    plateDbIds: list[str] | None = None
    studyDbIds: list[str] | None = None
    studyNames: list[str] | None = None
    trialDbIds: list[str] | None = None
    programDbIds: list[str] | None = None


class AttributeSearchRequest(SearchRequestBase):
    attributeDbIds: list[str] | None = None
    attributeNames: list[str] | None = None
    attributePUIs: list[str] | None = None
    attributeCategories: list[str] | None = None
    germplasmDbIds: list[str] | None = None
    methodDbIds: list[str] | None = None
    scaleDbIds: list[str] | None = None
    traitDbIds: list[str] | None = None
    ontologyDbIds: list[str] | None = None
    commonCropNames: list[str] | None = None
    studyDbIds: list[str] | None = None
    dataTypes: list[str] | None = None


class AttributeValueSearchRequest(SearchRequestBase):
    attributeValueDbIds: list[str] | None = None
    attributeDbIds: list[str] | None = None
    attributeNames: list[str] | None = None
    germplasmDbIds: list[str] | None = None
    germplasmNames: list[str] | None = None
    dataTypes: list[str] | None = None


class PedigreeSearchRequest(SearchRequestBase):
    germplasmDbIds: list[str] | None = None
    germplasmNames: list[str] | None = None
    germplasmPUIs: list[str] | None = None
    accessionNumbers: list[str] | None = None
    familyCodes: list[str] | None = None
    binomialNames: list[str] | None = None
    commonCropNames: list[str] | None = None
    programDbIds: list[str] | None = None
    trialDbIds: list[str] | None = None
    studyDbIds: list[str] | None = None
    includeFullTree: bool | None = None
    includeParents: bool | None = None
    includeSiblings: bool | None = None
    includeProgeny: bool | None = None
    pedigreeDepth: int | None = None
    progenyDepth: int | None = None


class ListSearchRequest(SearchRequestBase):
    listDbIds: list[str] | None = None
    listNames: list[str] | None = None
    listOwnerNames: list[str] | None = None
    listOwnerPersonDbIds: list[str] | None = None
    listSources: list[str] | None = None
    listType: str | None = None
    programDbIds: list[str] | None = None
    commonCropNames: list[str] | None = None
    dateCreatedRangeStart: str | None = None
    dateCreatedRangeEnd: str | None = None
    dateModifiedRangeStart: str | None = None
    dateModifiedRangeEnd: str | None = None


class PeopleSearchRequest(SearchRequestBase):
    personDbIds: list[str] | None = None
    firstNames: list[str] | None = None
    middleNames: list[str] | None = None
    lastNames: list[str] | None = None
    emailAddresses: list[str] | None = None
    mailingAddresses: list[str] | None = None
    userIDs: list[str] | None = None


# Genotyping Search Requests
class CallSearchRequest(SearchRequestBase):
    callSetDbIds: list[str] | None = None
    variantDbIds: list[str] | None = None
    variantSetDbIds: list[str] | None = None
    expandHomozygotes: bool | None = None
    sepPhased: str | None = None
    sepUnphased: str | None = None
    unknownString: str | None = None


class CallSetSearchRequest(SearchRequestBase):
    callSetDbIds: list[str] | None = None
    callSetNames: list[str] | None = None
    germplasmDbIds: list[str] | None = None
    germplasmNames: list[str] | None = None
    sampleDbIds: list[str] | None = None
    sampleNames: list[str] | None = None
    variantSetDbIds: list[str] | None = None


class VariantSearchRequest(SearchRequestBase):
    variantDbIds: list[str] | None = None
    variantSetDbIds: list[str] | None = None
    referenceDbIds: list[str] | None = None
    referenceSetDbIds: list[str] | None = None
    start: int | None = None
    end: int | None = None


class VariantSetSearchRequest(SearchRequestBase):
    variantSetDbIds: list[str] | None = None
    variantSetNames: list[str] | None = None
    studyDbIds: list[str] | None = None
    studyNames: list[str] | None = None
    callSetDbIds: list[str] | None = None


class PlateSearchRequest(SearchRequestBase):
    plateDbIds: list[str] | None = None
    plateNames: list[str] | None = None
    plateBarcodes: list[str] | None = None
    sampleDbIds: list[str] | None = None
    sampleNames: list[str] | None = None
    germplasmDbIds: list[str] | None = None
    observationUnitDbIds: list[str] | None = None
    studyDbIds: list[str] | None = None
    trialDbIds: list[str] | None = None
    programDbIds: list[str] | None = None
    commonCropNames: list[str] | None = None


class ReferenceSearchRequest(SearchRequestBase):
    referenceDbIds: list[str] | None = None
    referenceSetDbIds: list[str] | None = None
    accessions: list[str] | None = None
    md5checksums: list[str] | None = None
    isDerived: bool | None = None
    minLength: int | None = None
    maxLength: int | None = None


class ReferenceSetSearchRequest(SearchRequestBase):
    referenceSetDbIds: list[str] | None = None
    accessions: list[str] | None = None
    assemblyPUIs: list[str] | None = None
    md5checksums: list[str] | None = None


class MarkerPositionSearchRequest(SearchRequestBase):
    markerPositionDbIds: list[str] | None = None
    variantDbIds: list[str] | None = None
    mapDbIds: list[str] | None = None
    linkageGroupNames: list[str] | None = None
    minPosition: int | None = None
    maxPosition: int | None = None


class AlleleMatrixSearchRequest(SearchRequestBase):
    callSetDbIds: list[str] | None = None
    germplasmDbIds: list[str] | None = None
    germplasmNames: list[str] | None = None
    germplasmPUIs: list[str] | None = None
    sampleDbIds: list[str] | None = None
    variantDbIds: list[str] | None = None
    variantSetDbIds: list[str] | None = None
    positionRanges: list[dict] | None = None
    expandHomozygotes: bool | None = None
    sepPhased: str | None = None
    sepUnphased: str | None = None
    unknownString: str | None = None
    preview: bool | None = None
    dataMatrixAbbreviations: list[str] | None = None
    dataMatrixNames: list[str] | None = None


async def _create_search_result(search_type: str, request_data: dict, results: list[dict]) -> str:
    """
    Create a search result and return the searchResultsDbId.

    Uses Redis when available, falls back to in-memory storage.
    Results auto-expire after 30 minutes.
    """
    search_id = await job_service.cache_search_result(
        search_type=search_type,
        request_data=request_data,
        results=results
    )
    return search_id


async def _get_search_result(search_results_db_id: str) -> dict | None:
    """
    Retrieve search results by ID.

    Returns None if not found or expired (30 min TTL).
    """
    cached = await job_service.get_search_result(search_results_db_id)
    if not cached:
        return None

    # Convert to expected format for backward compatibility
    return {
        "searchType": cached.get("search_type"),
        "request": cached.get("request"),
        "results": cached.get("results", []),
        "createdAt": cached.get("created_at"),
        "totalCount": cached.get("total_count", 0)
    }


def _brapi_response(data: Any, page: int = 0, page_size: int = 1000, total: int = 0):
    """Standard BrAPI response wrapper"""
    return {
        "metadata": {
            "datafiles": [],
            "pagination": {
                "currentPage": page,
                "pageSize": page_size,
                "totalCount": total,
                "totalPages": max(1, (total + page_size - 1) // page_size)
            },
            "status": [{"message": "Request successful", "messageType": "INFO"}]
        },
        "result": data
    }


def _search_response(search_results_db_id: str):
    """Response for POST search - returns searchResultsDbId"""
    return {
        "metadata": {
            "datafiles": [],
            "pagination": {"currentPage": 0, "pageSize": 0, "totalCount": 0, "totalPages": 0},
            "status": [{"message": "Search submitted successfully", "messageType": "INFO"}]
        },
        "result": {
            "searchResultsDbId": search_results_db_id
        }
    }


# ============ CORE MODULE SEARCH ENDPOINTS ============

@router.post("/search/programs")
async def search_programs(
    request: ProgramSearchRequest,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_optional_user),
):
    """Submit a search request for Programs"""
    # Query database
    query = select(Program)

    # Apply filters
    if request.programDbIds:
        query = query.where(Program.program_db_id.in_(request.programDbIds))
    if request.programNames:
        # Case-insensitive partial match
        for name in request.programNames:
            query = query.where(Program.program_name.ilike(f"%{name}%"))
    if request.abbreviations:
        query = query.where(Program.abbreviation.in_(request.abbreviations))

    result = await db.execute(query)
    programs = result.scalars().all()

    # Convert to BrAPI format
    results = [
        {
            "programDbId": p.program_db_id or str(p.id),
            "programName": p.program_name,
            "abbreviation": p.abbreviation,
            "objective": p.objective,
            "additionalInfo": p.additional_info or {},
            "externalReferences": p.external_references or []
        }
        for p in programs
    ]

    search_id = await _create_search_result("programs", request.model_dump(), results)
    return _search_response(search_id)


@router.get("/search/programs/{searchResultsDbId}")
async def get_search_programs_results(
    searchResultsDbId: str,
    page: int = Query(0, ge=0),
    pageSize: int = Query(1000, ge=1, le=10000),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_optional_user),
):
    """Get the results of a Programs search request"""
    result = await _get_search_result(searchResultsDbId)
    if not result:
        raise HTTPException(status_code=404, detail="Search results not found")

    data = result["results"]
    total = len(data)
    start = page * pageSize
    paginated = data[start:start + pageSize]

    return _brapi_response({"data": paginated}, page, pageSize, total)


@router.post("/search/studies")
async def search_studies(
    request: StudySearchRequest,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_optional_user),
):
    """Submit a search request for Studies"""
    # Query database
    query = select(Study)

    # Apply filters
    if request.studyDbIds:
        query = query.where(Study.study_db_id.in_(request.studyDbIds))
    if request.studyNames:
        for name in request.studyNames:
            query = query.where(Study.study_name.ilike(f"%{name}%"))
    if request.studyTypes:
        query = query.where(Study.study_type.in_(request.studyTypes))
    if request.trialDbIds:
        query = query.join(Trial).where(Trial.trial_db_id.in_(request.trialDbIds))
    if request.active is not None:
        query = query.where(Study.active == request.active)

    result = await db.execute(query)
    studies = result.scalars().all()

    # Convert to BrAPI format
    results = [
        {
            "studyDbId": s.study_db_id or str(s.id),
            "studyName": s.study_name,
            "studyType": s.study_type,
            "studyCode": s.study_code,
            "studyDescription": s.study_description,
            "commonCropName": s.common_crop_name,
            "active": s.active,
            "startDate": s.start_date,
            "endDate": s.end_date,
            "additionalInfo": s.additional_info or {},
            "externalReferences": s.external_references or []
        }
        for s in studies
    ]

    search_id = await _create_search_result("studies", request.model_dump(), results)
    return _search_response(search_id)


@router.get("/search/studies/{searchResultsDbId}")
async def get_search_studies_results(
    searchResultsDbId: str,
    page: int = Query(0, ge=0),
    pageSize: int = Query(1000, ge=1, le=10000),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_optional_user),
):
    """Get the results of a Studies search request"""
    result = await _get_search_result(searchResultsDbId)
    if not result:
        raise HTTPException(status_code=404, detail="Search results not found")

    data = result["results"]
    total = len(data)
    start = page * pageSize
    paginated = data[start:start + pageSize]

    return _brapi_response({"data": paginated}, page, pageSize, total)


@router.post("/search/trials")
async def search_trials(
    request: TrialSearchRequest,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_optional_user),
):
    """Submit a search request for Trials"""
    # Query database
    query = select(Trial)

    # Apply filters
    if request.trialDbIds:
        query = query.where(Trial.trial_db_id.in_(request.trialDbIds))
    if request.trialNames:
        for name in request.trialNames:
            query = query.where(Trial.trial_name.ilike(f"%{name}%"))
    if request.commonCropNames:
        query = query.where(Trial.common_crop_name.in_(request.commonCropNames))
    if request.programDbIds:
        query = query.join(Program).where(Program.program_db_id.in_(request.programDbIds))
    if request.active is not None:
        query = query.where(Trial.active == request.active)

    result = await db.execute(query)
    trials = result.scalars().all()

    # Convert to BrAPI format
    results = [
        {
            "trialDbId": t.trial_db_id or str(t.id),
            "trialName": t.trial_name,
            "trialDescription": t.trial_description,
            "trialType": t.trial_type,
            "commonCropName": t.common_crop_name,
            "active": t.active,
            "startDate": t.start_date,
            "endDate": t.end_date,
            "additionalInfo": t.additional_info or {},
            "externalReferences": t.external_references or []
        }
        for t in trials
    ]

    search_id = await _create_search_result("trials", request.model_dump(), results)
    return _search_response(search_id)


@router.get("/search/trials/{searchResultsDbId}")
async def get_search_trials_results(
    searchResultsDbId: str,
    page: int = Query(0, ge=0),
    pageSize: int = Query(1000, ge=1, le=10000),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_optional_user),
):
    """Get the results of a Trials search request"""
    result = await _get_search_result(searchResultsDbId)
    if not result:
        raise HTTPException(status_code=404, detail="Search results not found")

    data = result["results"]
    total = len(data)
    start = page * pageSize
    paginated = data[start:start + pageSize]

    return _brapi_response({"data": paginated}, page, pageSize, total)


@router.post("/search/locations")
async def search_locations(
    request: LocationSearchRequest,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_optional_user),
):
    """Submit a search request for Locations"""
    # Query database
    query = select(Location)

    # Apply filters
    if request.locationDbIds:
        query = query.where(Location.location_db_id.in_(request.locationDbIds))
    if request.locationNames:
        for name in request.locationNames:
            query = query.where(Location.location_name.ilike(f"%{name}%"))
    if request.locationTypes:
        query = query.where(Location.location_type.in_(request.locationTypes))
    if request.countryCodes:
        query = query.where(Location.country_code.in_(request.countryCodes))
    if request.countryNames:
        query = query.where(Location.country_name.in_(request.countryNames))

    result = await db.execute(query)
    locations = result.scalars().all()

    # Convert to BrAPI format
    results = [
        {
            "locationDbId": loc.location_db_id or str(loc.id),
            "locationName": loc.location_name,
            "locationType": loc.location_type,
            "abbreviation": loc.abbreviation,
            "countryCode": loc.country_code,
            "countryName": loc.country_name,
            "instituteName": loc.institute_name,
            "instituteAddress": loc.institute_address,
            "additionalInfo": loc.additional_info or {},
            "externalReferences": loc.external_references or []
        }
        for loc in locations
    ]

    search_id = await _create_search_result("locations", request.model_dump(), results)
    return _search_response(search_id)


@router.get("/search/locations/{searchResultsDbId}")
async def get_search_locations_results(
    searchResultsDbId: str,
    page: int = Query(0, ge=0),
    pageSize: int = Query(1000, ge=1, le=10000),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_optional_user),
):
    """Get the results of a Locations search request"""
    result = await _get_search_result(searchResultsDbId)
    if not result:
        raise HTTPException(status_code=404, detail="Search results not found")

    data = result["results"]
    total = len(data)
    start = page * pageSize
    paginated = data[start:start + pageSize]

    return _brapi_response({"data": paginated}, page, pageSize, total)


@router.post("/search/lists")
async def search_lists(
    request: ListSearchRequest,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_optional_user),
):
    """Submit a search request for Lists"""
    # Query database
    query = select(ListModel)

    # Apply filters
    if request.listDbIds:
        query = query.where(ListModel.list_db_id.in_(request.listDbIds))
    if request.listNames:
        for name in request.listNames:
            query = query.where(ListModel.list_name.ilike(f"%{name}%"))
    if request.listType:
        query = query.where(ListModel.list_type == request.listType)
    if request.listOwnerNames:
        query = query.where(ListModel.list_owner_name.in_(request.listOwnerNames))

    result = await db.execute(query)
    lists = result.scalars().all()

    # Convert to BrAPI format
    results = [
        {
            "listDbId": lst.list_db_id or str(lst.id),
            "listName": lst.list_name,
            "listDescription": lst.list_description,
            "listType": lst.list_type,
            "listSize": lst.list_size or 0,
            "listSource": lst.list_source,
            "listOwnerName": lst.list_owner_name,
            "listOwnerPersonDbId": lst.list_owner_person_db_id,
            "dateCreated": lst.date_created,
            "dateModified": lst.date_modified,
            "data": lst.data or [],
            "additionalInfo": lst.additional_info or {},
            "externalReferences": lst.external_references or []
        }
        for lst in lists
    ]

    search_id = await _create_search_result("lists", request.model_dump(), results)
    return _search_response(search_id)


@router.get("/search/lists/{searchResultsDbId}")
async def get_search_lists_results(
    searchResultsDbId: str,
    page: int = Query(0, ge=0),
    pageSize: int = Query(1000, ge=1, le=10000),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_optional_user),
):
    """Get the results of a Lists search request"""
    result = await _get_search_result(searchResultsDbId)
    if not result:
        raise HTTPException(status_code=404, detail="Search results not found")

    data = result["results"]
    total = len(data)
    start = page * pageSize
    paginated = data[start:start + pageSize]

    return _brapi_response({"data": paginated}, page, pageSize, total)


@router.post("/search/people")
async def search_people(
    request: PeopleSearchRequest,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_optional_user),
):
    """Submit a search request for People"""
    # Build query
    query = select(PersonModel)

    # Apply filters
    if request.personDbIds:
        query = query.where(PersonModel.person_db_id.in_(request.personDbIds))
    if request.firstNames:
        conditions = [PersonModel.first_name.ilike(f"%{name}%") for name in request.firstNames]
        query = query.where(func.or_(*conditions))
    if request.lastNames:
        conditions = [PersonModel.last_name.ilike(f"%{name}%") for name in request.lastNames]
        query = query.where(func.or_(*conditions))
    if request.emailAddresses:
        query = query.where(PersonModel.email_address.in_(request.emailAddresses))

    # Execute query
    result = await db.execute(query)
    people = result.scalars().all()

    # Convert to BrAPI format
    results = [
        {
            "personDbId": p.person_db_id,
            "firstName": p.first_name,
            "lastName": p.last_name,
            "emailAddress": p.email_address,
        }
        for p in people
    ]

    search_id = await _create_search_result("people", request.model_dump(), results)
    return _search_response(search_id)


@router.get("/search/people/{searchResultsDbId}")
async def get_search_people_results(
    searchResultsDbId: str,
    page: int = Query(0, ge=0),
    pageSize: int = Query(1000, ge=1, le=10000),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_optional_user),
):
    """Get the results of a People search request"""
    result = await _get_search_result(searchResultsDbId)
    if not result:
        raise HTTPException(status_code=404, detail="Search results not found")

    data = result["results"]
    total = len(data)
    start = page * pageSize
    paginated = data[start:start + pageSize]

    return _brapi_response({"data": paginated}, page, pageSize, total)


# ============ GERMPLASM MODULE SEARCH ENDPOINTS ============

@router.post("/search/germplasm")
async def search_germplasm(
    request: GermplasmSearchRequest,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_optional_user),
):
    """Submit a search request for Germplasm"""
    # Query database
    query = select(Germplasm)

    # Apply filters
    if request.germplasmDbIds:
        query = query.where(Germplasm.germplasm_db_id.in_(request.germplasmDbIds))
    if request.germplasmNames:
        for name in request.germplasmNames:
            query = query.where(Germplasm.germplasm_name.ilike(f"%{name}%"))
    if request.commonCropNames:
        query = query.where(Germplasm.common_crop_name.in_(request.commonCropNames))
    if request.species:
        query = query.where(Germplasm.species.in_(request.species))
    if request.genus:
        query = query.where(Germplasm.genus.in_(request.genus))
    if request.accessionNumbers:
        query = query.where(Germplasm.accession_number.in_(request.accessionNumbers))

    result = await db.execute(query)
    germplasm_list = result.scalars().all()

    # Convert to BrAPI format
    results = [
        {
            "germplasmDbId": g.germplasm_db_id or str(g.id),
            "germplasmName": g.germplasm_name,
            "germplasmPUI": g.germplasm_pui,
            "accessionNumber": g.accession_number,
            "commonCropName": g.common_crop_name,
            "genus": g.genus,
            "species": g.species,
            "subtaxa": g.subtaxa,
            "biologicalStatusOfAccessionCode": g.biological_status_of_accession_code,
            "countryOfOriginCode": g.country_of_origin_code,
            "defaultDisplayName": g.default_display_name or g.germplasm_name,
            "pedigree": g.pedigree,
            "seedSource": g.seed_source,
            "instituteCode": g.institute_code,
            "instituteName": g.institute_name,
            "additionalInfo": g.additional_info or {},
            "externalReferences": g.external_references or []
        }
        for g in germplasm_list
    ]

    search_id = await _create_search_result("germplasm", request.model_dump(), results)
    return _search_response(search_id)


@router.get("/search/germplasm/{searchResultsDbId}")
async def get_search_germplasm_results(
    searchResultsDbId: str,
    page: int = Query(0, ge=0),
    pageSize: int = Query(1000, ge=1, le=10000),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_optional_user),
):
    """Get the results of a Germplasm search request"""
    result = await _get_search_result(searchResultsDbId)
    if not result:
        raise HTTPException(status_code=404, detail="Search results not found")

    data = result["results"]
    total = len(data)
    start = page * pageSize
    paginated = data[start:start + pageSize]

    return _brapi_response({"data": paginated}, page, pageSize, total)


@router.post("/search/attributes")
async def search_attributes(
    request: AttributeSearchRequest,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_optional_user),
):
    """Submit a search request for Germplasm Attributes"""
    # Build query from database
    query = select(GermplasmAttribute)

    # Apply filters
    if request.attributeDbIds:
        query = query.where(GermplasmAttribute.attribute_db_id.in_(request.attributeDbIds))
    if request.attributeNames:
        name_filters = [GermplasmAttribute.attribute_name.ilike(f"%{name}%") for name in request.attributeNames]
        query = query.where(func.or_(*name_filters))
    if request.attributeCategories:
        query = query.where(GermplasmAttribute.attribute_category.in_(request.attributeCategories))
    if request.germplasmDbIds:
        query = query.join(Germplasm).where(Germplasm.germplasm_db_id.in_(request.germplasmDbIds))

    # Execute query and convert to BrAPI format
    result = await db.execute(query)
    attributes = result.scalars().all()

    results = []
    for attr in attributes:
        results.append({
            "attributeDbId": attr.attribute_db_id or str(attr.id),
            "attributeName": attr.attribute_name,
            "attributeCategory": attr.attribute_category,
            "attributeDescription": attr.attribute_description,
            "additionalInfo": attr.additional_info or {},
            "externalReferences": attr.external_references or []
        })

    search_id = await _create_search_result("attributes", request.model_dump(), results)
    return _search_response(search_id)


@router.get("/search/attributes/{searchResultsDbId}")
async def get_search_attributes_results(
    searchResultsDbId: str,
    page: int = Query(0, ge=0),
    pageSize: int = Query(1000, ge=1, le=10000),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_optional_user),
):
    """Get the results of an Attributes search request"""
    result = await _get_search_result(searchResultsDbId)
    if not result:
        raise HTTPException(status_code=404, detail="Search results not found")

    data = result["results"]
    total = len(data)
    start = page * pageSize
    paginated = data[start:start + pageSize]

    return _brapi_response({"data": paginated}, page, pageSize, total)


@router.post("/search/attributevalues")
async def search_attributevalues(
    request: AttributeValueSearchRequest,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_optional_user),
):
    """Submit a search request for Germplasm Attribute Values"""
    # Build query from database - attribute values are stored in GermplasmAttribute
    query = select(GermplasmAttribute).join(Germplasm)

    # Apply filters
    if request.attributeValueDbIds:
        # attributeValueDbId maps to the attribute record id
        query = query.where(GermplasmAttribute.attribute_db_id.in_(request.attributeValueDbIds))
    if request.attributeDbIds:
        query = query.where(GermplasmAttribute.attribute_db_id.in_(request.attributeDbIds))
    if request.attributeNames:
        name_filters = [GermplasmAttribute.attribute_name.ilike(f"%{name}%") for name in request.attributeNames]
        query = query.where(func.or_(*name_filters))
    if request.germplasmDbIds:
        query = query.where(Germplasm.germplasm_db_id.in_(request.germplasmDbIds))
    if request.germplasmNames:
        name_filters = [Germplasm.germplasm_name.ilike(f"%{name}%") for name in request.germplasmNames]
        query = query.where(func.or_(*name_filters))

    # Execute query and convert to BrAPI format
    result = await db.execute(query)
    attr_values = result.scalars().all()

    results = []
    for av in attr_values:
        results.append({
            "attributeValueDbId": f"attrval_{av.id}",
            "attributeDbId": av.attribute_db_id or str(av.id),
            "attributeName": av.attribute_name,
            "germplasmDbId": av.germplasm.germplasm_db_id if av.germplasm else None,
            "germplasmName": av.germplasm.germplasm_name if av.germplasm else None,
            "value": av.value,
            "determinationDate": av.determination_date.isoformat() if av.determination_date else None,
            "additionalInfo": av.additional_info or {},
            "externalReferences": av.external_references or []
        })

    search_id = await _create_search_result("attributevalues", request.model_dump(), results)
    return _search_response(search_id)


@router.get("/search/attributevalues/{searchResultsDbId}")
async def get_search_attributevalues_results(
    searchResultsDbId: str,
    page: int = Query(0, ge=0),
    pageSize: int = Query(1000, ge=1, le=10000),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_optional_user),
):
    """Get the results of an Attribute Values search request"""
    result = await _get_search_result(searchResultsDbId)
    if not result:
        raise HTTPException(status_code=404, detail="Search results not found")

    data = result["results"]
    total = len(data)
    start = page * pageSize
    paginated = data[start:start + pageSize]

    return _brapi_response({"data": paginated}, page, pageSize, total)


@router.post("/search/pedigree")
async def search_pedigree(
    request: PedigreeSearchRequest,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_optional_user),
):
    """Submit a search request for Pedigree"""
    # Build query from database - pedigree is stored in Germplasm table
    query = select(Germplasm).where(Germplasm.pedigree.isnot(None))

    # Apply filters
    if request.germplasmDbIds:
        query = query.where(Germplasm.germplasm_db_id.in_(request.germplasmDbIds))
    if request.germplasmNames:
        # Use ilike for case-insensitive partial matching
        name_filters = [Germplasm.germplasm_name.ilike(f"%{name}%") for name in request.germplasmNames]
        query = query.where(func.or_(*name_filters))
    if request.commonCropNames:
        query = query.where(Germplasm.common_crop_name.in_(request.commonCropNames))
    if request.includeParents:
        # Filter to only include germplasm that have parent information
        query = query.where(Germplasm.pedigree.contains('/'))

    # Execute query and convert to BrAPI format
    result = await db.execute(query)
    germplasm_list = result.scalars().all()

    results = []
    for germ in germplasm_list:
        # Parse pedigree string to extract parent information
        parents = []
        if germ.pedigree and '/' in germ.pedigree:
            # Simple pedigree parsing - in production, use more sophisticated parser
            parent_parts = germ.pedigree.split('/')
            if len(parent_parts) >= 2:
                parents = [
                    {"germplasmDbId": f"parent_{parent_parts[0]}", "germplasmName": parent_parts[0], "parentType": "FEMALE"},
                    {"germplasmDbId": f"parent_{parent_parts[1]}", "germplasmName": parent_parts[1], "parentType": "MALE"}
                ]

        results.append({
            "germplasmDbId": germ.germplasm_db_id,
            "germplasmName": germ.germplasm_name,
            "pedigree": germ.pedigree,
            "crossingPlan": None,
            "crossingYear": None,
            "familyCode": None,
            "parents": parents,
            "siblings": [],  # Would need additional query to find siblings
            "progeny": [],   # Would need additional query to find progeny
            "additionalInfo": germ.additional_info or {},
            "externalReferences": germ.external_references or []
        })

    search_id = await _create_search_result("pedigree", request.model_dump(), results)
    return _search_response(search_id)


@router.get("/search/pedigree/{searchResultsDbId}")
async def get_search_pedigree_results(
    searchResultsDbId: str,
    page: int = Query(0, ge=0),
    pageSize: int = Query(1000, ge=1, le=10000),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_optional_user),
):
    """Get the results of a Pedigree search request"""
    result = await _get_search_result(searchResultsDbId)
    if not result:
        raise HTTPException(status_code=404, detail="Search results not found")

    data = result["results"]
    total = len(data)
    start = page * pageSize
    paginated = data[start:start + pageSize]

    return _brapi_response({"data": paginated}, page, pageSize, total)


# ============ PHENOTYPING MODULE SEARCH ENDPOINTS ============

@router.post("/search/observations")
async def search_observations(
    request: ObservationSearchRequest,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_optional_user),
):
    """Submit a search request for Observations"""
    # Build query from database
    query = select(Observation)

    # Apply filters
    if request.observationDbIds:
        query = query.where(Observation.observation_db_id.in_(request.observationDbIds))
    if request.observationUnitDbIds:
        query = query.where(Observation.observation_unit_db_id.in_(request.observationUnitDbIds))
    if request.observationVariableDbIds:
        query = query.where(Observation.observation_variable_db_id.in_(request.observationVariableDbIds))
    if request.studyDbIds:
        query = query.where(Observation.study_db_id.in_(request.studyDbIds))
    if request.seasonDbIds:
        query = query.where(Observation.season_db_id.in_(request.seasonDbIds))

    # Execute query and convert to BrAPI format
    result = await db.execute(query)
    observations = result.scalars().all()

    results = []
    for obs in observations:
        results.append({
            "observationDbId": obs.observation_db_id,
            "observationUnitDbId": obs.observation_unit_db_id,
            "observationVariableDbId": obs.observation_variable_db_id,
            "studyDbId": obs.study_db_id,
            "value": obs.value,
            "collector": obs.collector,
            "observationTimeStamp": obs.observation_time_stamp.isoformat() if obs.observation_time_stamp else None,
            "season": {"seasonDbId": obs.season_db_id} if obs.season_db_id else None,
            "additionalInfo": obs.additional_info or {},
            "externalReferences": obs.external_references or []
        })

    search_id = await _create_search_result("observations", request.model_dump(), results)
    return _search_response(search_id)


@router.get("/search/observations/{searchResultsDbId}")
async def get_search_observations_results(
    searchResultsDbId: str,
    page: int = Query(0, ge=0),
    pageSize: int = Query(1000, ge=1, le=10000),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_optional_user),
):
    """Get the results of an Observations search request"""
    result = await _get_search_result(searchResultsDbId)
    if not result:
        raise HTTPException(status_code=404, detail="Search results not found")

    data = result["results"]
    total = len(data)
    start = page * pageSize
    paginated = data[start:start + pageSize]

    return _brapi_response({"data": paginated}, page, pageSize, total)


@router.post("/search/observationunits")
async def search_observationunits(
    request: ObservationUnitSearchRequest,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_optional_user),
):
    """Submit a search request for Observation Units"""
    # Build query from database
    query = select(ObservationUnit)

    # Apply filters
    if request.observationUnitDbIds:
        query = query.where(ObservationUnit.observation_unit_db_id.in_(request.observationUnitDbIds))
    if request.germplasmDbIds:
        query = query.where(ObservationUnit.germplasm_db_id.in_(request.germplasmDbIds))
    if request.studyDbIds:
        query = query.where(ObservationUnit.study_db_id.in_(request.studyDbIds))
    if request.locationDbIds:
        query = query.where(ObservationUnit.location_db_id.in_(request.locationDbIds))
    if request.trialDbIds:
        query = query.where(ObservationUnit.trial_db_id.in_(request.trialDbIds))
    if request.programDbIds:
        query = query.where(ObservationUnit.program_db_id.in_(request.programDbIds))

    # Execute query and convert to BrAPI format
    result = await db.execute(query)
    observation_units = result.scalars().all()

    results = []
    for ou in observation_units:
        results.append({
            "observationUnitDbId": ou.observation_unit_db_id,
            "observationUnitName": ou.observation_unit_name,
            "observationUnitPUI": ou.observation_unit_pui,
            "germplasmDbId": ou.germplasm_db_id,
            "germplasmName": ou.germplasm_name,
            "studyDbId": ou.study_db_id,
            "studyName": ou.study_name,
            "locationDbId": ou.location_db_id,
            "locationName": ou.location_name,
            "trialDbId": ou.trial_db_id,
            "trialName": ou.trial_name,
            "programDbId": ou.program_db_id,
            "programName": ou.program_name,
            "observationUnitPosition": ou.observation_unit_position or {},
            "treatments": ou.treatments or [],
            "additionalInfo": ou.additional_info or {},
            "externalReferences": ou.external_references or []
        })

    search_id = await _create_search_result("observationunits", request.model_dump(), results)
    return _search_response(search_id)


@router.get("/search/observationunits/{searchResultsDbId}")
async def get_search_observationunits_results(
    searchResultsDbId: str,
    page: int = Query(0, ge=0),
    pageSize: int = Query(1000, ge=1, le=10000),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_optional_user),
):
    """Get the results of an Observation Units search request"""
    result = await _get_search_result(searchResultsDbId)
    if not result:
        raise HTTPException(status_code=404, detail="Search results not found")

    data = result["results"]
    total = len(data)
    start = page * pageSize
    paginated = data[start:start + pageSize]

    return _brapi_response({"data": paginated}, page, pageSize, total)


@router.post("/search/variables")
async def search_variables(
    request: VariableSearchRequest,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_optional_user),
):
    """Submit a search request for Observation Variables"""
    # Build query from database
    query = select(ObservationVariable)

    # Apply filters
    if request.observationVariableDbIds:
        query = query.where(ObservationVariable.observation_variable_db_id.in_(request.observationVariableDbIds))
    if request.observationVariableNames:
        # Use ilike for case-insensitive partial matching
        name_filters = [ObservationVariable.observation_variable_name.ilike(f"%{name}%") for name in request.observationVariableNames]
        query = query.where(func.or_(*name_filters))
    if request.traitDbIds:
        query = query.where(ObservationVariable.trait_db_id.in_(request.traitDbIds))
    if request.traitClasses:
        query = query.where(ObservationVariable.trait_class.in_(request.traitClasses))
    if request.methodDbIds:
        query = query.where(ObservationVariable.method_db_id.in_(request.methodDbIds))
    if request.scaleDbIds:
        query = query.where(ObservationVariable.scale_db_id.in_(request.scaleDbIds))
    if request.studyDbIds:
        query = query.where(ObservationVariable.study_db_id.in_(request.studyDbIds))

    # Execute query and convert to BrAPI format
    result = await db.execute(query)
    variables = result.scalars().all()

    results = []
    for var in variables:
        results.append({
            "observationVariableDbId": var.observation_variable_db_id,
            "observationVariableName": var.observation_variable_name,
            "commonCropName": var.common_crop_name,
            "defaultValue": var.default_value,
            "documentationURL": var.documentation_url,
            "growthStage": var.growth_stage,
            "institution": var.institution,
            "language": var.language,
            "scientist": var.scientist,
            "status": var.status,
            "submissionTimestamp": var.submission_timestamp,
            "synonyms": var.synonyms or [],
            "trait": {
                "traitDbId": var.trait_db_id,
                "traitName": var.trait_name,
                "traitDescription": var.trait_description,
                "traitClass": var.trait_class
            } if var.trait_db_id else None,
            "method": {
                "methodDbId": var.method_db_id,
                "methodName": var.method_name,
                "methodDescription": var.method_description,
                "methodClass": var.method_class,
                "formula": var.formula
            } if var.method_db_id else None,
            "scale": {
                "scaleDbId": var.scale_db_id,
                "scaleName": var.scale_name,
                "dataType": var.data_type,
                "decimalPlaces": var.decimal_places,
                "validValues": var.valid_values
            } if var.scale_db_id else None,
            "additionalInfo": var.additional_info or {},
            "externalReferences": var.external_references or []
        })

    search_id = await _create_search_result("variables", request.model_dump(), results)
    return _search_response(search_id)


@router.get("/search/variables/{searchResultsDbId}")
async def get_search_variables_results(
    searchResultsDbId: str,
    page: int = Query(0, ge=0),
    pageSize: int = Query(1000, ge=1, le=10000),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_optional_user),
):
    """Get the results of a Variables search request"""
    result = await _get_search_result(searchResultsDbId)
    if not result:
        raise HTTPException(status_code=404, detail="Search results not found")

    data = result["results"]
    total = len(data)
    start = page * pageSize
    paginated = data[start:start + pageSize]

    return _brapi_response({"data": paginated}, page, pageSize, total)


@router.post("/search/images")
async def search_images(
    request: ImageSearchRequest,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_optional_user),
):
    """Submit a search request for Images"""
    # Build query from database
    query = select(Image)

    # Apply filters
    if request.imageDbIds:
        query = query.where(Image.image_db_id.in_(request.imageDbIds))
    if request.imageNames:
        # Use ilike for case-insensitive partial matching
        name_filters = [Image.image_name.ilike(f"%{name}%") for name in request.imageNames]
        query = query.where(func.or_(*name_filters))
    if request.mimeTypes:
        query = query.where(Image.mime_type.in_(request.mimeTypes))
    if request.observationUnitDbIds:
        query = query.where(Image.observation_unit_db_id.in_(request.observationUnitDbIds))
    if request.observationDbIds:
        query = query.where(Image.observation_db_id.in_(request.observationDbIds))
    if request.descriptiveOntologyTerms:
        # Search in descriptive ontology terms JSON field
        for term in request.descriptiveOntologyTerms:
            query = query.where(Image.descriptive_ontology_terms.contains([term]))

    # Execute query and convert to BrAPI format
    result = await db.execute(query)
    images = result.scalars().all()

    results = []
    for img in images:
        results.append({
            "imageDbId": img.image_db_id,
            "imageName": img.image_name,
            "imageURL": img.image_url,
            "imageFileSize": img.image_file_size,
            "imageFileName": img.image_file_name,
            "imageHeight": img.image_height,
            "imageWidth": img.image_width,
            "mimeType": img.mime_type,
            "observationDbId": img.observation_db_id,
            "observationUnitDbId": img.observation_unit_db_id,
            "imageLocation": {
                "geometry": img.image_location_geometry,
                "type": img.image_location_type
            } if img.image_location_geometry else None,
            "imageTimeStamp": img.image_time_stamp.isoformat() if img.image_time_stamp else None,
            "descriptiveOntologyTerms": img.descriptive_ontology_terms or [],
            "additionalInfo": img.additional_info or {},
            "externalReferences": img.external_references or []
        })

    search_id = await _create_search_result("images", request.model_dump(), results)
    return _search_response(search_id)


@router.get("/search/images/{searchResultsDbId}")
async def get_search_images_results(
    searchResultsDbId: str,
    page: int = Query(0, ge=0),
    pageSize: int = Query(1000, ge=1, le=10000),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_optional_user),
):
    """Get the results of an Images search request"""
    result = await _get_search_result(searchResultsDbId)
    if not result:
        raise HTTPException(status_code=404, detail="Search results not found")

    data = result["results"]
    total = len(data)
    start = page * pageSize
    paginated = data[start:start + pageSize]

    return _brapi_response({"data": paginated}, page, pageSize, total)


@router.post("/search/samples")
async def search_samples(
    request: SampleSearchRequest,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_optional_user),
):
    """Submit a search request for Samples"""
    # Build query from database
    query = select(Sample)

    # Apply filters
    if request.sampleDbIds:
        query = query.where(Sample.sample_db_id.in_(request.sampleDbIds))
    if request.sampleNames:
        # Use ilike for case-insensitive partial matching
        name_filters = [Sample.sample_name.ilike(f"%{name}%") for name in request.sampleNames]
        query = query.where(func.or_(*name_filters))
    if request.germplasmDbIds:
        query = query.where(Sample.germplasm_db_id.in_(request.germplasmDbIds))
    if request.studyDbIds:
        query = query.where(Sample.study_db_id.in_(request.studyDbIds))
    if request.plateDbIds:
        query = query.where(Sample.plate_db_id.in_(request.plateDbIds))
    if request.observationUnitDbIds:
        query = query.where(Sample.observation_unit_db_id.in_(request.observationUnitDbIds))

    # Execute query and convert to BrAPI format
    result = await db.execute(query)
    samples = result.scalars().all()

    results = []
    for sample in samples:
        results.append({
            "sampleDbId": sample.sample_db_id,
            "sampleName": sample.sample_name,
            "sampleBarcode": sample.sample_barcode,
            "sampleDescription": sample.sample_description,
            "sampleGroupDbId": sample.sample_group_db_id,
            "samplePUI": sample.sample_pui,
            "sampleTimestamp": sample.sample_timestamp.isoformat() if sample.sample_timestamp else None,
            "sampleType": sample.sample_type,
            "tissueType": sample.tissue_type,
            "germplasmDbId": sample.germplasm_db_id,
            "studyDbId": sample.study_db_id,
            "plateDbId": sample.plate_db_id,
            "plateName": sample.plate_name,
            "observationUnitDbId": sample.observation_unit_db_id,
            "well": sample.well,
            "row": sample.row,
            "column": sample.column,
            "takenBy": sample.taken_by,
            "sampleLocation": {
                "geometry": sample.sample_location_geometry,
                "type": sample.sample_location_type
            } if sample.sample_location_geometry else None,
            "additionalInfo": sample.additional_info or {},
            "externalReferences": sample.external_references or []
        })

    search_id = await _create_search_result("samples", request.model_dump(), results)
    return _search_response(search_id)


@router.get("/search/samples/{searchResultsDbId}")
async def get_search_samples_results(
    searchResultsDbId: str,
    page: int = Query(0, ge=0),
    pageSize: int = Query(1000, ge=1, le=10000),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_optional_user),
):
    """Get the results of a Samples search request"""
    result = await _get_search_result(searchResultsDbId)
    if not result:
        raise HTTPException(status_code=404, detail="Search results not found")

    data = result["results"]
    total = len(data)
    start = page * pageSize
    paginated = data[start:start + pageSize]

    return _brapi_response({"data": paginated}, page, pageSize, total)


# ============ GENOTYPING MODULE SEARCH ENDPOINTS ============

@router.post("/search/calls")
async def search_calls(
    request: CallSearchRequest,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_optional_user),
):
    """Submit a search request for Genotype Calls"""
    # Build query from database
    query = select(Call).join(CallSet).join(Variant)

    # Apply filters
    if request.callSetDbIds:
        query = query.where(CallSet.call_set_db_id.in_(request.callSetDbIds))
    if request.variantDbIds:
        query = query.where(Variant.variant_db_id.in_(request.variantDbIds))
    if request.variantSetDbIds:
        query = query.join(VariantSet, Variant.variant_set_id == VariantSet.id).where(
            VariantSet.variant_set_db_id.in_(request.variantSetDbIds)
        )

    # Execute query and convert to BrAPI format
    result = await db.execute(query)
    calls = result.scalars().all()

    results = []
    for call in calls:
        results.append({
            "callDbId": call.call_db_id or str(call.id),
            "callSetDbId": call.call_set.call_set_db_id if call.call_set else None,
            "callSetName": call.call_set.call_set_name if call.call_set else None,
            "variantDbId": call.variant.variant_db_id if call.variant else None,
            "variantName": call.variant.variant_name if call.variant else None,
            "genotype": call.genotype or {},
            "genotypeValue": call.genotype_value,
            "genotypeLikelihood": call.genotype_likelihood,
            "phaseSet": call.phaseSet,
            "additionalInfo": call.additional_info or {},
            "externalReferences": call.external_references or []
        })

    search_id = await _create_search_result("calls", request.model_dump(), results)
    return _search_response(search_id)


@router.get("/search/calls/{searchResultsDbId}")
async def get_search_calls_results(
    searchResultsDbId: str,
    page: int = Query(0, ge=0),
    pageSize: int = Query(1000, ge=1, le=10000),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_optional_user),
):
    """Get the results of a Calls search request"""
    result = await _get_search_result(searchResultsDbId)
    if not result:
        raise HTTPException(status_code=404, detail="Search results not found")

    data = result["results"]
    total = len(data)
    start = page * pageSize
    paginated = data[start:start + pageSize]

    return _brapi_response({"data": paginated}, page, pageSize, total)


@router.post("/search/callsets")
async def search_callsets(
    request: CallSetSearchRequest,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_optional_user),
):
    """Submit a search request for Call Sets"""
    # Build query from database
    query = select(CallSet)

    # Apply filters
    if request.callSetDbIds:
        query = query.where(CallSet.call_set_db_id.in_(request.callSetDbIds))
    if request.callSetNames:
        name_filters = [CallSet.call_set_name.ilike(f"%{name}%") for name in request.callSetNames]
        query = query.where(func.or_(*name_filters))
    if request.sampleDbIds:
        query = query.where(CallSet.sample_db_id.in_(request.sampleDbIds))
    if request.variantSetDbIds:
        # Join through the many-to-many relationship
        query = query.join(CallSet.variant_sets).where(
            VariantSet.variant_set_db_id.in_(request.variantSetDbIds)
        )

    # Execute query and convert to BrAPI format
    result = await db.execute(query)
    call_sets = result.scalars().all()

    results = []
    for cs in call_sets:
        results.append({
            "callSetDbId": cs.call_set_db_id or str(cs.id),
            "callSetName": cs.call_set_name,
            "sampleDbId": cs.sample_db_id,
            "created": cs.created,
            "updated": cs.updated,
            "additionalInfo": cs.additional_info or {},
            "externalReferences": cs.external_references or []
        })

    search_id = await _create_search_result("callsets", request.model_dump(), results)
    return _search_response(search_id)


@router.get("/search/callsets/{searchResultsDbId}")
async def get_search_callsets_results(
    searchResultsDbId: str,
    page: int = Query(0, ge=0),
    pageSize: int = Query(1000, ge=1, le=10000),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_optional_user),
):
    """Get the results of a Call Sets search request"""
    result = await _get_search_result(searchResultsDbId)
    if not result:
        raise HTTPException(status_code=404, detail="Search results not found")

    data = result["results"]
    total = len(data)
    start = page * pageSize
    paginated = data[start:start + pageSize]

    return _brapi_response({"data": paginated}, page, pageSize, total)


@router.post("/search/variants")
async def search_variants(
    request: VariantSearchRequest,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_optional_user),
):
    """Submit a search request for Variants"""
    # Build query from database
    query = select(Variant)

    # Apply filters
    if request.variantDbIds:
        query = query.where(Variant.variant_db_id.in_(request.variantDbIds))
    if request.variantSetDbIds:
        query = query.join(VariantSet).where(VariantSet.variant_set_db_id.in_(request.variantSetDbIds))
    if request.referenceDbIds:
        query = query.join(Reference).where(Reference.reference_db_id.in_(request.referenceDbIds))
    if request.referenceSetDbIds:
        query = query.join(Reference).join(ReferenceSet).where(
            ReferenceSet.reference_set_db_id.in_(request.referenceSetDbIds)
        )
    if request.start is not None:
        query = query.where(Variant.start >= request.start)
    if request.end is not None:
        query = query.where(Variant.end <= request.end)

    # Execute query and convert to BrAPI format
    result = await db.execute(query)
    variants = result.scalars().all()

    results = []
    for var in variants:
        results.append({
            "variantDbId": var.variant_db_id or str(var.id),
            "variantName": var.variant_name,
            "variantType": var.variant_type,
            "referenceBases": var.reference_bases,
            "alternateBases": var.alternate_bases or [],
            "start": var.start,
            "end": var.end,
            "cipos": var.cipos,
            "ciend": var.ciend,
            "svlen": var.svlen,
            "filtersApplied": var.filters_applied,
            "filtersPassed": var.filters_passed,
            "additionalInfo": var.additional_info or {},
            "externalReferences": var.external_references or []
        })

    search_id = await _create_search_result("variants", request.model_dump(), results)
    return _search_response(search_id)


@router.get("/search/variants/{searchResultsDbId}")
async def get_search_variants_results(
    searchResultsDbId: str,
    page: int = Query(0, ge=0),
    pageSize: int = Query(1000, ge=1, le=10000),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_optional_user),
):
    """Get the results of a Variants search request"""
    result = await _get_search_result(searchResultsDbId)
    if not result:
        raise HTTPException(status_code=404, detail="Search results not found")

    data = result["results"]
    total = len(data)
    start = page * pageSize
    paginated = data[start:start + pageSize]

    return _brapi_response({"data": paginated}, page, pageSize, total)


@router.post("/search/variantsets")
async def search_variantsets(
    request: VariantSetSearchRequest,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_optional_user),
):
    """Submit a search request for Variant Sets"""
    # Build query from database
    query = select(VariantSet)

    # Apply filters
    if request.variantSetDbIds:
        query = query.where(VariantSet.variant_set_db_id.in_(request.variantSetDbIds))
    if request.variantSetNames:
        name_filters = [VariantSet.variant_set_name.ilike(f"%{name}%") for name in request.variantSetNames]
        query = query.where(func.or_(*name_filters))
    if request.studyDbIds:
        from app.models.core import Study
        query = query.join(Study).where(Study.study_db_id.in_(request.studyDbIds))
    if request.callSetDbIds:
        query = query.join(VariantSet.call_sets).where(
            CallSet.call_set_db_id.in_(request.callSetDbIds)
        )

    # Execute query and convert to BrAPI format
    result = await db.execute(query)
    variant_sets = result.scalars().all()

    results = []
    for vs in variant_sets:
        results.append({
            "variantSetDbId": vs.variant_set_db_id or str(vs.id),
            "variantSetName": vs.variant_set_name,
            "analysis": vs.analysis or [],
            "availableFormats": vs.available_formats or [],
            "callSetCount": vs.call_set_count,
            "variantCount": vs.variant_count,
            "additionalInfo": vs.additional_info or {},
            "externalReferences": vs.external_references or []
        })

    search_id = await _create_search_result("variantsets", request.model_dump(), results)
    return _search_response(search_id)


@router.get("/search/variantsets/{searchResultsDbId}")
async def get_search_variantsets_results(
    searchResultsDbId: str,
    page: int = Query(0, ge=0),
    pageSize: int = Query(1000, ge=1, le=10000),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_optional_user),
):
    """Get the results of a Variant Sets search request"""
    result = await _get_search_result(searchResultsDbId)
    if not result:
        raise HTTPException(status_code=404, detail="Search results not found")

    data = result["results"]
    total = len(data)
    start = page * pageSize
    paginated = data[start:start + pageSize]

    return _brapi_response({"data": paginated}, page, pageSize, total)


@router.post("/search/plates")
async def search_plates(
    request: PlateSearchRequest,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_optional_user),
):
    """Submit a search request for Plates"""
    # Build query from database
    query = select(Plate)

    # Apply filters
    if request.plateDbIds:
        query = query.where(Plate.plate_db_id.in_(request.plateDbIds))
    if request.plateNames:
        name_filters = [Plate.plate_name.ilike(f"%{name}%") for name in request.plateNames]
        query = query.where(func.or_(*name_filters))
    if request.plateBarcodes:
        query = query.where(Plate.plate_barcode.in_(request.plateBarcodes))
    if request.studyDbIds:
        from app.models.core import Study
        query = query.join(Study).where(Study.study_db_id.in_(request.studyDbIds))
    if request.trialDbIds:
        from app.models.core import Trial
        query = query.join(Trial).where(Trial.trial_db_id.in_(request.trialDbIds))
    if request.programDbIds:
        from app.models.core import Program
        query = query.join(Program).where(Program.program_db_id.in_(request.programDbIds))

    # Execute query and convert to BrAPI format
    result = await db.execute(query)
    plates = result.scalars().all()

    results = []
    for plate in plates:
        results.append({
            "plateDbId": plate.plate_db_id or str(plate.id),
            "plateName": plate.plate_name,
            "plateBarcode": plate.plate_barcode,
            "plateFormat": plate.plate_format,
            "sampleType": plate.sample_type,
            "statusTimeStamp": plate.status_time_stamp,
            "clientPlateDbId": plate.client_plate_db_id,
            "clientPlateBarcode": plate.client_plate_barcode,
            "additionalInfo": plate.additional_info or {},
            "externalReferences": plate.external_references or []
        })

    search_id = await _create_search_result("plates", request.model_dump(), results)
    return _search_response(search_id)


@router.get("/search/plates/{searchResultsDbId}")
async def get_search_plates_results(
    searchResultsDbId: str,
    page: int = Query(0, ge=0),
    pageSize: int = Query(1000, ge=1, le=10000),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_optional_user),
):
    """Get the results of a Plates search request"""
    result = await _get_search_result(searchResultsDbId)
    if not result:
        raise HTTPException(status_code=404, detail="Search results not found")

    data = result["results"]
    total = len(data)
    start = page * pageSize
    paginated = data[start:start + pageSize]

    return _brapi_response({"data": paginated}, page, pageSize, total)


@router.post("/search/references")
async def search_references(
    request: ReferenceSearchRequest,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_optional_user),
):
    """Submit a search request for References"""
    # Build query from database
    query = select(Reference)

    # Apply filters
    if request.referenceDbIds:
        query = query.where(Reference.reference_db_id.in_(request.referenceDbIds))
    if request.referenceSetDbIds:
        query = query.join(ReferenceSet).where(ReferenceSet.reference_set_db_id.in_(request.referenceSetDbIds))
    if request.accessions:
        # Search in source_accessions JSON field
        for acc in request.accessions:
            query = query.where(Reference.source_accessions.contains([acc]))
    if request.md5checksums:
        query = query.where(Reference.md5checksum.in_(request.md5checksums))
    if request.isDerived is not None:
        query = query.where(Reference.is_derived == request.isDerived)
    if request.minLength is not None:
        query = query.where(Reference.length >= request.minLength)
    if request.maxLength is not None:
        query = query.where(Reference.length <= request.maxLength)

    # Execute query and convert to BrAPI format
    result = await db.execute(query)
    references = result.scalars().all()

    results = []
    for ref in references:
        results.append({
            "referenceDbId": ref.reference_db_id or str(ref.id),
            "referenceName": ref.reference_name,
            "length": ref.length,
            "md5checksum": ref.md5checksum,
            "sourceURI": ref.source_uri,
            "sourceAccessions": ref.source_accessions or [],
            "sourceDivergence": ref.source_divergence,
            "species": ref.species,
            "isDerived": ref.is_derived,
            "additionalInfo": ref.additional_info or {},
            "externalReferences": ref.external_references or []
        })

    search_id = await _create_search_result("references", request.model_dump(), results)
    return _search_response(search_id)


@router.get("/search/references/{searchResultsDbId}")
async def get_search_references_results(
    searchResultsDbId: str,
    page: int = Query(0, ge=0),
    pageSize: int = Query(1000, ge=1, le=10000),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_optional_user),
):
    """Get the results of a References search request"""
    result = await _get_search_result(searchResultsDbId)
    if not result:
        raise HTTPException(status_code=404, detail="Search results not found")

    data = result["results"]
    total = len(data)
    start = page * pageSize
    paginated = data[start:start + pageSize]

    return _brapi_response({"data": paginated}, page, pageSize, total)


@router.post("/search/referencesets")
async def search_referencesets(
    request: ReferenceSetSearchRequest,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_optional_user),
):
    """Submit a search request for Reference Sets"""
    # Build query from database
    query = select(ReferenceSet)

    # Apply filters
    if request.referenceSetDbIds:
        query = query.where(ReferenceSet.reference_set_db_id.in_(request.referenceSetDbIds))
    if request.assemblyPUIs:
        query = query.where(ReferenceSet.assembly_pui.in_(request.assemblyPUIs))
    if request.accessions:
        # Search in source_accessions JSON field
        for acc in request.accessions:
            query = query.where(ReferenceSet.source_accessions.contains([acc]))
    if request.md5checksums:
        query = query.where(ReferenceSet.md5checksum.in_(request.md5checksums))

    # Execute query and convert to BrAPI format
    result = await db.execute(query)
    reference_sets = result.scalars().all()

    results = []
    for rs in reference_sets:
        results.append({
            "referenceSetDbId": rs.reference_set_db_id or str(rs.id),
            "referenceSetName": rs.reference_set_name,
            "description": rs.description,
            "assemblyPUI": rs.assembly_pui,
            "sourceURI": rs.source_uri,
            "sourceAccessions": rs.source_accessions or [],
            "sourceGermplasm": rs.source_germplasm or [],
            "species": rs.species,
            "isDerived": rs.is_derived,
            "md5checksum": rs.md5checksum,
            "additionalInfo": rs.additional_info or {},
            "externalReferences": rs.external_references or []
        })

    search_id = await _create_search_result("referencesets", request.model_dump(), results)
    return _search_response(search_id)


@router.get("/search/referencesets/{searchResultsDbId}")
async def get_search_referencesets_results(
    searchResultsDbId: str,
    page: int = Query(0, ge=0),
    pageSize: int = Query(1000, ge=1, le=10000),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_optional_user),
):
    """Get the results of a Reference Sets search request"""
    result = await _get_search_result(searchResultsDbId)
    if not result:
        raise HTTPException(status_code=404, detail="Search results not found")

    data = result["results"]
    total = len(data)
    start = page * pageSize
    paginated = data[start:start + pageSize]

    return _brapi_response({"data": paginated}, page, pageSize, total)


@router.post("/search/markerpositions")
async def search_markerpositions(
    request: MarkerPositionSearchRequest,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_optional_user),
):
    """Submit a search request for Marker Positions"""
    # Build query from database
    query = select(MarkerPosition)

    # Apply filters
    if request.markerPositionDbIds:
        query = query.where(MarkerPosition.marker_position_db_id.in_(request.markerPositionDbIds))
    if request.variantDbIds:
        query = query.where(MarkerPosition.variant_db_id.in_(request.variantDbIds))
    if request.mapDbIds:
        query = query.join(GenomeMap).where(GenomeMap.map_db_id.in_(request.mapDbIds))
    if request.linkageGroupNames:
        query = query.where(MarkerPosition.linkage_group_name.in_(request.linkageGroupNames))
    if request.minPosition is not None:
        query = query.where(MarkerPosition.position >= request.minPosition)
    if request.maxPosition is not None:
        query = query.where(MarkerPosition.position <= request.maxPosition)

    # Execute query and convert to BrAPI format
    result = await db.execute(query)
    marker_positions = result.scalars().all()

    results = []
    for mp in marker_positions:
        results.append({
            "markerPositionDbId": mp.marker_position_db_id or str(mp.id),
            "variantDbId": mp.variant_db_id,
            "variantName": mp.variant_name,
            "mapDbId": mp.genome_map.map_db_id if mp.genome_map else None,
            "mapName": mp.genome_map.map_name if mp.genome_map else None,
            "linkageGroupName": mp.linkage_group_name,
            "position": mp.position,
            "additionalInfo": mp.additional_info or {},
            "externalReferences": mp.external_references or []
        })

    search_id = await _create_search_result("markerpositions", request.model_dump(), results)
    return _search_response(search_id)


@router.get("/search/markerpositions/{searchResultsDbId}")
async def get_search_markerpositions_results(
    searchResultsDbId: str,
    page: int = Query(0, ge=0),
    pageSize: int = Query(1000, ge=1, le=10000),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_optional_user),
):
    """Get the results of a Marker Positions search request"""
    result = await _get_search_result(searchResultsDbId)
    if not result:
        raise HTTPException(status_code=404, detail="Search results not found")

    data = result["results"]
    total = len(data)
    start = page * pageSize
    paginated = data[start:start + pageSize]

    return _brapi_response({"data": paginated}, page, pageSize, total)


@router.post("/search/allelematrix")
async def search_allelematrix(
    request: AlleleMatrixSearchRequest,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_optional_user),
):
    """Submit a search request for Allele Matrix"""
    # Build query from database - allele matrix is a complex query across Call, CallSet, Variant
    # Get call sets
    callset_query = select(CallSet)
    if request.callSetDbIds:
        callset_query = callset_query.where(CallSet.call_set_db_id.in_(request.callSetDbIds))
    if request.sampleDbIds:
        callset_query = callset_query.where(CallSet.sample_db_id.in_(request.sampleDbIds))

    callset_result = await db.execute(callset_query)
    call_sets = callset_result.scalars().all()
    callset_db_ids = [cs.call_set_db_id for cs in call_sets]

    # Get variants
    variant_query = select(Variant)
    if request.variantDbIds:
        variant_query = variant_query.where(Variant.variant_db_id.in_(request.variantDbIds))
    if request.variantSetDbIds:
        variant_query = variant_query.join(VariantSet).where(
            VariantSet.variant_set_db_id.in_(request.variantSetDbIds)
        )

    variant_result = await db.execute(variant_query)
    variants = variant_result.scalars().all()
    variant_db_ids = [v.variant_db_id for v in variants]

    # Get variant set IDs
    variantset_db_ids = list({
        v.variant_set.variant_set_db_id for v in variants
        if v.variant_set and v.variant_set.variant_set_db_id
    }) if variants else (request.variantSetDbIds or [])

    # Build genotype matrix from calls
    # Query calls for the selected callsets and variants
    if call_sets and variants:
        calls_query = select(Call).join(CallSet).join(Variant).where(
            CallSet.call_set_db_id.in_(callset_db_ids),
            Variant.variant_db_id.in_(variant_db_ids)
        )
        calls_result = await db.execute(calls_query)
        calls = calls_result.scalars().all()

        # Build matrix: rows = variants, columns = callsets
        # Optimization: Pre-build lookup map for calls to avoid O(N^2) search
        calls_map = {
            (c.variant.variant_db_id, c.call_set.call_set_db_id): c
            for c in calls
        }

        matrix = []
        for var in variants:
            row = []
            for cs in call_sets:
                call = calls_map.get((var.variant_db_id, cs.call_set_db_id))
                row.append(call.genotype_value if call else "./.")
            matrix.append(row)
    else:
        matrix = []

    # Build result in BrAPI format
    result_data = {
        "callSetDbIds": callset_db_ids or [],
        "variantDbIds": variant_db_ids or [],
        "variantSetDbIds": variantset_db_ids or [],
        "dataMatrices": [
            {
                "dataMatrixAbbreviation": "GT",
                "dataMatrixName": "Genotype",
                "dataType": "string",
                "dataMatrix": matrix
            }
        ] if matrix else [],
        "pagination": [
            {"dimension": "VARIANTS", "page": 0, "pageSize": len(variant_db_ids), "totalCount": len(variant_db_ids), "totalPages": 1},
            {"dimension": "CALLSETS", "page": 0, "pageSize": len(callset_db_ids), "totalCount": len(callset_db_ids), "totalPages": 1}
        ]
    }

    search_id = await _create_search_result("allelematrix", request.model_dump(), [result_data])
    return _search_response(search_id)


@router.get("/search/allelematrix/{searchResultsDbId}")
async def get_search_allelematrix_results(
    searchResultsDbId: str,
    page: int = Query(0, ge=0),
    pageSize: int = Query(1000, ge=1, le=10000),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_optional_user),
):
    """Get the results of an Allele Matrix search request"""
    result = await _get_search_result(searchResultsDbId)
    if not result:
        raise HTTPException(status_code=404, detail="Search results not found")

    # Allele matrix has special structure
    data = result["results"][0] if result["results"] else {}

    return {
        "metadata": {
            "datafiles": [],
            "pagination": {"currentPage": page, "pageSize": pageSize, "totalCount": 1, "totalPages": 1},
            "status": [{"message": "Request successful", "messageType": "INFO"}]
        },
        "result": data
    }
