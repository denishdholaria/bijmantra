"""
Phenomic Selection API Router
High-throughput phenotyping endpoints
"""
from fastapi import APIRouter, Depends, Query, File, UploadFile, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from pydantic import BaseModel

from app.core.database import get_db
from app.api.deps import get_current_user
from app.services.phenomic_selection import phenomic_selection_service

router = APIRouter(prefix="/phenomic-selection", tags=["Phenomic Selection"])


class PredictRequest(BaseModel):
    model_id: str
    sample_ids: list[str]


@router.get("/datasets")
async def get_datasets(
    crop: Optional[str] = Query(None),
    platform: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get phenomic datasets"""
    return await phenomic_selection_service.get_datasets(db, current_user.organization_id, crop, platform)


@router.get("/datasets/{dataset_id}")
async def get_dataset(
    dataset_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get single dataset"""
    return await phenomic_selection_service.get_dataset(db, current_user.organization_id, dataset_id)


@router.get("/models")
async def get_models(
    dataset_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get prediction models"""
    return await phenomic_selection_service.get_models(db, current_user.organization_id, dataset_id, status)


@router.post("/predict")
async def predict_traits(
    request: PredictRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Predict traits for samples"""
    return await phenomic_selection_service.predict_traits(
        db, current_user.organization_id,
        request.model_id,
        request.sample_ids
    )


@router.post("/upload", summary="Upload spectral data")
async def upload_spectral_data(
    file: UploadFile = File(...),
    dataset_name: Optional[str] = Query(None),
    crop: Optional[str] = Query(None),
    platform: Optional[str] = Query("NIRS"),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Upload spectral data (CSV, DX, SPC).
    Simulates storage and returns success.
    """
    if not file.filename.lower().endswith(('.csv', '.dx', '.spc')):
        raise HTTPException(400, "Invalid file format. Supported: .csv, .dx, .spc")

    # Simulate processing
    content = await file.read()
    size = len(content)

    # In a real implementation, we would parse the file and store it.
    # For now, we just return a success message.

    return {
        "success": True,
        "filename": file.filename,
        "size_bytes": size,
        "message": f"Successfully uploaded {file.filename}. Data processing started.",
        "dataset_id": "simulated-dataset-id",
        "status": "processing"
    }


@router.get("/spectral/{dataset_id}")
async def get_spectral_data(
    dataset_id: str,
    sample_id: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get spectral data for visualization"""
    return await phenomic_selection_service.get_spectral_data(db, current_user.organization_id, dataset_id, sample_id)


@router.get("/statistics")
async def get_statistics(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get phenomic selection statistics"""
    return await phenomic_selection_service.get_statistics(db, current_user.organization_id)
