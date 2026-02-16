"""Germplasm service helpers with audit integration."""

from app.models.audit import AuditLog


class GermplasmService:
    @staticmethod
    async def log_mutation(db, organization_id: int | None, user_id: int | None, action: str, target_id: str, changes: dict | None = None):
        db.add(
            AuditLog(
                organization_id=organization_id,
                user_id=user_id,
                action=action,
                target_type="germplasm",
                target_id=target_id,
                changes=changes,
                method=action,
            )
        )
