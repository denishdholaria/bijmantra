"""
Phenomic Selection API Router
High-throughput phenotyping endpoints
"""
from fastapi import APIRouter, Query
from typing import Optional
from pydantic import BaseModel

from app.services.phenomic_selection import phenomic_selection_service

router = APIRouter(prefix="/phenomic-selection", tags=["Phenomic Selection"])


class PredictRequest(BaseModel):
    model_id: str
    sample_ids: list[str]


@router.get("/datasets")
async def get_datasets(
    crop: Optional[str] = Query(None),
    platform: Optional[str] = Query(None)
):
    """Get phenomic datasets"""
    return await phenomic_selection_service.get_datasets(crop, platform)


@router.get("/datasets/{dataset_id}")
async def get_dataset(dataset_id: str):
    """Get single dataset"""
    return await phenomic_selection_service.get_dataset(dataset_id)


@router.get("/models")
async def get_models(
    dataset_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None)
):
    """Get prediction models"""
    return await phenomic_selection_service.get_models(dataset_id, status)


@router.post("/predict")
async def predict_traits(request: PredictRequest):
    """Predict traits for samples"""
    return await phenomic_selection_service.predict_traits(
        request.model_id,
        request.sample_ids
    )


@router.get("/spectral/{dataset_id}")
async def get_spectral_data(
    dataset_id: str,
    sample_id: Optional[str] = Query(None)
):
    """Get spectral data for visualization"""
    return await phenomic_selection_service.get_spectral_data(dataset_id, sample_id)


@router.get("/statistics")
async def get_statistics():
    """Get phenomic selection statistics"""
    return await phenomic_selection_service.get_statistics()
