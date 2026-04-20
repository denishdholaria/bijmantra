"""
Audit Trail Service
Enterprise-grade audit logging for compliance and traceability

APEX FEATURE: Complete audit trail for regulatory compliance
"""

import contextlib
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict
from sqlalchemy import JSON, Column, DateTime, Index, Integer, String
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.base import Base


# ============================================
# ENUMS
# ============================================

class AuditAction(StrEnum):
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    LOGIN = "login"
    LOGOUT = "logout"
    EXPORT = "export"
    IMPORT = "import"
    SHARE = "share"
    APPROVE = "approve"
    REJECT = "reject"
    COMPUTE = "compute"


class AuditSeverity(StrEnum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


# ============================================
# MODELS
# ============================================

class AuditLog(Base):
    """Audit log entry for tracking all system activities"""

    __tablename__ = "legacy_audit_logs"
    id = Column(Integer, primary_key=True, index=True)

    # Who
    user_id = Column(String, nullable=True, index=True)
    user_email = Column(String, nullable=True)
    user_name = Column(String, nullable=True)
    organization_id = Column(String, nullable=True, index=True)

    # What
    action = Column(String, nullable=False, index=True)
    entity_type = Column(String, nullable=False, index=True)
    entity_id = Column(String, nullable=True, index=True)
    entity_name = Column(String, nullable=True)

    # Details
    description = Column(String, nullable=True)
    old_values = Column(JSON, nullable=True)
    new_values = Column(JSON, nullable=True)
    extra_data = Column(JSON, nullable=True)  # renamed from 'metadata' (reserved)

    # Context
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)
    request_id = Column(String, nullable=True, index=True)
    session_id = Column(String, nullable=True)

    # Classification
    severity = Column(String, default=AuditSeverity.INFO.value)
    category = Column(String, nullable=True, index=True)
    tags = Column(JSON, nullable=True)

    # Timestamps
    timestamp = Column(DateTime, default=lambda: datetime.now(UTC), index=True)

    # Indexes for common queries
    __table_args__ = (
        Index('ix_audit_user_timestamp', 'user_id', 'timestamp'),
        Index('ix_audit_entity_timestamp', 'entity_type', 'entity_id', 'timestamp'),
        Index('ix_audit_org_timestamp', 'organization_id', 'timestamp'),
    )


# ============================================
# SCHEMAS
# ============================================

class AuditLogCreate(BaseModel):
    user_id: str | None = None
    user_email: str | None = None
    user_name: str | None = None
    organization_id: str | None = None
    action: AuditAction
    entity_type: str
    entity_id: str | None = None
    entity_name: str | None = None
    description: str | None = None
    old_values: dict[str, Any] | None = None
    new_values: dict[str, Any] | None = None
    metadata: dict[str, Any] | None = None
    ip_address: str | None = None
    user_agent: str | None = None
    request_id: str | None = None
    session_id: str | None = None
    severity: AuditSeverity = AuditSeverity.INFO
    category: str | None = None
    tags: list[str] | None = None


class AuditLogResponse(BaseModel):
    id: int
    user_id: str | None
    user_email: str | None
    user_name: str | None
    organization_id: str | None
    action: str
    entity_type: str
    entity_id: str | None
    entity_name: str | None
    description: str | None
    old_values: dict[str, Any] | None
    new_values: dict[str, Any] | None
    metadata: dict[str, Any] | None
    ip_address: str | None
    severity: str
    category: str | None
    tags: list[str] | None
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)


class AuditLogFilter(BaseModel):
    user_id: str | None = None
    organization_id: str | None = None
    action: AuditAction | None = None
    entity_type: str | None = None
    entity_id: str | None = None
    severity: AuditSeverity | None = None
    category: str | None = None
    start_date: datetime | None = None
    end_date: datetime | None = None
    search: str | None = None


# ============================================
# SERVICE
# ============================================

class AuditService:
    """Service for managing audit logs"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def log(self, entry: AuditLogCreate) -> AuditLog:
        """Create a new audit log entry"""
        audit_log = AuditLog(
            user_id=entry.user_id,
            user_email=entry.user_email,
            user_name=entry.user_name,
            organization_id=entry.organization_id,
            action=entry.action.value,
            entity_type=entry.entity_type,
            entity_id=entry.entity_id,
            entity_name=entry.entity_name,
            description=entry.description,
            old_values=entry.old_values,
            new_values=entry.new_values,
            extra_data=entry.metadata,
            ip_address=entry.ip_address,
            user_agent=entry.user_agent,
            request_id=entry.request_id,
            session_id=entry.session_id,
            severity=entry.severity.value,
            category=entry.category,
            tags=entry.tags,
            timestamp=datetime.now(UTC)
        )

        self.db.add(audit_log)
        await self.db.commit()
        await self.db.refresh(audit_log)

        return audit_log

    async def get_logs(
        self,
        filter: AuditLogFilter,
        skip: int = 0,
        limit: int = 100
    ) -> list[AuditLog]:
        """Query audit logs with filters"""
        query = select(AuditLog)

        if filter.user_id:
            query = query.where(AuditLog.user_id == filter.user_id)

        if filter.organization_id:
            query = query.where(AuditLog.organization_id == filter.organization_id)

        if filter.action:
            query = query.where(AuditLog.action == filter.action.value)

        if filter.entity_type:
            query = query.where(AuditLog.entity_type == filter.entity_type)

        if filter.entity_id:
            query = query.where(AuditLog.entity_id == filter.entity_id)

        if filter.severity:
            query = query.where(AuditLog.severity == filter.severity.value)

        if filter.category:
            query = query.where(AuditLog.category == filter.category)

        if filter.start_date:
            query = query.where(AuditLog.timestamp >= filter.start_date)

        if filter.end_date:
            query = query.where(AuditLog.timestamp <= filter.end_date)

        query = query.order_by(AuditLog.timestamp.desc())
        query = query.offset(skip).limit(limit)

        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_entity_history(
        self,
        entity_type: str,
        entity_id: str,
        limit: int = 50
    ) -> list[AuditLog]:
        """Get complete history for a specific entity"""
        query = select(AuditLog).where(
            AuditLog.entity_type == entity_type,
            AuditLog.entity_id == entity_id
        ).order_by(AuditLog.timestamp.desc()).limit(limit)

        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_user_activity(
        self,
        user_id: str,
        days: int = 30,
        limit: int = 100
    ) -> list[AuditLog]:
        """Get recent activity for a user"""
        from datetime import timedelta

        start_date = datetime.now(UTC) - timedelta(days=days)

        query = select(AuditLog).where(
            AuditLog.user_id == user_id,
            AuditLog.timestamp >= start_date
        ).order_by(AuditLog.timestamp.desc()).limit(limit)

        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_security_events(
        self,
        organization_id: str | None = None,
        limit: int = 100
    ) -> list[AuditLog]:
        """Get security-related events (logins, exports, etc.)"""
        security_actions = [
            AuditAction.LOGIN.value,
            AuditAction.LOGOUT.value,
            AuditAction.EXPORT.value,
            AuditAction.SHARE.value
        ]

        query = select(AuditLog).where(
            AuditLog.action.in_(security_actions)
        )

        if organization_id:
            query = query.where(AuditLog.organization_id == organization_id)

        query = query.order_by(AuditLog.timestamp.desc()).limit(limit)

        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_change_diff(
        self,
        entity_type: str,
        entity_id: str,
        from_timestamp: datetime,
        to_timestamp: datetime
    ) -> dict[str, Any]:
        """Get aggregated changes between two timestamps"""
        query = select(AuditLog).where(
            AuditLog.entity_type == entity_type,
            AuditLog.entity_id == entity_id,
            AuditLog.timestamp >= from_timestamp,
            AuditLog.timestamp <= to_timestamp,
            AuditLog.action == AuditAction.UPDATE.value
        ).order_by(AuditLog.timestamp.asc())

        result = await self.db.execute(query)
        logs = result.scalars().all()

        # Aggregate all changes
        all_changes = {}
        for log in logs:
            if log.old_values and log.new_values:
                for key, new_val in log.new_values.items():
                    if key not in all_changes:
                        all_changes[key] = {
                            'original': log.old_values.get(key),
                            'current': new_val,
                            'changes': []
                        }
                    all_changes[key]['current'] = new_val
                    all_changes[key]['changes'].append({
                        'timestamp': log.timestamp.isoformat(),
                        'user': log.user_name or log.user_email,
                        'from': log.old_values.get(key),
                        'to': new_val
                    })

        return all_changes


# ============================================
# DECORATOR FOR AUTOMATIC AUDITING
# ============================================

def audit_action(
    action: AuditAction,
    entity_type: str,
    description_template: str | None = None
):
    """Decorator to automatically audit function calls"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Extract context from kwargs or args
            db = kwargs.get('db')
            current_user = kwargs.get('current_user')
            request = kwargs.get('request')

            # Execute the function
            result = await func(*args, **kwargs)

            # Create audit entry
            if db and current_user:
                audit_service = AuditService(db)

                entity_id = None
                entity_name = None

                # Try to extract entity info from result
                if hasattr(result, 'id'):
                    entity_id = str(result.id)
                if hasattr(result, 'name'):
                    entity_name = result.name

                description = description_template
                if description and hasattr(result, '__dict__'):
                    with contextlib.suppress(BaseException):
                        description = description_template.format(**result.__dict__)

                await audit_service.log(AuditLogCreate(
                    user_id=str(current_user.id) if current_user else None,
                    user_email=current_user.email if current_user else None,
                    user_name=current_user.name if hasattr(current_user, 'name') else None,
                    organization_id=str(current_user.organization_id) if hasattr(current_user, 'organization_id') else None,
                    action=action,
                    entity_type=entity_type,
                    entity_id=entity_id,
                    entity_name=entity_name,
                    description=description,
                    ip_address=request.client.host if request else None,
                    user_agent=request.headers.get('user-agent') if request else None
                ))

            return result

        return wrapper
    return decorator


# ============================================
# HELPER FUNCTIONS
# ============================================

def compute_diff(old: dict[str, Any], new: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Compute the difference between two dictionaries"""
    diff = {}

    all_keys = set(old.keys()) | set(new.keys())

    for key in all_keys:
        old_val = old.get(key)
        new_val = new.get(key)

        if old_val != new_val:
            diff[key] = {
                'old': old_val,
                'new': new_val
            }

    return diff


async def log_data_change(
    db: AsyncSession,
    user: Any,
    action: AuditAction,
    entity_type: str,
    entity_id: str,
    entity_name: str | None = None,
    old_data: dict | None = None,
    new_data: dict | None = None,
    request: Any = None
):
    """Helper function to log data changes"""
    audit_service = AuditService(db)

    # Compute diff if both old and new data provided
    old_values = None
    new_values = None

    if old_data and new_data:
        diff = compute_diff(old_data, new_data)
        old_values = {k: v['old'] for k, v in diff.items()}
        new_values = {k: v['new'] for k, v in diff.items()}
    elif new_data:
        new_values = new_data
    elif old_data:
        old_values = old_data

    await audit_service.log(AuditLogCreate(
        user_id=str(user.id) if user else None,
        user_email=user.email if user else None,
        organization_id=str(user.organization_id) if hasattr(user, 'organization_id') else None,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        entity_name=entity_name,
        old_values=old_values,
        new_values=new_values,
        ip_address=request.client.host if request else None,
        user_agent=request.headers.get('user-agent') if request else None
    ))
