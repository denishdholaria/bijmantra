"""
Integration Hub Service
Manage external API integrations and user API keys

Supported Integrations:
- NCBI (GenBank, BLAST, Entrez)
- Google Earth Engine
- OpenWeatherMap
- ERPNext
- Custom webhooks
"""

import hashlib
import json
import os
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel
from sqlalchemy import Column, DateTime, ForeignKey, Integer, LargeBinary, String, Text, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.http_tracing import create_traced_async_client
from app.models.base import BaseModel as DBBaseModel


# ---------------------------------------------------------------------------
# SQLAlchemy ORM model
# ---------------------------------------------------------------------------

class Integration(DBBaseModel):
    """SQLAlchemy model for the integrations table."""

    __tablename__ = "integrations"

    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    integration_type = Column(String(50), nullable=False)
    name = Column(String(255), nullable=False)
    # bytea — stores pgp_sym_encrypt() output
    credentials_encrypted = Column(LargeBinary, nullable=True)
    status = Column(String(20), default="pending")
    last_used = Column(DateTime(timezone=True), nullable=True)
    last_error = Column(Text, nullable=True)


# ---------------------------------------------------------------------------
# Enums and config types
# ---------------------------------------------------------------------------

class IntegrationType(StrEnum):
    """Supported integration types"""
    NCBI = "ncbi"
    EARTH_ENGINE = "earth_engine"
    OPENWEATHER = "openweather"
    ERPNEXT = "erpnext"
    WEBHOOK = "webhook"
    CUSTOM = "custom"


class IntegrationStatus(StrEnum):
    """Integration connection status"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    PENDING = "pending"


@dataclass
class IntegrationConfig:
    """Configuration for an integration"""
    type: IntegrationType
    name: str
    description: str
    required_fields: list[str]
    optional_fields: list[str]
    docs_url: str
    icon: str


# Available integrations
INTEGRATIONS: dict[IntegrationType, IntegrationConfig] = {
    IntegrationType.NCBI: IntegrationConfig(
        type=IntegrationType.NCBI,
        name="NCBI",
        description="National Center for Biotechnology Information - GenBank, BLAST, Entrez",
        required_fields=["api_key", "email"],
        optional_fields=["tool_name"],
        docs_url="https://www.ncbi.nlm.nih.gov/books/NBK25497/",
        icon="🧬"
    ),
    IntegrationType.EARTH_ENGINE: IntegrationConfig(
        type=IntegrationType.EARTH_ENGINE,
        name="Google Earth Engine",
        description="Satellite imagery and geospatial analysis",
        required_fields=["service_account_key"],
        optional_fields=["project_id"],
        docs_url="https://developers.google.com/earth-engine",
        icon="🌍"
    ),
    IntegrationType.OPENWEATHER: IntegrationConfig(
        type=IntegrationType.OPENWEATHER,
        name="OpenWeatherMap",
        description="Weather data and forecasts",
        required_fields=["api_key"],
        optional_fields=[],
        docs_url="https://openweathermap.org/api",
        icon="🌤️"
    ),
    IntegrationType.ERPNEXT: IntegrationConfig(
        type=IntegrationType.ERPNEXT,
        name="ERPNext",
        description="Enterprise resource planning integration",
        required_fields=["api_key", "api_secret", "base_url"],
        optional_fields=[],
        docs_url="https://frappeframework.com/docs",
        icon="📊"
    ),
    IntegrationType.WEBHOOK: IntegrationConfig(
        type=IntegrationType.WEBHOOK,
        name="Webhook",
        description="Custom webhook for external notifications",
        required_fields=["url"],
        optional_fields=["secret", "headers"],
        docs_url="",
        icon="🔗"
    ),
}


# ---------------------------------------------------------------------------
# Pydantic response model (kept for API serialisation)
# ---------------------------------------------------------------------------

class UserIntegration(BaseModel):
    """User's integration configuration — used for API response serialisation."""
    id: str
    user_id: str
    organization_id: str
    integration_type: IntegrationType
    name: str
    status: IntegrationStatus
    last_used: datetime | None = None
    last_error: str | None = None
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------

class IntegrationHubService:
    """
    Service for managing external integrations.

    Credentials are encrypted at the database level using pgcrypto
    ``pgp_sym_encrypt()`` / ``pgp_sym_decrypt()``.  The encryption key is
    injected as the PostgreSQL session variable ``app.encryption_key`` by the
    SQLAlchemy connection event listener in ``app.core.database``.

    All mutating methods require an ``AsyncSession`` parameter so they can
    participate in the caller's unit-of-work.
    """

    # ------------------------------------------------------------------
    # pgcrypto helpers
    # ------------------------------------------------------------------

    async def _encrypt_credentials(
        self, db: AsyncSession, credentials: dict[str, str]
    ) -> bytes:
        """Encrypt a credentials dict as JSON using pgcrypto pgp_sym_encrypt."""
        credentials_json = json.dumps(credentials)
        try:
            result = await db.execute(
                text(
                    "SELECT pgp_sym_encrypt(:data, current_setting('app.encryption_key'))"
                ),
                {"data": credentials_json},
            )
        except Exception as exc:
            raise RuntimeError(
                "pgcrypto encryption failed — ensure INTEGRATION_ENCRYPTION_KEY "
                "is set and the pgcrypto extension is enabled."
            ) from exc
        return result.scalar_one()

    async def _decrypt_credentials(
        self, db: AsyncSession, encrypted: bytes
    ) -> dict[str, str]:
        """Decrypt credentials using pgcrypto pgp_sym_decrypt."""
        try:
            result = await db.execute(
                text(
                    "SELECT pgp_sym_decrypt(:data, current_setting('app.encryption_key'))"
                ),
                {"data": encrypted},
            )
        except Exception as exc:
            raise RuntimeError(
                "pgcrypto decryption failed — ensure INTEGRATION_ENCRYPTION_KEY "
                "is set and matches the key used during encryption."
            ) from exc
        decrypted_json = result.scalar_one()
        return json.loads(decrypted_json)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _generate_id(self, user_id: str, integration_type: str) -> str:
        """Generate a short unique integration ID (used as the string id in responses)."""
        hash_input = f"{user_id}:{integration_type}:{datetime.now(UTC).isoformat()}"
        return hashlib.sha256(hash_input.encode()).hexdigest()[:16]

    def _row_to_pydantic(self, row: Integration) -> UserIntegration:
        """Convert an ORM row to the Pydantic response model."""
        return UserIntegration(
            id=str(row.id),
            user_id=str(row.user_id),
            organization_id=str(row.organization_id),
            integration_type=IntegrationType(row.integration_type),
            name=row.name,
            status=IntegrationStatus(row.status or "pending"),
            last_used=row.last_used,
            last_error=row.last_error,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )

    # ------------------------------------------------------------------
    # Read-only helpers (no DB needed)
    # ------------------------------------------------------------------

    def get_available_integrations(self) -> list[dict[str, Any]]:
        """Get list of available integrations (static config, no DB needed)."""
        return [
            {
                "type": config.type.value,
                "name": config.name,
                "description": config.description,
                "required_fields": config.required_fields,
                "optional_fields": config.optional_fields,
                "docs_url": config.docs_url,
                "icon": config.icon,
            }
            for config in INTEGRATIONS.values()
        ]

    # ------------------------------------------------------------------
    # DB-backed CRUD
    # ------------------------------------------------------------------

    async def add_integration(
        self,
        db: AsyncSession,
        user_id: str,
        organization_id: str,
        integration_type: IntegrationType,
        name: str,
        credentials: dict[str, str],
    ) -> UserIntegration:
        """Add a new integration for a user, persisting to the database."""

        if integration_type not in INTEGRATIONS:
            raise ValueError(f"Unknown integration type: {integration_type}")

        config = INTEGRATIONS[integration_type]
        for field in config.required_fields:
            if field not in credentials:
                raise ValueError(f"Missing required field: {field}")

        encrypted = await self._encrypt_credentials(db, credentials)

        row = Integration(
            organization_id=int(organization_id),
            user_id=int(user_id),
            integration_type=integration_type.value,
            name=name,
            credentials_encrypted=encrypted,
            status=IntegrationStatus.PENDING.value,
        )
        db.add(row)
        await db.flush()  # populate row.id / timestamps without committing
        await db.refresh(row)
        return self._row_to_pydantic(row)

    async def get_user_integrations(
        self,
        db: AsyncSession,
        user_id: str,
        organization_id: str | None = None,
    ) -> list[UserIntegration]:
        """Get all integrations for a user from the database."""
        stmt = select(Integration).where(Integration.user_id == int(user_id))
        if organization_id is not None:
            stmt = stmt.where(Integration.organization_id == int(organization_id))
        result = await db.execute(stmt)
        rows = result.scalars().all()
        return [self._row_to_pydantic(r) for r in rows]

    async def get_integration(
        self, db: AsyncSession, integration_id: str
    ) -> UserIntegration | None:
        """Get a specific integration by ID."""
        row = await db.get(Integration, int(integration_id))
        if row is None:
            return None
        return self._row_to_pydantic(row)

    async def get_decrypted_credentials(
        self, db: AsyncSession, integration_id: str
    ) -> dict[str, str] | None:
        """Get decrypted credentials for an integration."""
        row = await db.get(Integration, int(integration_id))
        if row is None or row.credentials_encrypted is None:
            return None
        return await self._decrypt_credentials(db, row.credentials_encrypted)

    async def update_integration(
        self,
        db: AsyncSession,
        integration_id: str,
        name: str | None = None,
        credentials: dict[str, str] | None = None,
        status: IntegrationStatus | None = None,
    ) -> UserIntegration | None:
        """Update an integration."""
        row = await db.get(Integration, int(integration_id))
        if row is None:
            return None

        if name is not None:
            row.name = name
        if credentials is not None:
            row.credentials_encrypted = await self._encrypt_credentials(db, credentials)
        if status is not None:
            row.status = status.value

        await db.flush()
        await db.refresh(row)
        return self._row_to_pydantic(row)

    async def delete_integration(
        self, db: AsyncSession, integration_id: str
    ) -> bool:
        """Delete an integration."""
        row = await db.get(Integration, int(integration_id))
        if row is None:
            return False
        await db.delete(row)
        await db.flush()
        return True

    async def test_connection(
        self, db: AsyncSession, integration_id: str
    ) -> dict[str, Any]:
        """Test connection to an integration."""
        row = await db.get(Integration, int(integration_id))
        if row is None:
            return {"success": False, "error": "Integration not found"}

        credentials = await self.get_decrypted_credentials(db, integration_id)
        if credentials is None:
            return {"success": False, "error": "No credentials stored"}

        try:
            itype = IntegrationType(row.integration_type)
            if itype == IntegrationType.NCBI:
                result = await self._test_ncbi(credentials)
            elif itype == IntegrationType.OPENWEATHER:
                result = await self._test_openweather(credentials)
            elif itype == IntegrationType.WEBHOOK:
                result = await self._test_webhook(credentials)
            else:
                result = {"success": True, "message": "Connection test not implemented"}
        except Exception as e:
            row.status = IntegrationStatus.ERROR.value
            row.last_error = str(e)
            await db.flush()
            return {"success": False, "error": str(e)}

        return result

    async def record_usage(self, db: AsyncSession, integration_id: str) -> None:
        """Record that an integration was used."""
        row = await db.get(Integration, int(integration_id))
        if row is not None:
            row.last_used = datetime.now(UTC)
            row.status = IntegrationStatus.ACTIVE.value
            await db.flush()

    # ------------------------------------------------------------------
    # HTTP test helpers (unchanged)
    # ------------------------------------------------------------------

    async def _test_ncbi(self, credentials: dict[str, str]) -> dict[str, Any]:
        """Test NCBI connection."""
        async with create_traced_async_client() as client:
            response = await client.get(
                "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/einfo.fcgi",
                params={
                    "api_key": credentials.get("api_key"),
                    "email": credentials.get("email"),
                    "retmode": "json",
                },
            )
            if response.status_code == 200:
                return {"success": True, "message": "NCBI connection successful"}
            return {"success": False, "error": f"HTTP {response.status_code}"}

    async def _test_openweather(self, credentials: dict[str, str]) -> dict[str, Any]:
        """Test OpenWeatherMap connection."""
        async with create_traced_async_client() as client:
            response = await client.get(
                "https://api.openweathermap.org/data/2.5/weather",
                params={"q": "London", "appid": credentials.get("api_key")},
            )
            if response.status_code == 200:
                return {"success": True, "message": "OpenWeatherMap connection successful"}
            return {"success": False, "error": f"HTTP {response.status_code}"}

    async def _test_webhook(self, credentials: dict[str, str]) -> dict[str, Any]:
        """Test webhook connection."""
        url = credentials.get("url")
        if not url:
            return {"success": False, "error": "No URL configured"}
        async with create_traced_async_client() as client:
            try:
                response = await client.head(url, timeout=10)
                return {
                    "success": True,
                    "message": f"Webhook reachable (HTTP {response.status_code})",
                }
            except Exception as e:
                return {"success": False, "error": str(e)}


# ---------------------------------------------------------------------------
# Module-level singleton — service is now stateless (no cipher, no dict)
# ---------------------------------------------------------------------------

integration_hub = IntegrationHubService()
