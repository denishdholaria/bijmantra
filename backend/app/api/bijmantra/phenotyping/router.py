"""Phenotyping domain router aggregator."""

import logging
from fastapi import APIRouter

from app.api.bijmantra.phenotyping import (
    image_analysis,
    performance_ranking,
    phenology,
    phenotype,
    phenotype_comparison,
    vision,
)

logger = logging.getLogger(__name__)

phenotyping_router = APIRouter()

# Include all phenotyping domain routers
phenotyping_router.include_router(phenotype.router, tags=["Phenotype Analysis"])
phenotyping_router.include_router(
    phenotype_comparison.router, tags=["Phenotype Comparison"]
)
phenotyping_router.include_router(phenology.router, tags=["Phenology Tracker"])

# Image processing is optional (requires cv2 dependencies)
try:
    from app.api.bijmantra.phenotyping import image
    phenotyping_router.include_router(image.router, tags=["Image Processing"])
except Exception as image_import_error:
    logger.warning("Image processing routes disabled due to missing dependencies: %s", image_import_error)

phenotyping_router.include_router(image_analysis.router, tags=["Image Analysis"])
phenotyping_router.include_router(vision.router, tags=["Vision Training Ground"])
phenotyping_router.include_router(
    performance_ranking.router, tags=["Performance Ranking"]
)
