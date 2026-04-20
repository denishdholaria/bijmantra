"""Phenomic Selection API Router."""

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.core import User
from app.modules.phenotyping.services.phenomic_selection_service import phenomic_selection_service


router = APIRouter(prefix="/phenomic-selection", tags=["Phenomic Selection"])


class PredictRequest(BaseModel):
    model_id: str
    sample_ids: list[str]


@router.get("/datasets")
async def get_datasets(
    crop: str | None = Query(None),
    platform: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get phenomic datasets"""
    return await phenomic_selection_service.get_datasets(
        db, current_user.organization_id, crop, platform
    )


@router.get("/datasets/{dataset_id}")
async def get_dataset(
    dataset_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get single dataset"""
    return await phenomic_selection_service.get_dataset(
        db, current_user.organization_id, dataset_id
    )


@router.get("/models")
async def get_models(
    dataset_id: str | None = Query(None),
    status: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get prediction models"""
    return await phenomic_selection_service.get_models(
        db, current_user.organization_id, dataset_id, status
    )


@router.post("/predict")
async def predict_traits(
    request: PredictRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Predict traits for samples"""
    return await phenomic_selection_service.predict_traits(
        db, current_user.organization_id, request.model_id, request.sample_ids
    )


@router.post("/upload", summary="Upload spectral data")
async def upload_spectral_data(
    file: UploadFile = File(...),
    dataset_name: str | None = Form(None),
    crop: str | None = Form(None),
    platform: str | None = Form("NIRS"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Upload spectral data (CSV, DX, SPC).
    Creates a persistent ingestion receipt for downstream processing.
    """
    file_name = file.filename or "spectral-upload.dat"
    if not file_name.lower().endswith((".csv", ".dx", ".spc")):
        raise HTTPException(400, "Invalid file format. Supported: .csv, .dx, .spc")

    content = await file.read()
    size = len(content)

    return await phenomic_selection_service.create_upload_receipt(
        db=db,
        organization_id=current_user.organization_id,
        user_id=current_user.id,
        filename=file_name,
        content_type=file.content_type or "application/octet-stream",
        size_bytes=size,
        dataset_name=dataset_name,
        crop=crop,
        platform=platform,
    )


@router.get("/spectral/{dataset_id}")
async def get_spectral_data(
    dataset_id: str,
    sample_id: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get spectral data for visualization"""
    return await phenomic_selection_service.get_spectral_data(
        db, current_user.organization_id, dataset_id, sample_id
    )


@router.get("/statistics")
async def get_statistics(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get phenomic selection statistics"""
    return await phenomic_selection_service.get_statistics(db, current_user.organization_id)
