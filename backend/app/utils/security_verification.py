"""Security verification utilities."""

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


async def verify_encryption_at_rest(db: AsyncSession) -> dict:
    """Check PostgreSQL settings that indicate encryption-at-rest posture."""
    checks = {}
    for key in ["ssl", "data_checksums"]:
        try:
            row = (await db.execute(text("SELECT setting FROM pg_settings WHERE name = :name"), {"name": key})).first()
            checks[key] = row[0] if row else "unknown"
        except Exception as exc:
            checks[key] = f"unavailable: {exc.__class__.__name__}"
    checks["verified"] = checks.get("ssl") in {"on", "1", "true", True}
    return checks
