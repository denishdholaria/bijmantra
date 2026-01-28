"""
Backup & Restore API
Database backup and restore management
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pydantic import BaseModel
from typing import List, Literal, Optional
from datetime import datetime, timedelta, timezone
import asyncio
import uuid

from app.core.database import get_db
from app.models.data_management import Backup, BackupType, BackupStatus

router = APIRouter(prefix="/backup", tags=["backup"])


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
    backup_id: str


def format_size(size_bytes: int) -> str:
    """Format bytes to human readable string"""
    if size_bytes >= 1_000_000_000:
        return f"{size_bytes / 1_000_000_000:.1f} GB"
    elif size_bytes >= 1_000_000:
        return f"{size_bytes / 1_000_000:.1f} MB"
    elif size_bytes >= 1_000:
        return f"{size_bytes / 1_000:.1f} KB"
    return f"{size_bytes} B"


@router.get("/", response_model=List[BackupResponse])
async def list_backups(db: AsyncSession = Depends(get_db)):
    """List all backups"""
    result = await db.execute(
        select(Backup).order_by(Backup.created_at.desc())
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
async def get_backup_stats(db: AsyncSession = Depends(get_db)):
    """Get backup statistics"""
    result = await db.execute(select(Backup).order_by(Backup.created_at.desc()))
    backups = result.scalars().all()
    
    successful = [b for b in backups if b.status == BackupStatus.COMPLETED]
    latest = backups[0] if backups else None
    
    return BackupStatsResponse(
        total_backups=len(backups),
        successful_backups=len(successful),
        latest_size=format_size(latest.size_bytes or 0) if latest else "-",
        auto_backup_schedule="Daily at 3:00 AM"
    )


async def _create_backup_task(backup_id: uuid.UUID, backup_type: str, db_url: str):
    """Background task to create backup"""
    # In production, this would actually create a backup
    # For now, simulate the process
    await asyncio.sleep(5)
    
    # Note: In a real implementation, you'd need a new database session here
    # This is simplified for demo purposes


@router.post("/create", response_model=BackupResponse)
async def create_backup(
    request: BackupCreateRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """Create a new backup"""
    backup_id = uuid.uuid4()
    timestamp = datetime.now(timezone.utc)
    
    # Map string type to enum
    backup_type_enum = BackupType.MANUAL
    if request.type == "full":
        backup_type_enum = BackupType.FULL
    elif request.type == "incremental":
        backup_type_enum = BackupType.INCREMENTAL
    
    new_backup = Backup(
        id=backup_id,
        backup_name=f"backup_{timestamp.strftime('%Y-%m-%d_%H%M%S')}_{request.type}",
        backup_type=backup_type_enum,
        status=BackupStatus.IN_PROGRESS,
        size_bytes=0,
        started_at=timestamp,
        storage_provider="local"
    )
    
    db.add(new_backup)
    await db.commit()
    await db.refresh(new_backup)
    
    # In production, start background task
    # background_tasks.add_task(_create_backup_task, backup_id, request.type, str(db.get_bind().url))
    
    # For demo, immediately mark as completed with simulated size
    new_backup.status = BackupStatus.COMPLETED
    new_backup.completed_at = timestamp + timedelta(minutes=15)
    new_backup.size_bytes = 2_500_000_000  # 2.5 GB simulated
    await db.commit()
    await db.refresh(new_backup)
    
    return BackupResponse(
        id=str(new_backup.id),
        name=new_backup.backup_name,
        size=format_size(new_backup.size_bytes or 0),
        type=new_backup.backup_type.value if new_backup.backup_type else "manual",
        status=new_backup.status.value if new_backup.status else "in_progress",
        created_at=new_backup.created_at,
        created_by="Current User"
    )


@router.post("/restore")
async def restore_backup(request: RestoreRequest, db: AsyncSession = Depends(get_db)):
    """Restore from a backup"""
    try:
        backup_uuid = uuid.UUID(request.backup_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid backup ID format")
    
    result = await db.execute(
        select(Backup).where(Backup.id == backup_uuid)
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
async def download_backup(backup_id: str, db: AsyncSession = Depends(get_db)):
    """Download a backup file"""
    try:
        backup_uuid = uuid.UUID(backup_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid backup ID format")
    
    result = await db.execute(
        select(Backup).where(Backup.id == backup_uuid)
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
async def delete_backup(backup_id: str, db: AsyncSession = Depends(get_db)):
    """Delete a backup"""
    try:
        backup_uuid = uuid.UUID(backup_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid backup ID format")
    
    result = await db.execute(
        select(Backup).where(Backup.id == backup_uuid)
    )
    backup = result.scalar_one_or_none()
    
    if not backup:
        raise HTTPException(status_code=404, detail="Backup not found")
    
    backup_name = backup.backup_name
    await db.delete(backup)
    await db.commit()
    
    return {"message": f"Backup {backup_name} deleted successfully"}
