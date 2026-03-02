"""
Integration Hub - API Routes

Endpoints for managing external integrations.
"""

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from .registry import INTEGRATION_REGISTRY, get_adapter, list_integrations


router = APIRouter(prefix="/integrations", tags=["Integrations"])


class IntegrationConfigRequest(BaseModel):
    """Request to configure an integration."""
    api_key: str | None = None
    api_secret: str | None = None
    base_url: str | None = None
    extra: dict[str, Any] = {}


class TestConnectionRequest(BaseModel):
    """Request to test an integration connection."""
    integration_id: str
    config: IntegrationConfigRequest


@router.get("/")
async def list_available_integrations():
    """List all available integrations."""
    return {
        "integrations": list_integrations(),
        "total": len(INTEGRATION_REGISTRY),
    }


@router.get("/{integration_id}")
async def get_integration_info(integration_id: str):
    """Get information about a specific integration."""
    if integration_id not in INTEGRATION_REGISTRY:
        raise HTTPException(status_code=404, detail="Integration not found")

    adapter_class = INTEGRATION_REGISTRY[integration_id]
    return {
        "id": integration_id,
        "name": getattr(adapter_class, 'name', integration_id),
        "description": getattr(adapter_class, 'description', ''),
        "required_config": getattr(adapter_class, 'required_config', []),
        "optional_config": getattr(adapter_class, 'optional_config', []),
    }


@router.post("/{integration_id}/test")
async def test_integration_connection(
    integration_id: str,
    config: IntegrationConfigRequest
):
    """Test connection to an integration."""
    adapter = get_adapter(integration_id, config.dict())
    if not adapter:
        raise HTTPException(status_code=404, detail="Integration not found")

    async with adapter:
        success = await adapter.test_connection()
        status = await adapter.get_status()

    return {
        "integration_id": integration_id,
        "success": success,
        "status": status.value,
        "error": adapter.get_last_error(),
    }


@router.post("/{integration_id}/sync")
async def sync_integration(
    integration_id: str,
    config: IntegrationConfigRequest,
    direction: str = "pull"
):
    """
    Sync data with an integration.

    Args:
        integration_id: ID of the integration
        direction: "pull" to import, "push" to export
    """
    adapter = get_adapter(integration_id, config.dict())
    if not adapter:
        raise HTTPException(status_code=404, detail="Integration not found")

    try:
        async with adapter:
            result = await adapter.sync(direction)
        return {
            "integration_id": integration_id,
            "direction": direction,
            "success": result.success,
            "records_synced": result.records_synced,
            "records_failed": result.records_failed,
            "errors": result.errors,
            "duration_ms": result.duration_ms,
        }
    except NotImplementedError:
        raise HTTPException(
            status_code=501,
            detail="This integration does not support sync"
        )
