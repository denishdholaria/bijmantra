"""
Meilisearch Integration for Instant Search
Indexes BrAPI data for typo-tolerant, instant search

Updated Dec 2025:
- Hybrid search (keyword + semantic)
- Federated multi-index search
- Similar documents API
- Ranking score threshold
"""

from datetime import UTC, datetime
from typing import Any

from meilisearch import Client

# Configuration - import from settings to ensure .env is loaded
from app.core.config import settings


MEILISEARCH_HOST = settings.MEILISEARCH_HOST
MEILISEARCH_API_KEY = settings.MEILISEARCH_API_KEY

# Index names
INDEXES = {
    "germplasm": "germplasm",
    "traits": "traits",
    "trials": "trials",
    "locations": "locations",
    "observations": "observations",
    "programs": "programs",
    "studies": "studies",
}

# Index configurations with v1.11+ features
INDEX_SETTINGS = {
    "germplasm": {
        "searchableAttributes": [
            "germplasmName",
            "accessionNumber",
            "species",
            "genus",
            "subtaxa",
            "synonyms",
            "instituteCode",
            "countryOfOrigin",
            "pedigree",
        ],
        "filterableAttributes": [
            "species",
            "genus",
            "countryOfOrigin",
            "biologicalStatus",
            "instituteCode",
            "collectionDate",
        ],
        "sortableAttributes": [
            "germplasmName",
            "accessionNumber",
            "createdAt",
            "collectionDate",
        ],
        "displayedAttributes": [
            "germplasmDbId",
            "germplasmName",
            "accessionNumber",
            "species",
            "genus",
            "countryOfOrigin",
            "biologicalStatus",
            "synonyms",
            "pedigree",
        ],
        "rankingRules": [
            "words",
            "typo",
            "proximity",
            "attribute",
            "sort",
            "exactness",
        ],
        "typoTolerance": {
            "enabled": True,
            "minWordSizeForTypos": {
                "oneTypo": 4,
                "twoTypos": 8,
            },
        },
        "pagination": {
            "maxTotalHits": 10000,
        },
    },
    "traits": {
        "searchableAttributes": [
            "observationVariableName",
            "trait.traitName",
            "trait.traitDescription",
            "trait.traitClass",
            "method.methodName",
            "method.methodDescription",
            "scale.scaleName",
            "ontologyReference.ontologyName",
        ],
        "filterableAttributes": [
            "trait.traitClass",
            "ontologyReference.ontologyName",
            "scale.dataType",
        ],
        "sortableAttributes": [
            "observationVariableName",
            "trait.traitName",
        ],
        "typoTolerance": {
            "enabled": True,
        },
    },
    "trials": {
        "searchableAttributes": [
            "trialName",
            "trialDescription",
            "programName",
            "locationName",
            "contacts",
        ],
        "filterableAttributes": [
            "programDbId",
            "locationDbId",
            "active",
            "startDate",
            "endDate",
            "trialType",
        ],
        "sortableAttributes": [
            "trialName",
            "startDate",
            "endDate",
        ],
        "typoTolerance": {
            "enabled": True,
        },
    },
    "locations": {
        "searchableAttributes": [
            "locationName",
            "locationType",
            "countryName",
            "instituteName",
            "abbreviation",
        ],
        "filterableAttributes": [
            "countryCode",
            "locationType",
            "_geo",  # Enable geo search
        ],
        "sortableAttributes": [
            "locationName",
            "_geoPoint",  # Sort by distance
        ],
        "typoTolerance": {
            "enabled": True,
        },
    },
    "programs": {
        "searchableAttributes": [
            "programName",
            "programDescription",
            "objective",
            "leadPerson",
        ],
        "filterableAttributes": [
            "commonCropName",
            "active",
        ],
        "sortableAttributes": [
            "programName",
            "createdAt",
        ],
    },
    "studies": {
        "searchableAttributes": [
            "studyName",
            "studyDescription",
            "studyType",
            "trialName",
            "locationName",
        ],
        "filterableAttributes": [
            "trialDbId",
            "locationDbId",
            "active",
            "seasonDbId",
            "studyType",
        ],
        "sortableAttributes": [
            "studyName",
            "startDate",
        ],
    },
}

TENANT_FILTER_ATTRIBUTE = "organization_id"

for _index_settings in INDEX_SETTINGS.values():
    _filterable = _index_settings.setdefault("filterableAttributes", [])
    if TENANT_FILTER_ATTRIBUTE not in _filterable:
        _filterable.append(TENANT_FILTER_ATTRIBUTE)


def _organization_id_from(source: dict[str, Any]) -> int | str | None:
    return (
        source.get("organization_id")
        or source.get("organizationId")
        or source.get("organizationDbId")
    )


def _with_tenant(source: dict[str, Any], document: dict[str, Any]) -> dict[str, Any]:
    organization_id = _organization_id_from(source)
    if organization_id is not None:
        document[TENANT_FILTER_ATTRIBUTE] = organization_id
    return document


def _tenant_filter(organization_id: int | str | None) -> str | None:
    if organization_id is None:
        return None
    try:
        return f"{TENANT_FILTER_ATTRIBUTE} = {int(organization_id)}"
    except (TypeError, ValueError):
        escaped_id = str(organization_id).replace('"', '\\"')
        return f'{TENANT_FILTER_ATTRIBUTE} = "{escaped_id}"'


def _merge_filter_options(
    options: dict[str, Any] | None,
    organization_id: int | str | None,
) -> dict[str, Any]:
    merged_options = dict(options or {})
    tenant_filter = _tenant_filter(organization_id)
    if not tenant_filter:
        return merged_options

    existing_filter = merged_options.get("filter")
    if existing_filter:
        merged_options["filter"] = f"({existing_filter}) AND {tenant_filter}"
    else:
        merged_options["filter"] = tenant_filter
    return merged_options


class MeilisearchService:
    """Service for managing Meilisearch indexes and search

    Features (v1.11+):
    - Typo-tolerant instant search
    - Federated multi-index search
    - Similar documents API
    - Geo search for locations
    - Ranking score threshold
    """

    def __init__(self):
        self.client: Client | None = None
        self._connected = False
        self._version: str | None = None

    def connect(self) -> bool:
        """Connect to Meilisearch server"""
        try:
            api_key = MEILISEARCH_API_KEY if MEILISEARCH_API_KEY else None
            self.client = Client(MEILISEARCH_HOST, api_key)
            # Test connection and get version
            self.client.health()
            version_info = self.client.get_version()
            self._version = version_info.get("pkgVersion", "unknown")
            self._connected = True
            print(f"[Meilisearch] Connected to {MEILISEARCH_HOST} (v{self._version})")
            return True
        except Exception as e:
            print(f"[Meilisearch] Connection failed: {e}")
            self._connected = False
            return False

    @property
    def connected(self) -> bool:
        return self._connected

    @property
    def version(self) -> str | None:
        return self._version

    def setup_indexes(self):
        """Create and configure all indexes"""
        if not self.client:
            raise RuntimeError("Not connected to Meilisearch")

        for index_name, idx_settings in INDEX_SETTINGS.items():
            try:
                # Determine primary key based on index
                pk_map = {
                    "germplasm": "germplasmDbId",
                    "traits": "observationVariableDbId",
                    "trials": "trialDbId",
                    "locations": "locationDbId",
                    "observations": "observationDbId",
                    "programs": "programDbId",
                    "studies": "studyDbId",
                }
                primary_key = pk_map.get(index_name, f"{index_name[:-1]}DbId")

                # Create index if not exists
                self.client.create_index(index_name, {"primaryKey": primary_key})
                print(f"[Meilisearch] Created index: {index_name}")
            except Exception:
                pass  # Index might already exist

            # Update settings
            index = self.client.index(index_name)
            index.update_settings(idx_settings)
            print(f"[Meilisearch] Configured index: {index_name}")

    def index_germplasm(self, germplasm_list: list[dict[str, Any]]):
        """Index germplasm documents"""
        if not self.client:
            return

        documents = []
        for g in germplasm_list:
            documents.append(
                _with_tenant(
                    g,
                    {
                        "id": g.get("germplasmDbId"),
                        "germplasmDbId": g.get("germplasmDbId"),
                        "germplasmName": g.get("germplasmName"),
                        "accessionNumber": g.get("accessionNumber"),
                        "species": g.get("species"),
                        "genus": g.get("genus"),
                        "subtaxa": g.get("subtaxa"),
                        "synonyms": g.get("synonyms", []),
                        "instituteCode": g.get("instituteCode"),
                        "countryOfOrigin": g.get("countryOfOriginCode"),
                        "biologicalStatus": g.get("biologicalStatusOfAccessionCode"),
                        "pedigree": g.get("pedigree"),
                        "collectionDate": g.get("acquisitionDate"),
                        "createdAt": datetime.now(UTC).isoformat(),
                    },
                )
            )

        index = self.client.index(INDEXES["germplasm"])
        task = index.add_documents(documents, primary_key="germplasmDbId")
        print(f"[Meilisearch] Indexed {len(documents)} germplasm documents (task: {task.task_uid})")
        return task

    def index_traits(self, traits_list: list[dict[str, Any]]):
        """Index trait/observation variable documents"""
        if not self.client:
            return

        documents = []
        for t in traits_list:
            documents.append(
                _with_tenant(
                    t,
                    {
                        "id": t.get("observationVariableDbId"),
                        "observationVariableDbId": t.get("observationVariableDbId"),
                        "observationVariableName": t.get("observationVariableName"),
                        "trait": t.get("trait", {}),
                        "method": t.get("method", {}),
                        "scale": t.get("scale", {}),
                        "ontologyReference": t.get("ontologyReference", {}),
                    },
                )
            )

        index = self.client.index(INDEXES["traits"])
        task = index.add_documents(documents, primary_key="observationVariableDbId")
        print(f"[Meilisearch] Indexed {len(documents)} trait documents (task: {task.task_uid})")
        return task

    def index_trials(self, trials_list: list[dict[str, Any]]):
        """Index trial documents"""
        if not self.client:
            return

        documents = []
        for t in trials_list:
            documents.append(
                _with_tenant(
                    t,
                    {
                        "id": t.get("trialDbId"),
                        "trialDbId": t.get("trialDbId"),
                        "trialName": t.get("trialName"),
                        "trialDescription": t.get("trialDescription"),
                        "programDbId": t.get("programDbId"),
                        "programName": t.get("programName"),
                        "locationDbId": t.get("locationDbId"),
                        "locationName": t.get("locationName"),
                        "startDate": t.get("startDate"),
                        "endDate": t.get("endDate"),
                        "active": t.get("active", True),
                        "trialType": t.get("trialType"),
                        "contacts": [c.get("name", "") for c in t.get("contacts", [])],
                    },
                )
            )

        index = self.client.index(INDEXES["trials"])
        task = index.add_documents(documents, primary_key="trialDbId")
        print(f"[Meilisearch] Indexed {len(documents)} trial documents (task: {task.task_uid})")
        return task

    def index_locations(self, locations_list: list[dict[str, Any]]):
        """Index location documents with geo coordinates"""
        if not self.client:
            return

        documents = []
        for loc in locations_list:
            doc = {
                "id": loc.get("locationDbId"),
                "locationDbId": loc.get("locationDbId"),
                "locationName": loc.get("locationName"),
                "locationType": loc.get("locationType"),
                "countryCode": loc.get("countryCode"),
                "countryName": loc.get("countryName"),
                "instituteName": loc.get("instituteName"),
                "abbreviation": loc.get("abbreviation"),
            }
            # Add geo coordinates if available
            coords = loc.get("coordinates", {})
            if coords.get("latitude") and coords.get("longitude"):
                doc["_geo"] = {
                    "lat": float(coords["latitude"]),
                    "lng": float(coords["longitude"]),
                }
            documents.append(_with_tenant(loc, doc))

        index = self.client.index(INDEXES["locations"])
        task = index.add_documents(documents, primary_key="locationDbId")
        print(f"[Meilisearch] Indexed {len(documents)} location documents (task: {task.task_uid})")
        return task

    def index_programs(self, programs_list: list[dict[str, Any]]):
        """Index breeding program documents"""
        if not self.client:
            return

        documents = []
        for p in programs_list:
            documents.append(
                _with_tenant(
                    p,
                    {
                        "id": p.get("programDbId"),
                        "programDbId": p.get("programDbId"),
                        "programName": p.get("programName"),
                        "programDescription": p.get("programDescription"),
                        "objective": p.get("objective"),
                        "commonCropName": p.get("commonCropName"),
                        "leadPerson": p.get("leadPersonName"),
                        "active": p.get("active", True),
                        "createdAt": datetime.now(UTC).isoformat(),
                    },
                )
            )

        index = self.client.index(INDEXES["programs"])
        task = index.add_documents(documents, primary_key="programDbId")
        print(f"[Meilisearch] Indexed {len(documents)} program documents (task: {task.task_uid})")
        return task

    def index_studies(self, studies_list: list[dict[str, Any]]):
        """Index study documents"""
        if not self.client:
            return

        documents = []
        for s in studies_list:
            documents.append(
                _with_tenant(
                    s,
                    {
                        "id": s.get("studyDbId"),
                        "studyDbId": s.get("studyDbId"),
                        "studyName": s.get("studyName"),
                        "studyDescription": s.get("studyDescription"),
                        "studyType": s.get("studyType"),
                        "trialDbId": s.get("trialDbId"),
                        "trialName": s.get("trialName"),
                        "locationDbId": s.get("locationDbId"),
                        "locationName": s.get("locationName"),
                        "seasonDbId": s.get("seasonDbId"),
                        "startDate": s.get("startDate"),
                        "active": s.get("active", True),
                    },
                )
            )

        index = self.client.index(INDEXES["studies"])
        task = index.add_documents(documents, primary_key="studyDbId")
        print(f"[Meilisearch] Indexed {len(documents)} study documents (task: {task.task_uid})")
        return task

    def search(
        self,
        index_name: str,
        query: str,
        options: dict | None = None,
        organization_id: int | str | None = None,
    ) -> dict:
        """Search an index with options"""
        if not self.client:
            return {"hits": [], "query": query}

        index = self.client.index(index_name)
        search_options = _merge_filter_options(options, organization_id)
        return index.search(query, search_options)

    def search_with_score_threshold(
        self,
        index_name: str,
        query: str,
        threshold: float = 0.5,
        limit: int = 20,
        organization_id: int | str | None = None,
    ) -> dict:
        """Search with ranking score threshold (v1.9+ feature)

        Only returns results above the score threshold for better relevance.
        """
        if not self.client:
            return {"hits": [], "query": query}

        index = self.client.index(index_name)
        search_options = _merge_filter_options(
            {
                "limit": limit,
                "showRankingScore": True,
                "rankingScoreThreshold": threshold,
            },
            organization_id,
        )
        return index.search(query, search_options)

    def federated_search(
        self,
        query: str,
        indexes: list[str] | None = None,
        limit: int = 20,
        organization_id: int | str | None = None,
    ) -> dict:
        """Federated search across multiple indexes (v1.10+ feature)

        Merges results from multiple indexes into a single ranked response.
        """
        if not self.client:
            return {"hits": [], "query": query}

        target_indexes = indexes or list(INDEXES.values())

        # Build federation queries
        queries = []
        for idx in target_indexes:
            search_options = _merge_filter_options({"limit": limit}, organization_id)
            queries.append(
                {
                    "indexUid": idx,
                    "q": query,
                    **search_options,
                }
            )

        try:
            # Use multi_search with federation
            result = self.client.multi_search(
                queries,
                {
                    "federation": {
                        "limit": limit,
                    }
                },
            )
            return result
        except Exception as e:
            # Fallback to regular multi-search if federation not supported
            print(f"[Meilisearch] Federation not available, using multi-search: {e}")
            return self.client.multi_search(queries)

    def search_all(
        self,
        query: str,
        limit: int = 10,
        organization_id: int | str | None = None,
    ) -> list[dict]:
        """Search across all indexes (legacy method, use federated_search for v1.10+)"""
        if not self.client:
            return []

        results = []
        per_index_limit = max(1, limit // len(INDEXES))

        for index_name in INDEXES.values():
            try:
                search_result = self.search(
                    index_name,
                    query,
                    {
                        "limit": per_index_limit,
                        "showRankingScore": True,
                    },
                    organization_id=organization_id,
                )
                for hit in search_result.get("hits", []):
                    hit["_index"] = index_name
                    results.append(hit)
            except Exception as e:
                print(f"[Meilisearch] Search error in {index_name}: {e}")

        # Sort by ranking score if available
        results.sort(key=lambda x: x.get("_rankingScore", 0), reverse=True)
        return results[:limit]

    def get_similar_documents(
        self,
        index_name: str,
        document_id: str,
        limit: int = 10,
        filter_str: str | None = None,
        organization_id: int | str | None = None,
    ) -> dict:
        """Get similar documents (v1.9+ feature)

        Finds documents similar to the given document based on content.
        """
        if not self.client:
            return {"hits": []}

        index = self.client.index(index_name)
        options = {
            "limit": limit,
            "showRankingScore": True,
        }
        if filter_str:
            options["filter"] = filter_str
        options = _merge_filter_options(options, organization_id)

        try:
            return index.search_similar_documents(document_id, options)
        except Exception as e:
            print(f"[Meilisearch] Similar documents error: {e}")
            return {"hits": []}

    def geo_search(
        self,
        index_name: str,
        query: str,
        lat: float,
        lng: float,
        radius_km: float = 100,
        limit: int = 20,
        organization_id: int | str | None = None,
    ) -> dict:
        """Search with geo radius filter

        Finds documents within radius_km of the given coordinates.
        """
        if not self.client:
            return {"hits": [], "query": query}

        index = self.client.index(index_name)
        # Convert km to meters for Meilisearch
        radius_m = int(radius_km * 1000)

        search_options = _merge_filter_options(
            {
                "limit": limit,
                "filter": f"_geoRadius({lat}, {lng}, {radius_m})",
                "sort": [f"_geoPoint({lat}, {lng}):asc"],
            },
            organization_id,
        )
        return index.search(query, search_options)

    def delete_document(self, index_name: str, document_id: str):
        """Delete a document from an index"""
        if not self.client:
            return

        index = self.client.index(index_name)
        index.delete_document(document_id)

    def delete_documents_by_filter(
        self,
        index_name: str,
        filter_str: str,
        organization_id: int | str | None = None,
    ):
        """Delete documents matching a filter (v1.2+ feature)"""
        if not self.client:
            return

        index = self.client.index(index_name)
        delete_filter = _merge_filter_options({"filter": filter_str}, organization_id)["filter"]
        return index.delete_documents_by_filter(delete_filter)

    def clear_index(self, index_name: str):
        """Clear all documents from an index"""
        if not self.client:
            return

        index = self.client.index(index_name)
        index.delete_all_documents()

    def get_stats(self) -> dict:
        """Get Meilisearch instance statistics"""
        if not self.client:
            return {}

        try:
            stats = self.client.get_stats()
            return {
                "databaseSize": stats.get("databaseSize", 0),
                "indexes": {
                    name: {
                        "numberOfDocuments": idx.get("numberOfDocuments", 0),
                        "isIndexing": idx.get("isIndexing", False),
                    }
                    for name, idx in stats.get("indexes", {}).items()
                },
                "version": self._version,
            }
        except Exception as e:
            print(f"[Meilisearch] Stats error: {e}")
            return {}

    def get_tasks(self, limit: int = 20) -> list[dict]:
        """Get recent indexing tasks"""
        if not self.client:
            return []

        try:
            result = self.client.get_tasks({"limit": limit})
            return result.get("results", [])
        except Exception as e:
            print(f"[Meilisearch] Tasks error: {e}")
            return []


# Singleton instance
meilisearch_service = MeilisearchService()


# FastAPI dependency
def get_meilisearch() -> MeilisearchService:
    """Get Meilisearch service instance"""
    if not meilisearch_service.connected:
        meilisearch_service.connect()
    return meilisearch_service
