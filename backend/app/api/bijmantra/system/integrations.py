"""
Integration Hub API
Manage external API integrations (NCBI, Earth Engine, OpenWeatherMap, ERPNext, Webhooks)
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user  # ADR-005: canonical auth path
from app.middleware.tenant_context import get_tenant_db
from app.models.core import User
from app.modules.interop.services.integration_hub_service import (
    IntegrationStatus,
    IntegrationType,
    UserIntegration,
    integration_hub,
)


router = APIRouter(prefix="/integrations", tags=["Integration Hub"], dependencies=[Depends(get_current_user)])


# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------

class IntegrationCreate(BaseModel):
    """Create a new integration"""
    integration_type: IntegrationType
    name: str = Field(..., min_length=1, max_length=100)
    credentials: dict = Field(..., description="API keys and secrets")


class IntegrationUpdate(BaseModel):
    """Update an integration"""
    name: str | None = None
    credentials: dict | None = None


class IntegrationResponse(BaseModel):
    """Integration response (credentials hidden)"""
    id: str
    user_id: str
    organization_id: str
    integration_type: IntegrationType
    name: str
    status: IntegrationStatus
    last_used: str | None = None
    last_error: str | None = None
    created_at: str
    updated_at: str


class TestConnectionResponse(BaseModel):
    """Connection test result"""
    success: bool
    message: str | None = None
    error: str | None = None


def _to_response(integration: UserIntegration) -> IntegrationResponse:
    """Convert UserIntegration to response (hide credentials)"""
    return IntegrationResponse(
        id=integration.id,
        user_id=integration.user_id,
        organization_id=integration.organization_id,
        integration_type=integration.integration_type,
        name=integration.name,
        status=integration.status,
        last_used=integration.last_used.isoformat() if integration.last_used else None,
        last_error=integration.last_error,
        created_at=integration.created_at.isoformat(),
        updated_at=integration.updated_at.isoformat(),
    )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("/available")
async def get_available_integrations():
    """Get list of available integration types"""
    return {"integrations": integration_hub.get_available_integrations()}


@router.get("/", response_model=list[IntegrationResponse])
async def list_integrations(
    current_user: User = Depends(get_current_user),
    organization_id: str | None = None,
    db: AsyncSession = Depends(get_tenant_db),
):
    """List all integrations for a user"""
    integrations = await integration_hub.get_user_integrations(
        db, str(current_user.id), organization_id
    )
    return [_to_response(i) for i in integrations]


@router.post("/", response_model=IntegrationResponse)
async def create_integration(
    data: IntegrationCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_db),
):
    """Create a new integration"""
    try:
        integration = await integration_hub.add_integration(
            db=db,
            user_id=str(current_user.id),
            organization_id=str(current_user.organization_id),
            integration_type=data.integration_type,
            name=data.name,
            credentials=data.credentials,
        )
        return _to_response(integration)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{integration_id}", response_model=IntegrationResponse)
async def get_integration(
    integration_id: str,
    db: AsyncSession = Depends(get_tenant_db),
):
    """Get a specific integration"""
    integration = await integration_hub.get_integration(db, integration_id)
    if not integration:
        raise HTTPException(status_code=404, detail="Integration not found")
    return _to_response(integration)


@router.patch("/{integration_id}", response_model=IntegrationResponse)
async def update_integration(
    integration_id: str,
    data: IntegrationUpdate,
    db: AsyncSession = Depends(get_tenant_db),
):
    """Update an integration"""
    integration = await integration_hub.update_integration(
        db=db,
        integration_id=integration_id,
        name=data.name,
        credentials=data.credentials,
    )
    if not integration:
        raise HTTPException(status_code=404, detail="Integration not found")
    return _to_response(integration)


@router.delete("/{integration_id}")
async def delete_integration(
    integration_id: str,
    db: AsyncSession = Depends(get_tenant_db),
):
    """Delete an integration"""
    if not await integration_hub.delete_integration(db, integration_id):
        raise HTTPException(status_code=404, detail="Integration not found")
    return {"message": "Integration deleted"}


@router.post("/{integration_id}/test", response_model=TestConnectionResponse)
async def test_integration(
    integration_id: str,
    db: AsyncSession = Depends(get_tenant_db),
):
    """Test connection to an integration"""
    result = await integration_hub.test_connection(db, integration_id)
    return TestConnectionResponse(**result)
