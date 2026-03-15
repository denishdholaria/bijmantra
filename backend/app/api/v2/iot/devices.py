"""
IoT Device Registry API
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.core import User
from app.schemas.iot.device import (
    IoTDeviceCreate,
    IoTDeviceListResponse,
    IoTDeviceResponse,
    IoTDeviceUpdate,
)
from app.modules.environment.services.iot.device_service import device_registry_service


router = APIRouter(prefix="/iot/devices", tags=["IoT Devices"])

@router.post("/", response_model=IoTDeviceResponse, status_code=status.HTTP_201_CREATED)
async def create_device(
    device_in: IoTDeviceCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Register a new IoT device.
    """
    try:
        # Assuming current_user has organization_id. If optional, fallback to 1 or handle error.
        # In this system, users belong to organizations.
        org_id = current_user.organization_id
        if not org_id:
             raise HTTPException(status_code=400, detail="User must belong to an organization")

        device = await device_registry_service.create_device(
            db=db,
            device_in=device_in,
            organization_id=org_id
        )
        return device
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/", response_model=IoTDeviceListResponse)
async def list_devices(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    device_type: str | None = Query(None),
    status: str | None = Query(None),
    field_id: int | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List all registered IoT devices.
    """
    org_id = current_user.organization_id

    items, total = await device_registry_service.list_devices(
        db=db,
        skip=skip,
        limit=limit,
        organization_id=org_id,
        device_type=device_type,
        status=status,
        field_id=field_id
    )

    return {"total": total, "items": items}


@router.get("/{device_id}", response_model=IoTDeviceResponse)
async def get_device(
    device_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get device details by ID.
    """
    device = await device_registry_service.get_device(db, device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    # Check authorization
    if device.organization_id != current_user.organization_id:
        raise HTTPException(status_code=403, detail="Not authorized to access this device")

    return device


@router.put("/{device_id}", response_model=IoTDeviceResponse)
async def update_device(
    device_id: int,
    device_in: IoTDeviceUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update device details.
    """
    # Check existence and authorization first
    device = await device_registry_service.get_device(db, device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    if device.organization_id != current_user.organization_id:
        raise HTTPException(status_code=403, detail="Not authorized to update this device")

    updated_device = await device_registry_service.update_device(
        db=db,
        device_id=device_id,
        device_in=device_in
    )
    return updated_device


@router.delete("/{device_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_device(
    device_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a device.
    """
    # Check existence and authorization first
    device = await device_registry_service.get_device(db, device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    if device.organization_id != current_user.organization_id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this device")

    success = await device_registry_service.delete_device(db, device_id)
    if not success:
         raise HTTPException(status_code=500, detail="Failed to delete device")
    return None
