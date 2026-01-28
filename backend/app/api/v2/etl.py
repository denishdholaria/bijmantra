"""
ETL Pipeline API
Trigger and monitor Data Lake ETL jobs.
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from app.api.deps import get_current_superuser
from app.services.analytics.etl_service import etl_service
from app.models.core import User

router = APIRouter(prefix="/etl", tags=["System - ETL"])

@router.post("/run", status_code=202)
async def trigger_etl_job(
    background_tasks: BackgroundTasks,
    domain: str = "all",
    current_user: User = Depends(get_current_superuser)
):
    """
    Trigger an ETL job manually.
    Requires Superuser privileges.

    Args:
        domain: specific domain to run (e.g., 'yield_prediction') or 'all'.
    """
    if domain == "all" or domain == "yield_prediction":
        background_tasks.add_task(etl_service.run_nightly_etl)
        return {"status": "accepted", "message": "ETL job submitted for background processing"}
    else:
        raise HTTPException(status_code=400, detail=f"Unknown ETL domain: {domain}")
