"""
Data Domain Router Aggregator
Composes all data-related routers into a single mountable router
"""

from fastapi import APIRouter

from app.api.bijmantra.data import (
    data_dictionary,
    data_quality,
    data_sync,
    data_validation,
    data_visualization,
    etl,
    export,
    import_api,
    offline_sync,
    quick_entry,
    csv_mapper,
)

data_router = APIRouter()

# Data management and quality
data_router.include_router(data_dictionary.router, tags=["Data Dictionary"])
data_router.include_router(data_quality.router, tags=["Data Quality"])
data_router.include_router(data_validation.router, tags=["Data Validation"])
data_router.include_router(data_sync.router, tags=["Data Sync"])
data_router.include_router(offline_sync.router, tags=["Offline Sync"])

# Data import/export
data_router.include_router(import_api.router, tags=["Data Import"])
data_router.include_router(export.router, tags=["Data Export"])
data_router.include_router(etl.router, tags=["ETL"])

# Data entry and visualization
data_router.include_router(quick_entry.router, tags=["Quick Entry"])
data_router.include_router(data_visualization.router, tags=["Data Visualization"])

# CSV mapping
data_router.include_router(csv_mapper.router, tags=["CSV Mapper"])
