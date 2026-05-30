"""Legacy bridges for Intelligence Knowledge Graph retrieval.

These adapters let old service methods delegate into Intelligence application code
without importing Intelligence's route-facing adapter and creating an import cycle.
"""

from typing import Any, Protocol

from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.intelligence.capabilities.knowledge_graph.schemas.knowledge_graph import (
    KnowledgeGraphEdgeResponse,
    KnowledgeGraphEdgesListQuery,
    KnowledgeGraphEvidencePackQuery,
    KnowledgeGraphEvidencePackResponse,
    KnowledgeGraphEvidenceSearchQuery,
    KnowledgeGraphEvidenceSearchResponse,
    KnowledgeGraphFairAssetRef,
    KnowledgeGraphNeighborhoodQuery,
    KnowledgeGraphNeighborhoodResponse,
)
from app.domains.knowledge.capabilities.research_asset_core.ports import (
    FairAssetMetadataRecord,
)


class LegacyKnowledgeGraphRetrievalService(Protocol):
    fair_metadata_service: Any

    def require_supported_direction(self, direction: str) -> str:
        """Normalize and validate a graph direction."""

    def require_supported_result_side(self, result_side: str) -> str:
        """Normalize and validate a graph evidence-search result side."""

    def require_supported_relationship_type(self, relationship_type: str) -> str:
        """Normalize and validate a graph relationship type."""

    async def list_edges(
        self,
        db: AsyncSession,
        *,
        organization_id: int,
        source_asset_type: str | None = None,
        source_asset_id: str | None = None,
        target_asset_type: str | None = None,
        target_asset_id: str | None = None,
        relationship_type: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Any]:
        """Return legacy Knowledge Graph edge models."""

    async def search_evidence(
        self,
        db: AsyncSession,
        *,
        organization_id: int,
        source_asset_type: str | None = None,
        source_asset_id: str | None = None,
        target_asset_type: str | None = None,
        target_asset_id: str | None = None,
        relationship_type: str | None = None,
        result_side: str = "source",
        limit: int = 100,
        offset: int = 0,
    ) -> KnowledgeGraphEvidenceSearchResponse:
        """Return legacy evidence search results."""

    async def build_evidence_pack(
        self,
        db: AsyncSession,
        *,
        organization_id: int,
        asset_type: str,
        asset_id: str,
        direction: str = "both",
        relationship_type: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> KnowledgeGraphEvidencePackResponse:
        """Return the legacy evidence pack."""

    async def get_neighborhood(
        self,
        db: AsyncSession,
        *,
        organization_id: int,
        asset_type: str,
        asset_id: str,
        direction: str = "both",
        relationship_type: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> KnowledgeGraphNeighborhoodResponse:
        """Return the legacy neighborhood response."""

    async def require_fair_asset(
        self,
        db: AsyncSession,
        *,
        organization_id: int,
        asset_type: str,
        asset_db_id: str,
    ) -> FairAssetMetadataRecord:
        """Return FAIR metadata through the ResearchAsset boundary."""


class LegacyKnowledgeGraphRetrievalDataSource:
    """Data-source adapter from Intelligence retrieval use cases to the legacy service."""

    def __init__(
        self,
        db: AsyncSession,
        service: LegacyKnowledgeGraphRetrievalService,
    ) -> None:
        self._db = db
        self._service = service

    def normalize_direction(self, direction: str) -> str:
        return self._service.require_supported_direction(direction)

    async def search_evidence(
        self, query: KnowledgeGraphEvidenceSearchQuery
    ) -> KnowledgeGraphEvidenceSearchResponse:
        return await self._service.search_evidence(
            self._db,
            organization_id=query.organization_id,
            source_asset_type=query.source_asset_type,
            source_asset_id=query.source_asset_id,
            target_asset_type=query.target_asset_type,
            target_asset_id=query.target_asset_id,
            relationship_type=query.relationship_type,
            result_side=query.result_side,
            limit=query.limit,
            offset=query.offset,
        )

    async def build_evidence_pack(
        self, query: KnowledgeGraphEvidencePackQuery
    ) -> KnowledgeGraphEvidencePackResponse:
        return await self._service.build_evidence_pack(
            self._db,
            organization_id=query.organization_id,
            asset_type=query.asset_type,
            asset_id=query.asset_id,
            direction=query.direction,
            relationship_type=query.relationship_type,
            limit=query.limit,
            offset=query.offset,
        )


class LegacyKnowledgeGraphEvidenceSearchDataSource:
    """Data-source adapter from Intelligence evidence-search builder to the legacy service."""

    def __init__(
        self,
        db: AsyncSession,
        service: LegacyKnowledgeGraphRetrievalService,
    ) -> None:
        self._db = db
        self._service = service

    def normalize_result_side(self, result_side: str) -> str:
        return self._service.require_supported_result_side(result_side)

    def normalize_asset_type(self, asset_type: str) -> str:
        return self._service.fair_metadata_service.require_supported_asset_type(asset_type)

    def normalize_relationship_type(self, relationship_type: str) -> str:
        return self._service.require_supported_relationship_type(relationship_type)

    async def list_edges(
        self, query: KnowledgeGraphEdgesListQuery
    ) -> list[KnowledgeGraphEdgeResponse]:
        edges = await self._service.list_edges(
            self._db,
            organization_id=query.organization_id,
            source_asset_type=query.source_asset_type,
            source_asset_id=query.source_asset_id,
            target_asset_type=query.target_asset_type,
            target_asset_id=query.target_asset_id,
            relationship_type=query.relationship_type,
            limit=query.limit,
            offset=query.offset,
        )
        return [KnowledgeGraphEdgeResponse.model_validate(edge) for edge in edges]

    async def require_fair_asset(
        self,
        *,
        organization_id: int,
        asset_type: str,
        asset_id: str,
    ) -> KnowledgeGraphFairAssetRef:
        metadata = await self._service.require_fair_asset(
            self._db,
            organization_id=organization_id,
            asset_type=asset_type,
            asset_db_id=asset_id,
        )
        return KnowledgeGraphFairAssetRef(
            asset_type=asset_type,
            asset_id=asset_id,
            asset_title=metadata.title,
            persistent_identifier=metadata.persistent_identifier,
        )


class LegacyKnowledgeGraphEvidencePackDataSource:
    """Data-source adapter from Intelligence evidence-pack builder to the legacy service."""

    def __init__(
        self,
        db: AsyncSession,
        service: LegacyKnowledgeGraphRetrievalService,
    ) -> None:
        self._db = db
        self._service = service

    def normalize_asset_type(self, asset_type: str) -> str:
        return self._service.fair_metadata_service.require_supported_asset_type(asset_type)

    async def require_fair_asset(
        self,
        *,
        organization_id: int,
        asset_type: str,
        asset_id: str,
    ) -> KnowledgeGraphFairAssetRef:
        metadata = await self._service.require_fair_asset(
            self._db,
            organization_id=organization_id,
            asset_type=asset_type,
            asset_db_id=asset_id,
        )
        return KnowledgeGraphFairAssetRef(
            asset_type=asset_type,
            asset_id=asset_id,
            asset_title=metadata.title,
            persistent_identifier=metadata.persistent_identifier,
        )

    async def get_neighborhood(
        self, query: KnowledgeGraphNeighborhoodQuery
    ) -> KnowledgeGraphNeighborhoodResponse:
        return await self._service.get_neighborhood(
            self._db,
            organization_id=query.organization_id,
            asset_type=query.asset_type,
            asset_id=query.asset_id,
            direction=query.direction,
            relationship_type=query.relationship_type,
            limit=query.limit,
            offset=query.offset,
        )
