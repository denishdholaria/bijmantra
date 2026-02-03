from fastapi import APIRouter

# Import sub-module routers
from app.modules.space.mars.router import router as mars_router
from app.modules.space.lunar.router import router as lunar_router
from app.modules.space.research.router import router as research_router
from app.modules.space.solar.router import router as solar_router

# Create the main Space Gateway router
router = APIRouter()

# Include sub-routers with specific prefixes
router.include_router(mars_router, prefix="/mars", tags=["MARS Module"])
router.include_router(lunar_router, prefix="/lunar", tags=["LUNAR Module"])
router.include_router(research_router, prefix="/research", tags=["Space Research"])
router.include_router(solar_router, prefix="/solar", tags=["Sun-Earth Systems"])
