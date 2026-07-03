"""Application facade for the federated agricultural asset registry."""

import uuid
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any

from app.domains.knowledge.capabilities.research_asset_core.application.fair_metadata_service import (
    FairAssetMetadataApplicationService,
)
from app.domains.knowledge.capabilities.research_asset_core.application.fair_promotion import (
    build_fair_promotion_payload,
)
from app.domains.knowledge.capabilities.research_asset_core.application.registration import (
    build_federated_asset_registration_plan,
)
from app.domains.knowledge.capabilities.research_asset_core.domain import (
    policies as research_asset_policies,
)
from app.domains.knowledge.capabilities.research_asset_core.ports import (
    FairAssetMetadataRecord,
    FederatedAssetRegistryRecord,
    FederatedAssetRegistryRepository,
    FederatedAssetRegistryWrite,
    FederatedConnectorRecord,
    FederatedConnectorWrite,
    FederatedSyncReceiptRecord,
    FederatedSyncReceiptWrite,
    ResearchAssetAuditEventRecord,
    ResearchAssetAuditLedger,
)
from app.domains.knowledge.capabilities.research_asset_core.schemas import (
    FairPromotionCommand,
    FederatedAssetPromotionSource,
    FederatedAssetRegistrationCommand,
    FederatedConnectorReference,
)
from app.domains.knowledge.capabilities.research_asset_core.schemas.fair_metadata import (
    FAIRAssetMetadataUpsert,
)
from app.domains.knowledge.capabilities.research_asset_core.schemas.federated_assets import (
    FederatedAssetConnectorCreate,
    FederatedAssetDryRunRequest,
    FederatedAssetFairPromotionRequest,
    FederatedAssetRegistrationCreate,
)


FEDERATED_AUDIT_ACTIONS = research_asset_policies.FEDERATED_AUDIT_ACTIONS
UnsupportedFederatedAssetKind = research_asset_policies.UnsupportedFederatedAssetKind
UnsupportedFederatedConnectorType = research_asset_policies.UnsupportedFederatedConnectorType


class FederatedConnectorNotFound(ValueError):
    """Raised when a connector is not available in the current organization."""


class FederatedAssetNotFound(ValueError):
    """Raised when a registry asset is not available in the current organization."""


class FederatedFairMetadataNotFound(ValueError):
    """Raised when a FAIR metadata link crosses organizations or does not exist."""


class DisabledFederatedConnector(ValueError):
    """Raised when an operation requires an enabled connector."""


RegistryRepositoryFactory = Callable[[Any], FederatedAssetRegistryRepository]
AuditLedgerFactory = Callable[[Any], ResearchAssetAuditLedger]


class FederatedAssetRegistryApplicationService:
    """Manage connector manifests, metadata-only asset rows, and dry-run receipts."""

    def __init__(
        self,
        fair_metadata_service: FairAssetMetadataApplicationService | None = None,
        *,
        registry_repository_factory: RegistryRepositoryFactory | None = None,
        audit_ledger_factory: AuditLedgerFactory | None = None,
    ) -> None:
        self.fair_metadata_service = (
            fair_metadata_service or FairAssetMetadataApplicationService()
        )
        self._registry_repository_factory = registry_repository_factory
        self._audit_ledger_factory = audit_ledger_factory

    def normalize_connector_key(self, connector_key: str) -> str:
        return research_asset_policies.normalize_connector_key(connector_key)

    def require_supported_connector_type(self, connector_type: str) -> str:
        return research_asset_policies.require_supported_connector_type(connector_type)

    def require_supported_asset_kind(self, asset_kind: str) -> str:
        return research_asset_policies.require_supported_federated_asset_kind(asset_kind)

    async def create_connector(
        self,
        db: Any,
        *,
        organization_id: int,
        actor_user_id: int | None = None,
        payload: FederatedAssetConnectorCreate,
    ) -> FederatedConnectorRecord:
        connector_key = self.normalize_connector_key(payload.connector_key)
        connector_type = self.require_supported_connector_type(payload.connector_type)
        repository = self._registry_repository(db)

        connector = await repository.save_connector(
            FederatedConnectorWrite(
                organization_id=organization_id,
                connector_key=connector_key,
                connector_type=connector_type,
                display_name=payload.display_name,
                endpoint_url=payload.endpoint_url,
                description=payload.description,
                enabled=payload.enabled,
                auth_mode=payload.auth_mode or "none",
                capabilities=list(payload.capabilities or []),
                standards=list(payload.standards or []),
                governance=dict(payload.governance or {}),
                schema_version="federated_connector.v1",
            )
        )
        await self._write_audit_event(
            db,
            organization_id=organization_id,
            actor_user_id=actor_user_id,
            action=research_asset_policies.FEDERATED_CONNECTOR_UPSERT_ACTION,
            target_type="federated_asset_connector",
            target_id=connector.connector_key,
            changes={
                "connectorKey": connector.connector_key,
                "connectorType": connector.connector_type,
                "displayName": connector.display_name,
                "enabled": connector.enabled,
                "authMode": connector.auth_mode,
                "standards": list(connector.standards or []),
                "capabilities": list(connector.capabilities or []),
            },
        )
        return connector

    async def get_connector(
        self,
        db: Any,
        *,
        organization_id: int,
        connector_key: str,
    ) -> FederatedConnectorRecord | None:
        return await self._registry_repository(db).get_connector_by_key(
            organization_id=organization_id,
            connector_key=self.normalize_connector_key(connector_key),
        )

    async def list_connectors(
        self,
        db: Any,
        *,
        organization_id: int,
    ) -> list[FederatedConnectorRecord]:
        return await self._registry_repository(db).list_connectors(
            organization_id=organization_id,
        )

    async def run_connector_dry_run(
        self,
        db: Any,
        *,
        organization_id: int,
        connector_key: str,
        actor_user_id: int | None = None,
        payload: FederatedAssetDryRunRequest,
    ) -> FederatedSyncReceiptRecord:
        connector = await self._require_connector(
            db,
            organization_id=organization_id,
            connector_key=connector_key,
            require_enabled=True,
        )
        manifest_snapshot = {
            "connector": self._connector_snapshot(connector),
            "candidateAssets": payload.candidate_assets,
            "dryRunNote": payload.dry_run_note,
            "policy": {
                "rawDataImport": False,
                "registryWrites": False,
                "domainWrites": False,
            },
        }
        digest = research_asset_policies.sha256_digest(manifest_snapshot)
        discovered_count = len(payload.candidate_assets)
        repository = self._registry_repository(db)
        receipt = await repository.create_sync_receipt(
            FederatedSyncReceiptWrite(
                organization_id=organization_id,
                connector_id=connector.id,
                receipt_id=f"fed-sync-{uuid.uuid4().hex[:16]}",
                run_mode="dry_run",
                status="dry_run_completed",
                source_digest=digest,
                discovered_asset_count=discovered_count,
                registered_asset_count=0,
                skipped_asset_count=discovered_count,
                error=None,
                manifest_snapshot=manifest_snapshot,
                started_at=datetime.now(UTC),
                completed_at=datetime.now(UTC),
                schema_version="federated_sync_receipt.v1",
            )
        )
        await self._write_audit_event(
            db,
            organization_id=organization_id,
            actor_user_id=actor_user_id,
            action=research_asset_policies.FEDERATED_CONNECTOR_DRY_RUN_ACTION,
            target_type="federated_asset_connector",
            target_id=connector.connector_key,
            changes={
                "connectorKey": connector.connector_key,
                "receiptId": receipt.receipt_id,
                "sourceDigest": receipt.source_digest,
                "discoveredAssetCount": receipt.discovered_asset_count,
                "registeredAssetCount": receipt.registered_asset_count,
                "skippedAssetCount": receipt.skipped_asset_count,
                "policy": manifest_snapshot["policy"],
            },
        )
        return receipt

    async def register_asset(
        self,
        db: Any,
        *,
        organization_id: int,
        actor_user_id: int | None = None,
        payload: FederatedAssetRegistrationCreate,
    ) -> FederatedAssetRegistryRecord:
        connector = await self._require_connector(
            db,
            organization_id=organization_id,
            connector_key=payload.connector_key,
            require_enabled=True,
        )
        registration_plan = build_federated_asset_registration_plan(
            FederatedAssetRegistrationCommand(
                connector_key=connector.connector_key,
                external_asset_id=payload.external_asset_id,
                asset_kind=payload.asset_kind,
                title=payload.title,
                source_uri=payload.source_uri,
                source_digest=payload.source_digest,
                license=payload.license,
                data_standard=payload.data_standard,
                standards_mappings=dict(payload.standards_mappings or {}),
                metadata=dict(payload.metadata or {}),
                provenance=dict(payload.provenance or {}),
            )
        )
        if payload.fair_metadata_id is not None:
            await self._require_fair_metadata(
                db,
                organization_id=organization_id,
                fair_metadata_id=payload.fair_metadata_id,
            )

        repository = self._registry_repository(db)
        asset = await repository.get_asset_by_external_id(
            organization_id=organization_id,
            connector_id=connector.id,
            external_asset_id=registration_plan.external_asset_id,
        )

        asset = await repository.save_asset(
            FederatedAssetRegistryWrite(
                organization_id=organization_id,
                connector_id=connector.id,
                registry_asset_id=(
                    asset.registry_asset_id if asset else registration_plan.registry_asset_id
                ),
                external_asset_id=registration_plan.external_asset_id,
                asset_kind=registration_plan.asset_kind,
                title=payload.title,
                description=payload.description,
                source_uri=payload.source_uri,
                source_digest=registration_plan.source_digest,
                license=payload.license,
                data_standard=payload.data_standard,
                standards_mappings=dict(payload.standards_mappings or {}),
                fair_metadata_id=payload.fair_metadata_id,
                asset_metadata=dict(payload.metadata or {}),
                provenance=dict(payload.provenance or {}),
                status=payload.status or "active",
                schema_version="federated_asset_record.v1",
            )
        )
        await self._write_audit_event(
            db,
            organization_id=organization_id,
            actor_user_id=actor_user_id,
            action=research_asset_policies.FEDERATED_ASSET_REGISTER_ACTION,
            target_type="federated_asset_record",
            target_id=asset.registry_asset_id,
            changes={
                "connectorKey": connector.connector_key,
                "registryAssetId": asset.registry_asset_id,
                "externalAssetId": asset.external_asset_id,
                "assetKind": asset.asset_kind,
                "sourceDigest": asset.source_digest,
                "fairMetadataId": asset.fair_metadata_id,
                "status": asset.status,
            },
        )
        return asset

    async def list_assets(
        self,
        db: Any,
        *,
        organization_id: int,
        connector_key: str | None = None,
        asset_kind: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[FederatedAssetRegistryRecord]:
        connector_id: int | None = None
        if connector_key:
            connector = await self._require_connector(
                db,
                organization_id=organization_id,
                connector_key=connector_key,
                require_enabled=False,
            )
            connector_id = connector.id
        normalized_asset_kind = self.require_supported_asset_kind(asset_kind) if asset_kind else None
        return await self._registry_repository(db).list_assets(
            organization_id=organization_id,
            connector_id=connector_id,
            asset_kind=normalized_asset_kind,
            limit=limit,
            offset=offset,
        )

    async def list_sync_receipts(
        self,
        db: Any,
        *,
        organization_id: int,
        connector_key: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[FederatedSyncReceiptRecord]:
        connector_id: int | None = None
        if connector_key:
            connector = await self._require_connector(
                db,
                organization_id=organization_id,
                connector_key=connector_key,
                require_enabled=False,
            )
            connector_id = connector.id
        return await self._registry_repository(db).list_sync_receipts(
            organization_id=organization_id,
            connector_id=connector_id,
            limit=limit,
            offset=offset,
        )

    async def promote_asset_to_fair_metadata(
        self,
        db: Any,
        *,
        organization_id: int,
        registry_asset_id: str,
        actor_user_id: int | None = None,
        payload: FederatedAssetFairPromotionRequest,
    ) -> FederatedAssetRegistryRecord:
        asset = await self._require_asset(
            db,
            organization_id=organization_id,
            registry_asset_id=registry_asset_id,
        )
        repository = self._registry_repository(db)
        connector = await repository.get_connector_by_id(
            organization_id=organization_id,
            connector_id=asset.connector_id,
        )
        fair_payload = self._build_fair_promotion_payload(
            asset=asset,
            connector=connector,
            payload=payload,
        )
        fair_metadata = await self.fair_metadata_service.upsert_asset_metadata(
            db,
            organization_id=organization_id,
            asset_type="federated_asset",
            asset_db_id=asset.registry_asset_id,
            payload=fair_payload,
        )

        linked_asset = await repository.set_asset_fair_metadata(
            organization_id=organization_id,
            registry_asset_id=asset.registry_asset_id,
            fair_metadata_id=fair_metadata.id,
        )
        if linked_asset is None:
            raise FederatedAssetNotFound(
                f"Federated asset '{registry_asset_id}' was not found in this organization"
            )
        await self._write_audit_event(
            db,
            organization_id=organization_id,
            actor_user_id=actor_user_id,
            action=research_asset_policies.FEDERATED_ASSET_PROMOTE_FAIR_ACTION,
            target_type="federated_asset_record",
            target_id=asset.registry_asset_id,
            changes={
                "registryAssetId": asset.registry_asset_id,
                "externalAssetId": asset.external_asset_id,
                "fairMetadataId": fair_metadata.id,
                "persistentIdentifier": fair_metadata.persistent_identifier,
                "assetType": fair_metadata.asset_type,
                "assetDbId": fair_metadata.asset_db_id,
            },
        )
        return linked_asset

    async def list_audit_events(
        self,
        db: Any,
        *,
        organization_id: int,
        target_type: str | None = None,
        target_id: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[ResearchAssetAuditEventRecord]:
        return await self._audit_ledger(db).list_events(
            organization_id=organization_id,
            actions=FEDERATED_AUDIT_ACTIONS,
            target_type=target_type,
            target_id=target_id,
            limit=limit,
            offset=offset,
        )

    async def _require_connector(
        self,
        db: Any,
        *,
        organization_id: int,
        connector_key: str,
        require_enabled: bool,
    ) -> FederatedConnectorRecord:
        connector = await self.get_connector(
            db,
            organization_id=organization_id,
            connector_key=connector_key,
        )
        if connector is None:
            raise FederatedConnectorNotFound(
                f"Federated connector '{connector_key}' was not found in this organization"
            )
        if require_enabled and not connector.enabled:
            raise DisabledFederatedConnector(
                f"Federated connector '{connector.connector_key}' is disabled"
            )
        return connector

    async def _require_fair_metadata(
        self,
        db: Any,
        *,
        organization_id: int,
        fair_metadata_id: int,
    ) -> FairAssetMetadataRecord:
        metadata = await self._registry_repository(db).get_fair_metadata_by_id(
            organization_id=organization_id,
            fair_metadata_id=fair_metadata_id,
        )
        if metadata is None:
            raise FederatedFairMetadataNotFound(
                f"FAIR metadata '{fair_metadata_id}' was not found in this organization"
            )
        return metadata

    async def _write_audit_event(
        self,
        db: Any,
        *,
        organization_id: int,
        actor_user_id: int | None,
        action: str,
        target_type: str,
        target_id: str | None,
        changes: dict[str, Any],
    ) -> None:
        await self._audit_ledger(db).write_event(
            organization_id=organization_id,
            actor_user_id=actor_user_id,
            action=action,
            target_type=target_type,
            target_id=target_id,
            changes=changes,
        )

    async def _require_asset(
        self,
        db: Any,
        *,
        organization_id: int,
        registry_asset_id: str,
    ) -> FederatedAssetRegistryRecord:
        asset = await self._registry_repository(db).get_asset_by_registry_id(
            organization_id=organization_id,
            registry_asset_id=registry_asset_id,
        )
        if asset is None:
            raise FederatedAssetNotFound(
                f"Federated asset '{registry_asset_id}' was not found in this organization"
            )
        return asset

    def _build_fair_promotion_payload(
        self,
        *,
        asset: FederatedAssetRegistryRecord,
        connector: FederatedConnectorRecord | None,
        payload: FederatedAssetFairPromotionRequest,
    ) -> FAIRAssetMetadataUpsert:
        fair_payload = build_fair_promotion_payload(
            asset=FederatedAssetPromotionSource(
                registry_asset_id=asset.registry_asset_id,
                external_asset_id=asset.external_asset_id,
                asset_kind=asset.asset_kind,
                title=asset.title,
                description=asset.description,
                source_uri=asset.source_uri,
                source_digest=asset.source_digest,
                license=asset.license,
                data_standard=asset.data_standard,
                provenance=dict(asset.provenance or {}),
            ),
            connector=(
                FederatedConnectorReference(
                    connector_key=connector.connector_key,
                    display_name=connector.display_name,
                )
                if connector
                else None
            ),
            command=FairPromotionCommand(
                fields_set=frozenset(payload.model_fields_set),
                persistent_identifier=payload.persistent_identifier,
                title=payload.title,
                description=payload.description,
                keywords=tuple(payload.keywords or ()),
                access_rights=payload.access_rights,
                license=payload.license,
                data_standard=payload.data_standard,
                ontology_terms=tuple(payload.ontology_terms or ()),
                provenance=dict(payload.provenance or {}),
                confidence=payload.confidence,
                data_source=payload.data_source,
                contributors=tuple(payload.contributors or ()),
                funding_acknowledgements=tuple(payload.funding_acknowledgements or ()),
                external_references=tuple(payload.external_references or ()),
                evidence_refs=tuple(payload.evidence_refs or ()),
            ),
        )
        return FAIRAssetMetadataUpsert(**fair_payload)

    def _connector_snapshot(self, connector: FederatedConnectorRecord) -> dict[str, Any]:
        return {
            "connectorKey": connector.connector_key,
            "connectorType": connector.connector_type,
            "displayName": connector.display_name,
            "endpointUrl": connector.endpoint_url,
            "capabilities": list(connector.capabilities or []),
            "standards": list(connector.standards or []),
            "authMode": connector.auth_mode,
            "governance": dict(connector.governance or {}),
        }

    def extract_candidate_identity(self, candidate_asset: dict[str, Any]) -> tuple[str | None, str | None]:
        return research_asset_policies.extract_candidate_identity(candidate_asset)

    def _registry_repository(
        self, db: Any
    ) -> FederatedAssetRegistryRepository:
        if self._registry_repository_factory is None:
            raise RuntimeError(
                "FederatedAssetRegistryApplicationService requires a registry repository factory"
            )
        return self._registry_repository_factory(db)

    def _audit_ledger(self, db: Any) -> ResearchAssetAuditLedger:
        if self._audit_ledger_factory is None:
            raise RuntimeError(
                "FederatedAssetRegistryApplicationService requires an audit ledger factory"
            )
        return self._audit_ledger_factory(db)
