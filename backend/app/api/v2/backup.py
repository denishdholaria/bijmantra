"""
Backup & Restore API
Database backup and restore management
"""
from datetime import UTC, datetime
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.data_management import Backup, BackupStatus, BackupType
from app.models.core import User


router = APIRouter(prefix="/backup", tags=["backup"], dependencies=[Depends(get_current_user)])


class BackupResponse(BaseModel):
    id: str
    name: str
    size: str
    type: Literal["full", "incremental", "manual"]
    status: Literal["completed", "in_progress", "failed"]
    created_at: datetime
    created_by: str


class BackupCreateRequest(BaseModel):
    type: Literal["full", "incremental", "manual"] = "manual"


class BackupStatsResponse(BaseModel):
    total_backups: int
    successful_backups: int
    latest_size: str
    auto_backup_schedule: str


class RestoreRequest(BaseModel):
    backup_id: int


def format_size(size_bytes: int) -> str:
    """Format bytes to human readable string"""
    if size_bytes >= 1_000_000_000:
        return f"{size_bytes / 1_000_000_000:.1f} GB"
    elif size_bytes >= 1_000_000:
        return f"{size_bytes / 1_000_000:.1f} MB"
    elif size_bytes >= 1_000:
        return f"{size_bytes / 1_000:.1f} KB"
    return f"{size_bytes} B"


@router.get("/", response_model=list[BackupResponse])
async def list_backups(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all backups"""
    result = await db.execute(
        select(Backup)
        .where(Backup.organization_id == current_user.organization_id)
        .order_by(Backup.created_at.desc())
    )
    backups = result.scalars().all()

    return [
        BackupResponse(
            id=str(b.id),
            name=b.backup_name,
            size=format_size(b.size_bytes or 0),
            type=b.backup_type.value if b.backup_type else "manual",
            status=b.status.value if b.status else "completed",
            created_at=b.created_at,
            created_by="System" if b.backup_type != BackupType.MANUAL else "admin@bijmantra.org"
        )
        for b in backups
    ]


@router.get("/stats", response_model=BackupStatsResponse)
async def get_backup_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get backup statistics"""
    result = await db.execute(
        select(Backup)
        .where(Backup.organization_id == current_user.organization_id)
        .order_by(Backup.created_at.desc())
    )
    backups = result.scalars().all()

    successful = [b for b in backups if b.status == BackupStatus.COMPLETED]
    latest = backups[0] if backups else None

    return BackupStatsResponse(
        total_backups=len(backups),
        successful_backups=len(successful),
        latest_size=format_size(latest.size_bytes or 0) if latest else "-",
        auto_backup_schedule="Unavailable"
    )


@router.post("/create", response_model=BackupResponse)
async def create_backup(
    request: BackupCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Record a new backup request."""
    timestamp = datetime.now(UTC).replace(tzinfo=None)

    # Map string type to enum
    backup_type_enum = BackupType.MANUAL
    if request.type == "full":
        backup_type_enum = BackupType.FULL
    elif request.type == "incremental":
        backup_type_enum = BackupType.INCREMENTAL

    new_backup = Backup(
        organization_id=current_user.organization_id,
        backup_name=f"backup_{timestamp.strftime('%Y-%m-%d_%H%M%S')}_{request.type}",
        backup_type=backup_type_enum,
        status=BackupStatus.IN_PROGRESS,
        size_bytes=0,
        started_at=timestamp,
        storage_provider="local",
        created_by=current_user.id,
    )

    db.add(new_backup)
    await db.commit()
    await db.refresh(new_backup)

    return BackupResponse(
        id=str(new_backup.id),
        name=new_backup.backup_name,
        size=format_size(new_backup.size_bytes or 0),
        type=new_backup.backup_type.value if new_backup.backup_type else "manual",
        status=new_backup.status.value if new_backup.status else "in_progress",
        created_at=new_backup.created_at,
        created_by=getattr(current_user, "email", None) or "Current User"
    )


@router.post("/restore")
async def restore_backup(
    request: RestoreRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Restore from a backup"""
    result = await db.execute(
        select(Backup).where(
            Backup.id == request.backup_id,
            Backup.organization_id == current_user.organization_id,
        )
    )
    backup = result.scalar_one_or_none()

    if not backup:
        raise HTTPException(status_code=404, detail="Backup not found")

    if backup.status != BackupStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Cannot restore from incomplete backup")

    # In production, this would trigger actual restore process
    return {
        "message": f"Restore from {backup.backup_name} initiated",
        "backup_id": str(backup.id),
        "estimated_time": "10-15 minutes"
    }


@router.get("/download/{backup_id}")
async def download_backup(
    backup_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Download a backup file"""
    result = await db.execute(
        select(Backup).where(
            Backup.id == backup_id,
            Backup.organization_id == current_user.organization_id,
        )
    )
    backup = result.scalar_one_or_none()

    if not backup:
        raise HTTPException(status_code=404, detail="Backup not found")

    # In production, this would return actual file
    return {
        "message": f"Download initiated for {backup.backup_name}",
        "backup_id": str(backup.id),
        "size": format_size(backup.size_bytes or 0),
        "download_url": f"/api/v2/backup/files/{backup_id}"
    }


@router.delete("/{backup_id}")
async def delete_backup(
    backup_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a backup"""
    result = await db.execute(
        select(Backup).where(
            Backup.id == backup_id,
            Backup.organization_id == current_user.organization_id,
        )
    )
    backup = result.scalar_one_or_none()

    if not backup:
        raise HTTPException(status_code=404, detail="Backup not found")

    backup_name = backup.backup_name
    await db.delete(backup)
    await db.commit()

    return {"message": f"Backup {backup_name} deleted successfully"}
