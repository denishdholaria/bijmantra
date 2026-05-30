"""FAIR asset metadata FastAPI adapter."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.domains.knowledge.capabilities.research_asset_core.adapters import (
    build_fair_metadata_application_service,
)
from app.domains.knowledge.capabilities.research_asset_core.adapters.api.access import (
    require_research_asset_api_access,
)
from app.domains.knowledge.capabilities.research_asset_core.application import (
    FairAssetNotFound,
    InvalidFairPersistentIdentifier,
    UnknownFairAssetType,
)
from app.domains.knowledge.capabilities.research_asset_core.schemas.fair_metadata import (
    FAIRAssetMetadataResponse,
    FAIRAssetMetadataUpsert,
)
from app.middleware.tenant_context import get_tenant_db
from app.models.core import User


router = APIRouter(prefix="/fair-metadata", tags=["FAIR Metadata"])
fair_metadata_service = build_fair_metadata_application_service()


def _to_response(metadata) -> FAIRAssetMetadataResponse:
    return FAIRAssetMetadataResponse.model_validate(metadata)


def _raise_http_error(error: ValueError) -> None:
    if isinstance(error, UnknownFairAssetType | InvalidFairPersistentIdentifier):
        raise HTTPException(status_code=400, detail=str(error)) from error
    if isinstance(error, FairAssetNotFound):
        raise HTTPException(status_code=404, detail=str(error)) from error
    raise HTTPException(status_code=400, detail=str(error)) from error


@router.put("/{asset_type}/{asset_db_id}", response_model=FAIRAssetMetadataResponse)
async def upsert_fair_metadata(
    asset_type: str,
    asset_db_id: str,
    payload: FAIRAssetMetadataUpsert,
    db: AsyncSession = Depends(get_tenant_db),
    current_user: User = Depends(get_current_user),
) -> FAIRAssetMetadataResponse:
    require_research_asset_api_access(
        current_user,
        required_permission="research_assets.register",
        required_data_scopes=("organization", "asset"),
    )
    try:
        metadata = await fair_metadata_service.upsert_asset_metadata(
            db,
            organization_id=current_user.organization_id,
            asset_type=asset_type,
            asset_db_id=asset_db_id,
            payload=payload,
        )
    except (UnknownFairAssetType, InvalidFairPersistentIdentifier, FairAssetNotFound) as error:
        _raise_http_error(error)
    return _to_response(metadata)


@router.get("/{asset_type}/{asset_db_id}", response_model=FAIRAssetMetadataResponse)
async def get_fair_metadata(
    asset_type: str,
    asset_db_id: str,
    db: AsyncSession = Depends(get_tenant_db),
    current_user: User = Depends(get_current_user),
) -> FAIRAssetMetadataResponse:
    require_research_asset_api_access(
        current_user,
        required_permission="research_assets.read",
        required_data_scopes=("organization",),
    )
    try:
        metadata = await fair_metadata_service.get_asset_metadata(
            db,
            organization_id=current_user.organization_id,
            asset_type=asset_type,
            asset_db_id=asset_db_id,
        )
    except UnknownFairAssetType as error:
        _raise_http_error(error)

    if metadata is None:
        raise HTTPException(status_code=404, detail="FAIR metadata not found")
    return _to_response(metadata)


@router.get("", response_model=list[FAIRAssetMetadataResponse])
async def list_fair_metadata(
    asset_type: str | None = Query(None),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_tenant_db),
    current_user: User = Depends(get_current_user),
) -> list[FAIRAssetMetadataResponse]:
    require_research_asset_api_access(
        current_user,
        required_permission="research_assets.read",
        required_data_scopes=("organization",),
    )
    try:
        records = await fair_metadata_service.list_asset_metadata(
            db,
            organization_id=current_user.organization_id,
            asset_type=asset_type,
            limit=limit,
            offset=offset,
        )
    except UnknownFairAssetType as error:
        _raise_http_error(error)
    return [_to_response(record) for record in records]
