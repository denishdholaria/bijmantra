"""
Operations Domain Router
Aggregates all operations-related endpoints
"""

import logging
from fastapi import APIRouter

from app.api.bijmantra.operations import (
    abiotic,
    agronomy,
    crop_health,
    disease,
    dock,
    dus,
    events,
    mta,
    quality,
    resource_management,
    sensors,
    social,
    tasks,
    vault_sensors,
)

logger = logging.getLogger(__name__)

operations_router = APIRouter()

# Include all operations routers
operations_router.include_router(abiotic.router, tags=["Abiotic Stress"])
operations_router.include_router(agronomy.router, tags=["Agronomy"])
operations_router.include_router(crop_health.router, tags=["Crop Health"])
operations_router.include_router(disease.router, tags=["Disease Resistance"])
operations_router.include_router(dock.router, tags=["Dock"])
operations_router.include_router(dus.router, tags=["DUS Testing"])
operations_router.include_router(events.router, tags=["Event Bus"])
operations_router.include_router(mta.router, tags=["Material Transfer Agreements"])
operations_router.include_router(quality.router, tags=["Quality Control"])
operations_router.include_router(resource_management.router, tags=["Resource Management"])

# Robotics is optional (requires cv2 dependencies)
try:
    from app.api.bijmantra.operations import robotics
    operations_router.include_router(robotics.router, tags=["Robotics"])
except Exception as robotics_import_error:
    logger.warning("Robotics routes disabled due to missing dependencies: %s", robotics_import_error)

operations_router.include_router(sensors.router, tags=["Sensor Networks"])
operations_router.include_router(social.router, tags=["Social"])
operations_router.include_router(tasks.router, tags=["Task Queue"])
operations_router.include_router(vault_sensors.router, tags=["Vault Sensors"])
