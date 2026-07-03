"""Inventory domain router aggregator."""
from fastapi import APIRouter

from app.api.bijmantra.inventory import (
    barcode,
    label_printing,
    processing,
    seed_inventory,
    traceability,
    warehouse,
)

inventory_router = APIRouter()

# Seed inventory management
inventory_router.include_router(seed_inventory.router, tags=["Seed Inventory"])

# Traceability and tracking
inventory_router.include_router(traceability.router, tags=["Seed Traceability"])

# Warehouse management
inventory_router.include_router(warehouse.router, tags=["Warehouse Management"])

# Processing operations
inventory_router.include_router(processing.router, tags=["Seed Processing"])

# Label printing
inventory_router.include_router(label_printing.router, tags=["Label Printing"])

# Barcode and QR code management
inventory_router.include_router(barcode.router, tags=["Barcode/QR"])
