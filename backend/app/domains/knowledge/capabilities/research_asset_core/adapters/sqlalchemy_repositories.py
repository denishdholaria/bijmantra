"""SQLAlchemy adapters for ResearchAsset persistence ports."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.knowledge.capabilities.research_asset_core.ports.records import (
    FairAssetMetadataRecord,
    FairAssetMetadataWrite,
    FairAssetTargetRecord,
    FederatedAssetRegistryRecord,
    FederatedAssetRegistryWrite,
    FederatedConnectorRecord,
    FederatedConnectorWrite,
    FederatedSyncReceiptRecord,
    FederatedSyncReceiptWrite,
    ResearchAssetAuditEventRecord,
)
from app.domains.knowledge.capabilities.research_asset_core.ports.repositories import (
    FairAssetMetadataRepository,
    FederatedAssetRegistryRepository,
    ResearchAssetAuditLedger,
)
from app.models.audit import AuditLog
from app.models.core import Study, Trial
from app.models.fair_metadata import FairAssetMetadata
from app.models.federated_assets import (
    FederatedAssetConnector,
    FederatedAssetRecord,
    FederatedAssetSyncReceipt,
)
from app.models.germplasm import Germplasm
from app.models.phenotyping import ObservationVariable


@dataclass(frozen=True)
class AssetBinding:
    """Persistence mapping for a FAIR-addressable source asset."""

    model: type
    public_id_field: str
    title_field: str


DEFAULT_FAIR_ASSET_BINDINGS: dict[str, AssetBinding] = {
    "observation_variable": AssetBinding(
        ObservationVariable,
        "observation_variable_db_id",
        "observation_variable_name",
    ),
    "germplasm": AssetBinding(Germplasm, "germplasm_db_id", "germplasm_name"),
    "trial": AssetBinding(Trial, "trial_db_id", "trial_name"),
    "study": AssetBinding(Study, "study_db_id", "study_name"),
    "federated_asset": AssetBinding(
        FederatedAssetRecord,
        "registry_asset_id",
        "title",
    ),
}


def _list(value: Any) -> list[Any]:
    return list(value or [])


def _dict(value: Any) -> dict[str, Any]:
    return dict(value or {})


def _fair_metadata_record(record: FairAssetMetadata) -> FairAssetMetadataRecord:
    return FairAssetMetadataRecord(
        id=record.id,
        organization_id=record.organization_id,
        asset_type=record.asset_type,
        asset_db_id=record.asset_db_id,
        persistent_identifier=record.persistent_identifier,
        title=record.title,
        description=record.description,
        keywords=_list(record.keywords),
        access_rights=record.access_rights,
        license=record.license,
        data_standard=record.data_standard,
        ontology_terms=_list(record.ontology_terms),
        provenance=_dict(record.provenance),
        confidence=record.confidence,
        data_source=record.data_source,
        contributors=_list(record.contributors),
        funding_acknowledgements=_list(record.funding_acknowledgements),
        external_references=_list(record.external_references),
        evidence_refs=_list(record.evidence_refs),
        schema_version=record.schema_version,
        created_at=record.created_at,
        updated_at=record.updated_at,
    )


def _connector_record(record: FederatedAssetConnector) -> FederatedConnectorRecord:
    return FederatedConnectorRecord(
        id=record.id,
        organization_id=record.organization_id,
        connector_key=record.connector_key,
        connector_type=record.connector_type,
        display_name=record.display_name,
        endpoint_url=record.endpoint_url,
        description=record.description,
        enabled=record.enabled,
        auth_mode=record.auth_mode,
        capabilities=_list(record.capabilities),
        standards=_list(record.standards),
        governance=_dict(record.governance),
        schema_version=record.schema_version,
        created_at=record.created_at,
        updated_at=record.updated_at,
    )


def _asset_record(record: FederatedAssetRecord) -> FederatedAssetRegistryRecord:
    return FederatedAssetRegistryRecord(
        id=record.id,
        organization_id=record.organization_id,
        connector_id=record.connector_id,
        registry_asset_id=record.registry_asset_id,
        external_asset_id=record.external_asset_id,
        asset_kind=record.asset_kind,
        title=record.title,
        description=record.description,
        source_uri=record.source_uri,
        source_digest=record.source_digest,
        license=record.license,
        data_standard=record.data_standard,
        standards_mappings=_dict(record.standards_mappings),
        fair_metadata_id=record.fair_metadata_id,
        asset_metadata=_dict(record.asset_metadata),
        provenance=_dict(record.provenance),
        status=record.status,
        schema_version=record.schema_version,
        created_at=record.created_at,
        updated_at=record.updated_at,
    )


def _sync_receipt_record(record: FederatedAssetSyncReceipt) -> FederatedSyncReceiptRecord:
    return FederatedSyncReceiptRecord(
        id=record.id,
        organization_id=record.organization_id,
        connector_id=record.connector_id,
        receipt_id=record.receipt_id,
        run_mode=record.run_mode,
        status=record.status,
        source_digest=record.source_digest,
        discovered_asset_count=record.discovered_asset_count,
        registered_asset_count=record.registered_asset_count,
        skipped_asset_count=record.skipped_asset_count,
        error=_dict(record.error) if record.error is not None else None,
        manifest_snapshot=_dict(record.manifest_snapshot),
        started_at=record.started_at,
        completed_at=record.completed_at,
        schema_version=record.schema_version,
        created_at=record.created_at,
        updated_at=record.updated_at,
    )


def _audit_event_record(record: AuditLog) -> ResearchAssetAuditEventRecord:
    return ResearchAssetAuditEventRecord(
        id=record.id,
        organization_id=record.organization_id,
        user_id=record.user_id,
        action=record.action,
        target_type=record.target_type,
        target_id=record.target_id,
        changes=_dict(record.changes) if record.changes is not None else None,
        method=record.method,
        created_at=record.created_at,
    )


class SqlAlchemyFairAssetMetadataRepository(FairAssetMetadataRepository):
    """SQLAlchemy implementation of FAIR metadata persistence."""

    def __init__(
        self,
        db: AsyncSession,
        *,
        asset_bindings: Mapping[str, AssetBinding] | None = None,
    ) -> None:
        self._db = db
        self._asset_bindings = dict(asset_bindings or DEFAULT_FAIR_ASSET_BINDINGS)

    async def get_target_asset(
        self,
        *,
        organization_id: int,
        asset_type: str,
        asset_db_id: str,
    ) -> FairAssetTargetRecord | None:
        binding = self._asset_bindings[asset_type]
        public_id_column = getattr(binding.model, binding.public_id_field)
        result = await self._db.execute(
            select(binding.model).where(
                binding.model.organization_id == organization_id,
                public_id_column == asset_db_id,
            )
        )
        target_asset = result.scalar_one_or_none()
        if target_asset is None:
            return None
        title = getattr(target_asset, binding.title_field, None)
        return FairAssetTargetRecord(
            asset_type=asset_type,
            asset_db_id=str(getattr(target_asset, binding.public_id_field)),
            title=str(title or getattr(target_asset, binding.public_id_field)),
        )

    async def get_metadata(
        self,
        *,
        organization_id: int,
        asset_type: str,
        asset_db_id: str,
    ) -> FairAssetMetadataRecord | None:
        result = await self._db.execute(
            select(FairAssetMetadata).where(
                FairAssetMetadata.organization_id == organization_id,
                FairAssetMetadata.asset_type == asset_type,
                FairAssetMetadata.asset_db_id == asset_db_id,
            )
        )
        record = result.scalar_one_or_none()
        return _fair_metadata_record(record) if record else None

    async def get_metadata_by_id(
        self,
        *,
        organization_id: int,
        fair_metadata_id: int,
    ) -> FairAssetMetadataRecord | None:
        result = await self._db.execute(
            select(FairAssetMetadata).where(
                FairAssetMetadata.organization_id == organization_id,
                FairAssetMetadata.id == fair_metadata_id,
            )
        )
        record = result.scalar_one_or_none()
        return _fair_metadata_record(record) if record else None

    async def list_metadata(
        self,
        *,
        organization_id: int,
        asset_type: str | None,
        limit: int,
        offset: int,
    ) -> list[FairAssetMetadataRecord]:
        stmt = select(FairAssetMetadata).where(FairAssetMetadata.organization_id == organization_id)
        if asset_type:
            stmt = stmt.where(FairAssetMetadata.asset_type == asset_type)
        stmt = stmt.order_by(FairAssetMetadata.created_at.desc()).offset(offset).limit(limit)

        result = await self._db.execute(stmt)
        return [_fair_metadata_record(record) for record in result.scalars().all()]

    async def save_metadata(
        self,
        metadata: FairAssetMetadataWrite,
    ) -> FairAssetMetadataRecord:
        record = await self._metadata_for_write(metadata)
        record.persistent_identifier = metadata.persistent_identifier
        record.title = metadata.title
        record.description = metadata.description
        record.keywords = list(metadata.keywords)
        record.access_rights = metadata.access_rights
        record.license = metadata.license
        record.data_standard = metadata.data_standard
        record.ontology_terms = list(metadata.ontology_terms)
        record.provenance = dict(metadata.provenance)
        record.confidence = metadata.confidence
        record.data_source = metadata.data_source
        record.contributors = list(metadata.contributors)
        record.funding_acknowledgements = list(metadata.funding_acknowledgements)
        record.external_references = list(metadata.external_references)
        record.evidence_refs = list(metadata.evidence_refs)
        record.schema_version = metadata.schema_version

        await self._db.flush()
        await self._db.refresh(record)
        return _fair_metadata_record(record)

    async def _metadata_for_write(
        self,
        metadata: FairAssetMetadataWrite,
    ) -> FairAssetMetadata:
        record: FairAssetMetadata | None = None
        if metadata.metadata_id is not None:
            result = await self._db.execute(
                select(FairAssetMetadata).where(
                    FairAssetMetadata.organization_id == metadata.organization_id,
                    FairAssetMetadata.id == metadata.metadata_id,
                )
            )
            record = result.scalar_one_or_none()
        if record is None:
            result = await self._db.execute(
                select(FairAssetMetadata).where(
                    FairAssetMetadata.organization_id == metadata.organization_id,
                    FairAssetMetadata.asset_type == metadata.asset_type,
                    FairAssetMetadata.asset_db_id == metadata.asset_db_id,
                )
            )
            record = result.scalar_one_or_none()
        if record is None:
            record = FairAssetMetadata(
                organization_id=metadata.organization_id,
                asset_type=metadata.asset_type,
                asset_db_id=metadata.asset_db_id,
                persistent_identifier=metadata.persistent_identifier,
                title=metadata.title,
            )
            self._db.add(record)
        return record


class SqlAlchemyFederatedAssetRegistryRepository(FederatedAssetRegistryRepository):
    """SQLAlchemy implementation of federated asset registry persistence."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def get_connector_by_key(
        self,
        *,
        organization_id: int,
        connector_key: str,
    ) -> FederatedConnectorRecord | None:
        result = await self._db.execute(
            select(FederatedAssetConnector).where(
                FederatedAssetConnector.organization_id == organization_id,
                FederatedAssetConnector.connector_key == connector_key,
            )
        )
        record = result.scalar_one_or_none()
        return _connector_record(record) if record else None

    async def get_connector_by_id(
        self,
        *,
        organization_id: int,
        connector_id: int,
    ) -> FederatedConnectorRecord | None:
        result = await self._db.execute(
            select(FederatedAssetConnector).where(
                FederatedAssetConnector.organization_id == organization_id,
                FederatedAssetConnector.id == connector_id,
            )
        )
        record = result.scalar_one_or_none()
        return _connector_record(record) if record else None

    async def list_connectors(
        self,
        *,
        organization_id: int,
    ) -> list[FederatedConnectorRecord]:
        result = await self._db.execute(
            select(FederatedAssetConnector)
            .where(FederatedAssetConnector.organization_id == organization_id)
            .order_by(FederatedAssetConnector.created_at.desc())
        )
        return [_connector_record(record) for record in result.scalars().all()]

    async def get_asset_by_external_id(
        self,
        *,
        organization_id: int,
        connector_id: int,
        external_asset_id: str,
    ) -> FederatedAssetRegistryRecord | None:
        result = await self._db.execute(
            select(FederatedAssetRecord).where(
                FederatedAssetRecord.organization_id == organization_id,
                FederatedAssetRecord.connector_id == connector_id,
                FederatedAssetRecord.external_asset_id == external_asset_id,
            )
        )
        record = result.scalar_one_or_none()
        return _asset_record(record) if record else None

    async def get_asset_by_registry_id(
        self,
        *,
        organization_id: int,
        registry_asset_id: str,
    ) -> FederatedAssetRegistryRecord | None:
        result = await self._db.execute(
            select(FederatedAssetRecord).where(
                FederatedAssetRecord.organization_id == organization_id,
                FederatedAssetRecord.registry_asset_id == registry_asset_id,
            )
        )
        record = result.scalar_one_or_none()
        return _asset_record(record) if record else None

    async def list_assets(
        self,
        *,
        organization_id: int,
        connector_id: int | None,
        asset_kind: str | None,
        limit: int,
        offset: int,
    ) -> list[FederatedAssetRegistryRecord]:
        stmt = select(FederatedAssetRecord).where(
            FederatedAssetRecord.organization_id == organization_id
        )
        if connector_id is not None:
            stmt = stmt.where(FederatedAssetRecord.connector_id == connector_id)
        if asset_kind:
            stmt = stmt.where(FederatedAssetRecord.asset_kind == asset_kind)
        stmt = stmt.order_by(FederatedAssetRecord.created_at.desc()).offset(offset).limit(limit)

        result = await self._db.execute(stmt)
        return [_asset_record(record) for record in result.scalars().all()]

    async def list_sync_receipts(
        self,
        *,
        organization_id: int,
        connector_id: int | None,
        limit: int,
        offset: int,
    ) -> list[FederatedSyncReceiptRecord]:
        stmt = select(FederatedAssetSyncReceipt).where(
            FederatedAssetSyncReceipt.organization_id == organization_id
        )
        if connector_id is not None:
            stmt = stmt.where(FederatedAssetSyncReceipt.connector_id == connector_id)
        stmt = (
            stmt.order_by(FederatedAssetSyncReceipt.created_at.desc())
            .offset(offset)
            .limit(limit)
        )

        result = await self._db.execute(stmt)
        return [_sync_receipt_record(record) for record in result.scalars().all()]

    async def get_fair_metadata_by_id(
        self,
        *,
        organization_id: int,
        fair_metadata_id: int,
    ) -> FairAssetMetadataRecord | None:
        result = await self._db.execute(
            select(FairAssetMetadata).where(
                FairAssetMetadata.organization_id == organization_id,
                FairAssetMetadata.id == fair_metadata_id,
            )
        )
        record = result.scalar_one_or_none()
        return _fair_metadata_record(record) if record else None

    async def save_connector(
        self,
        connector: FederatedConnectorWrite,
    ) -> FederatedConnectorRecord:
        result = await self._db.execute(
            select(FederatedAssetConnector).where(
                FederatedAssetConnector.organization_id == connector.organization_id,
                FederatedAssetConnector.connector_key == connector.connector_key,
            )
        )
        record = result.scalar_one_or_none()
        if record is None:
            record = FederatedAssetConnector(
                organization_id=connector.organization_id,
                connector_key=connector.connector_key,
                connector_type=connector.connector_type,
                display_name=connector.display_name,
            )
            self._db.add(record)

        record.connector_type = connector.connector_type
        record.display_name = connector.display_name
        record.endpoint_url = connector.endpoint_url
        record.description = connector.description
        record.enabled = connector.enabled
        record.auth_mode = connector.auth_mode
        record.capabilities = list(connector.capabilities)
        record.standards = list(connector.standards)
        record.governance = dict(connector.governance)
        record.schema_version = connector.schema_version

        await self._db.flush()
        await self._db.refresh(record)
        return _connector_record(record)

    async def save_asset(
        self,
        asset: FederatedAssetRegistryWrite,
    ) -> FederatedAssetRegistryRecord:
        result = await self._db.execute(
            select(FederatedAssetRecord).where(
                FederatedAssetRecord.organization_id == asset.organization_id,
                FederatedAssetRecord.connector_id == asset.connector_id,
                FederatedAssetRecord.external_asset_id == asset.external_asset_id,
            )
        )
        record = result.scalar_one_or_none()
        if record is None:
            record = FederatedAssetRecord(
                organization_id=asset.organization_id,
                connector_id=asset.connector_id,
                registry_asset_id=asset.registry_asset_id,
                external_asset_id=asset.external_asset_id,
                asset_kind=asset.asset_kind,
                title=asset.title,
            )
            self._db.add(record)

        record.asset_kind = asset.asset_kind
        record.title = asset.title
        record.description = asset.description
        record.source_uri = asset.source_uri
        record.source_digest = asset.source_digest
        record.license = asset.license
        record.data_standard = asset.data_standard
        record.standards_mappings = dict(asset.standards_mappings)
        record.fair_metadata_id = asset.fair_metadata_id
        record.asset_metadata = dict(asset.asset_metadata)
        record.provenance = dict(asset.provenance)
        record.status = asset.status
        record.schema_version = asset.schema_version

        await self._db.flush()
        await self._db.refresh(record)
        return _asset_record(record)

    async def create_sync_receipt(
        self,
        receipt: FederatedSyncReceiptWrite,
    ) -> FederatedSyncReceiptRecord:
        record = FederatedAssetSyncReceipt(
            organization_id=receipt.organization_id,
            connector_id=receipt.connector_id,
            receipt_id=receipt.receipt_id,
            run_mode=receipt.run_mode,
            status=receipt.status,
            source_digest=receipt.source_digest,
            discovered_asset_count=receipt.discovered_asset_count,
            registered_asset_count=receipt.registered_asset_count,
            skipped_asset_count=receipt.skipped_asset_count,
            error=receipt.error,
            manifest_snapshot=dict(receipt.manifest_snapshot),
            started_at=receipt.started_at,
            completed_at=receipt.completed_at,
            schema_version=receipt.schema_version,
        )
        self._db.add(record)
        await self._db.flush()
        await self._db.refresh(record)
        return _sync_receipt_record(record)

    async def set_asset_fair_metadata(
        self,
        *,
        organization_id: int,
        registry_asset_id: str,
        fair_metadata_id: int,
    ) -> FederatedAssetRegistryRecord | None:
        result = await self._db.execute(
            select(FederatedAssetRecord).where(
                FederatedAssetRecord.organization_id == organization_id,
                FederatedAssetRecord.registry_asset_id == registry_asset_id,
            )
        )
        record = result.scalar_one_or_none()
        if record is None:
            return None
        record.fair_metadata_id = fair_metadata_id
        await self._db.flush()
        await self._db.refresh(record)
        return _asset_record(record)


class SqlAlchemyResearchAssetAuditLedger(ResearchAssetAuditLedger):
    """SQLAlchemy implementation of the immutable ResearchAsset audit ledger."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def write_event(
        self,
        *,
        organization_id: int,
        actor_user_id: int | None,
        action: str,
        target_type: str,
        target_id: str | None,
        changes: dict[str, Any],
    ) -> None:
        self._db.add(
            AuditLog(
                organization_id=organization_id,
                user_id=actor_user_id,
                action=action,
                target_type=target_type,
                target_id=target_id,
                changes=changes,
                method="POST",
            )
        )
        await self._db.flush()

    async def list_events(
        self,
        *,
        organization_id: int,
        actions: Iterable[str],
        target_type: str | None,
        target_id: str | None,
        limit: int,
        offset: int,
    ) -> list[ResearchAssetAuditEventRecord]:
        stmt = select(AuditLog).where(
            AuditLog.organization_id == organization_id,
            AuditLog.action.in_(tuple(actions)),
        )
        if target_type:
            stmt = stmt.where(AuditLog.target_type == target_type)
        if target_id:
            stmt = stmt.where(AuditLog.target_id == target_id)
        stmt = stmt.order_by(AuditLog.created_at.desc(), AuditLog.id.desc()).offset(offset).limit(
            limit
        )

        result = await self._db.execute(stmt)
        return [_audit_event_record(record) for record in result.scalars().all()]
