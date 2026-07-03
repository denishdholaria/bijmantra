"""Federated agricultural asset registry FastAPI adapter."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.domains.knowledge.capabilities.research_asset_core.adapters import (
    build_federated_asset_registry_application_service,
)
from app.domains.knowledge.capabilities.research_asset_core.adapters.api.access import (
    require_research_asset_api_access,
)
from app.domains.knowledge.capabilities.research_asset_core.application import (
    DisabledFederatedConnector,
    FederatedAssetNotFound,
    FederatedConnectorNotFound,
    FederatedFairMetadataNotFound,
    UnsupportedFederatedAssetKind,
    UnsupportedFederatedConnectorType,
)
from app.domains.knowledge.capabilities.research_asset_core.schemas.federated_assets import (
    FederatedAssetAuditEventResponse,
    FederatedAssetConnectorCreate,
    FederatedAssetConnectorResponse,
    FederatedAssetDryRunRequest,
    FederatedAssetFairPromotionRequest,
    FederatedAssetRecordResponse,
    FederatedAssetRegistrationCreate,
    FederatedAssetSyncReceiptResponse,
)
from app.middleware.tenant_context import get_tenant_db
from app.models.core import User


router = APIRouter(prefix="/federated-assets", tags=["Federated Assets"])
federated_asset_registry_service = build_federated_asset_registry_application_service()


def _raise_http_error(error: ValueError) -> None:
    if isinstance(
        error,
        UnsupportedFederatedConnectorType
        | UnsupportedFederatedAssetKind
        | DisabledFederatedConnector,
    ):
        raise HTTPException(status_code=400, detail=str(error)) from error
    if isinstance(
        error,
        FederatedConnectorNotFound | FederatedAssetNotFound | FederatedFairMetadataNotFound,
    ):
        raise HTTPException(status_code=404, detail=str(error)) from error
    raise HTTPException(status_code=400, detail=str(error)) from error


@router.post("/connectors", response_model=FederatedAssetConnectorResponse)
async def create_federated_connector(
    payload: FederatedAssetConnectorCreate,
    db: AsyncSession = Depends(get_tenant_db),
    current_user: User = Depends(get_current_user),
) -> FederatedAssetConnectorResponse:
    await require_research_asset_api_access(
        current_user,
        db=db,
        required_permission="research_assets.register",
        required_data_scopes=("organization", "connector"),
    )
    try:
        connector = await federated_asset_registry_service.create_connector(
            db,
            organization_id=current_user.organization_id,
            actor_user_id=current_user.id,
            payload=payload,
        )
    except UnsupportedFederatedConnectorType as error:
        _raise_http_error(error)
    return FederatedAssetConnectorResponse.model_validate(connector)


@router.get("/connectors", response_model=list[FederatedAssetConnectorResponse])
async def list_federated_connectors(
    db: AsyncSession = Depends(get_tenant_db),
    current_user: User = Depends(get_current_user),
) -> list[FederatedAssetConnectorResponse]:
    await require_research_asset_api_access(
        current_user,
        db=db,
        required_permission="research_assets.read",
        required_data_scopes=("organization",),
    )
    connectors = await federated_asset_registry_service.list_connectors(
        db,
        organization_id=current_user.organization_id,
    )
    return [FederatedAssetConnectorResponse.model_validate(connector) for connector in connectors]


@router.post(
    "/connectors/{connector_key}/dry-run",
    response_model=FederatedAssetSyncReceiptResponse,
)
async def run_federated_connector_dry_run(
    connector_key: str,
    payload: FederatedAssetDryRunRequest,
    db: AsyncSession = Depends(get_tenant_db),
    current_user: User = Depends(get_current_user),
) -> FederatedAssetSyncReceiptResponse:
    await require_research_asset_api_access(
        current_user,
        db=db,
        required_permission="research_assets.register",
        required_data_scopes=("organization", "connector"),
    )
    try:
        receipt = await federated_asset_registry_service.run_connector_dry_run(
            db,
            organization_id=current_user.organization_id,
            connector_key=connector_key,
            actor_user_id=current_user.id,
            payload=payload,
        )
    except (FederatedConnectorNotFound, DisabledFederatedConnector) as error:
        _raise_http_error(error)
    return FederatedAssetSyncReceiptResponse.model_validate(receipt)


@router.post("/registry", response_model=FederatedAssetRecordResponse)
async def register_federated_asset(
    payload: FederatedAssetRegistrationCreate,
    db: AsyncSession = Depends(get_tenant_db),
    current_user: User = Depends(get_current_user),
) -> FederatedAssetRecordResponse:
    await require_research_asset_api_access(
        current_user,
        db=db,
        required_permission="research_assets.register",
        required_data_scopes=("organization", "asset", "connector"),
    )
    try:
        asset = await federated_asset_registry_service.register_asset(
            db,
            organization_id=current_user.organization_id,
            actor_user_id=current_user.id,
            payload=payload,
        )
    except (
        FederatedConnectorNotFound,
        UnsupportedFederatedAssetKind,
        FederatedFairMetadataNotFound,
        DisabledFederatedConnector,
    ) as error:
        _raise_http_error(error)
    return FederatedAssetRecordResponse.model_validate(asset)


@router.get("/registry", response_model=list[FederatedAssetRecordResponse])
async def list_federated_assets(
    connector_key: str | None = Query(None),
    asset_kind: str | None = Query(None),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_tenant_db),
    current_user: User = Depends(get_current_user),
) -> list[FederatedAssetRecordResponse]:
    await require_research_asset_api_access(
        current_user,
        db=db,
        required_permission="research_assets.read",
        required_data_scopes=("organization",),
    )
    try:
        assets = await federated_asset_registry_service.list_assets(
            db,
            organization_id=current_user.organization_id,
            connector_key=connector_key,
            asset_kind=asset_kind,
            limit=limit,
            offset=offset,
        )
    except (FederatedConnectorNotFound, UnsupportedFederatedAssetKind) as error:
        _raise_http_error(error)
    return [FederatedAssetRecordResponse.model_validate(asset) for asset in assets]


@router.post(
    "/registry/{registry_asset_id}/promote-fair",
    response_model=FederatedAssetRecordResponse,
)
async def promote_federated_asset_to_fair_metadata(
    registry_asset_id: str,
    payload: FederatedAssetFairPromotionRequest,
    db: AsyncSession = Depends(get_tenant_db),
    current_user: User = Depends(get_current_user),
) -> FederatedAssetRecordResponse:
    await require_research_asset_api_access(
        current_user,
        db=db,
        required_permission="research_assets.promote_fair",
        required_data_scopes=("organization", "asset", "provenance", "identifier"),
    )
    try:
        asset = await federated_asset_registry_service.promote_asset_to_fair_metadata(
            db,
            organization_id=current_user.organization_id,
            registry_asset_id=registry_asset_id,
            actor_user_id=current_user.id,
            payload=payload,
        )
    except ValueError as error:
        _raise_http_error(error)
    return FederatedAssetRecordResponse.model_validate(asset)


@router.get("/audit-events", response_model=list[FederatedAssetAuditEventResponse])
async def list_federated_asset_audit_events(
    target_type: str | None = Query(None),
    target_id: str | None = Query(None),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_tenant_db),
    current_user: User = Depends(get_current_user),
) -> list[FederatedAssetAuditEventResponse]:
    await require_research_asset_api_access(
        current_user,
        db=db,
        required_permission="research_assets.read",
        required_data_scopes=("organization",),
    )
    events = await federated_asset_registry_service.list_audit_events(
        db,
        organization_id=current_user.organization_id,
        target_type=target_type,
        target_id=target_id,
        limit=limit,
        offset=offset,
    )
    return [FederatedAssetAuditEventResponse.model_validate(event) for event in events]


@router.get("/receipts", response_model=list[FederatedAssetSyncReceiptResponse])
async def list_federated_sync_receipts(
    connector_key: str | None = Query(None),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_tenant_db),
    current_user: User = Depends(get_current_user),
) -> list[FederatedAssetSyncReceiptResponse]:
    await require_research_asset_api_access(
        current_user,
        db=db,
        required_permission="research_assets.read",
        required_data_scopes=("organization",),
    )
    try:
        receipts = await federated_asset_registry_service.list_sync_receipts(
            db,
            organization_id=current_user.organization_id,
            connector_key=connector_key,
            limit=limit,
            offset=offset,
        )
    except FederatedConnectorNotFound as error:
        _raise_http_error(error)
    return [FederatedAssetSyncReceiptResponse.model_validate(receipt) for receipt in receipts]
