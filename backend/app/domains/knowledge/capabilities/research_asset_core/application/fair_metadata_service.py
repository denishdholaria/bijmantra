"""Application facade for tenant-scoped FAIR asset metadata."""

from collections.abc import Callable
from typing import Any

from app.domains.knowledge.capabilities.research_asset_core.domain import (
    policies as research_asset_policies,
)
from app.domains.knowledge.capabilities.research_asset_core.ports import (
    FairAssetMetadataRecord,
    FairAssetMetadataRepository,
    FairAssetMetadataWrite,
    FairAssetTargetRecord,
)
from app.domains.knowledge.capabilities.research_asset_core.schemas.fair_metadata import (
    FAIRAssetMetadataUpsert,
)


InvalidFairPersistentIdentifier = research_asset_policies.InvalidFairPersistentIdentifier
UnknownFairAssetType = research_asset_policies.UnknownFairAssetType


class FairAssetNotFound(ValueError):
    """Raised when a referenced asset is not owned by the organization."""


FairMetadataRepositoryFactory = Callable[[Any], FairAssetMetadataRepository]


class FairAssetMetadataApplicationService:
    """Create, read, and list FAIR metadata for tenant-owned agricultural assets."""

    def __init__(
        self,
        *,
        repository_factory: FairMetadataRepositoryFactory | None = None,
    ) -> None:
        self._repository_factory = repository_factory

    def normalize_asset_type(self, asset_type: str) -> str:
        return research_asset_policies.normalize_fair_asset_type(asset_type)

    def require_supported_asset_type(self, asset_type: str) -> str:
        return research_asset_policies.require_supported_fair_asset_type(asset_type)

    async def upsert_asset_metadata(
        self,
        db: Any,
        *,
        organization_id: int,
        asset_type: str,
        asset_db_id: str,
        payload: FAIRAssetMetadataUpsert,
    ) -> FairAssetMetadataRecord:
        normalized_asset_type = self.require_supported_asset_type(asset_type)
        repository = self._repository(db)
        target_asset = await repository.get_target_asset(
            organization_id=organization_id,
            asset_type=normalized_asset_type,
            asset_db_id=asset_db_id,
        )
        if target_asset is None:
            raise FairAssetNotFound(
                f"{normalized_asset_type} '{asset_db_id}' was not found in this organization"
            )

        metadata = await repository.get_metadata(
            organization_id=organization_id,
            asset_type=normalized_asset_type,
            asset_db_id=asset_db_id,
        )
        is_new = metadata is None
        fields_set = payload.model_fields_set
        return await repository.save_metadata(
            FairAssetMetadataWrite(
                metadata_id=metadata.id if metadata else None,
                organization_id=organization_id,
                asset_type=normalized_asset_type,
                asset_db_id=asset_db_id,
                persistent_identifier=self._metadata_scalar(
                    payload,
                    metadata,
                    "persistent_identifier",
                    is_new=is_new,
                    fields_set=fields_set,
                    fallback=self._resolve_persistent_identifier(
                        payload.persistent_identifier,
                        asset_type=normalized_asset_type,
                        asset_db_id=asset_db_id,
                    ),
                ),
                title=self._metadata_scalar(
                    payload,
                    metadata,
                    "title",
                    is_new=is_new,
                    fields_set=fields_set,
                    fallback=payload.title or target_asset.title,
                ),
                description=self._metadata_scalar(
                    payload,
                    metadata,
                    "description",
                    is_new=is_new,
                    fields_set=fields_set,
                ),
                access_rights=self._metadata_scalar(
                    payload,
                    metadata,
                    "access_rights",
                    is_new=is_new,
                    fields_set=fields_set,
                ),
                license=self._metadata_scalar(
                    payload,
                    metadata,
                    "license",
                    is_new=is_new,
                    fields_set=fields_set,
                ),
                data_standard=self._metadata_scalar(
                    payload,
                    metadata,
                    "data_standard",
                    is_new=is_new,
                    fields_set=fields_set,
                ),
                confidence=self._metadata_scalar(
                    payload,
                    metadata,
                    "confidence",
                    is_new=is_new,
                    fields_set=fields_set,
                ),
                data_source=self._metadata_scalar(
                    payload,
                    metadata,
                    "data_source",
                    is_new=is_new,
                    fields_set=fields_set,
                ),
                keywords=self._metadata_list(
                    payload,
                    metadata,
                    "keywords",
                    is_new=is_new,
                    fields_set=fields_set,
                ),
                ontology_terms=self._metadata_list(
                    payload,
                    metadata,
                    "ontology_terms",
                    is_new=is_new,
                    fields_set=fields_set,
                ),
                contributors=self._metadata_list(
                    payload,
                    metadata,
                    "contributors",
                    is_new=is_new,
                    fields_set=fields_set,
                ),
                funding_acknowledgements=self._metadata_list(
                    payload,
                    metadata,
                    "funding_acknowledgements",
                    is_new=is_new,
                    fields_set=fields_set,
                ),
                external_references=self._metadata_list(
                    payload,
                    metadata,
                    "external_references",
                    is_new=is_new,
                    fields_set=fields_set,
                ),
                evidence_refs=self._metadata_list(
                    payload,
                    metadata,
                    "evidence_refs",
                    is_new=is_new,
                    fields_set=fields_set,
                ),
                provenance=self._metadata_dict(
                    payload,
                    metadata,
                    "provenance",
                    is_new=is_new,
                    fields_set=fields_set,
                ),
                schema_version=(metadata.schema_version if metadata else None)
                or "fair_asset_metadata.v1",
            )
        )

    async def get_asset_metadata(
        self,
        db: Any,
        *,
        organization_id: int,
        asset_type: str,
        asset_db_id: str,
    ) -> FairAssetMetadataRecord | None:
        normalized_asset_type = self.require_supported_asset_type(asset_type)
        return await self._repository(db).get_metadata(
            organization_id=organization_id,
            asset_type=normalized_asset_type,
            asset_db_id=asset_db_id,
        )

    async def list_asset_metadata(
        self,
        db: Any,
        *,
        organization_id: int,
        asset_type: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[FairAssetMetadataRecord]:
        normalized_asset_type = (
            self.require_supported_asset_type(asset_type) if asset_type else None
        )
        return await self._repository(db).list_metadata(
            organization_id=organization_id,
            asset_type=normalized_asset_type,
            limit=limit,
            offset=offset,
        )

    async def _get_target_asset(
        self,
        db: Any,
        *,
        organization_id: int,
        asset_type: str,
        asset_db_id: str,
    ) -> FairAssetTargetRecord | None:
        return await self._repository(db).get_target_asset(
            organization_id=organization_id,
            asset_type=asset_type,
            asset_db_id=asset_db_id,
        )

    def _metadata_scalar(
        self,
        payload: FAIRAssetMetadataUpsert,
        metadata: FairAssetMetadataRecord | None,
        field: str,
        *,
        is_new: bool,
        fields_set: set[str],
        fallback: Any = None,
    ) -> Any:
        if is_new or field in fields_set:
            value = getattr(payload, field)
            return fallback if value is None and fallback is not None else value
        return getattr(metadata, field) if metadata else fallback

    def _metadata_list(
        self,
        payload: FAIRAssetMetadataUpsert,
        metadata: FairAssetMetadataRecord | None,
        field: str,
        *,
        is_new: bool,
        fields_set: set[str],
    ) -> list[Any]:
        if is_new or field in fields_set:
            return list(getattr(payload, field) or [])
        return list(getattr(metadata, field) or []) if metadata else []

    def _metadata_dict(
        self,
        payload: FAIRAssetMetadataUpsert,
        metadata: FairAssetMetadataRecord | None,
        field: str,
        *,
        is_new: bool,
        fields_set: set[str],
    ) -> dict[str, Any]:
        if is_new or field in fields_set:
            return dict(getattr(payload, field) or {})
        return dict(getattr(metadata, field) or {}) if metadata else {}

    def _resolve_persistent_identifier(
        self,
        persistent_identifier: str | None,
        *,
        asset_type: str,
        asset_db_id: str,
    ) -> str:
        return research_asset_policies.resolve_persistent_identifier(
            persistent_identifier,
            asset_type=asset_type,
            asset_db_id=asset_db_id,
        )

    def _repository(self, db: Any) -> FairAssetMetadataRepository:
        if self._repository_factory is None:
            raise RuntimeError("FairAssetMetadataApplicationService requires a repository factory")
        return self._repository_factory(db)
