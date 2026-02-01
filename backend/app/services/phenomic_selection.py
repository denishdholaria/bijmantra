"""
Phenomic Selection Service
High-throughput phenotyping for genomic prediction

Converted to database queries per Zero Mock Data Policy.
"""
from typing import Optional
from datetime import datetime
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.phenomic import PhenomicDataset, PhenomicModel


class PhenomicSelectionService:
    """Service for phenomic selection and high-throughput phenotyping."""
    
    async def get_datasets(
        self,
        db: AsyncSession,
        organization_id: int,
        crop: Optional[str] = None,
        platform: Optional[str] = None
    ) -> list:
        """
        Get phenomic datasets.
        
        Args:
            db: Database session
            organization_id: Organization ID for multi-tenant isolation
            crop: Optional crop filter
            platform: Optional platform filter (NIRS, Hyperspectral, Thermal, etc.)
            
        Returns:
            List of phenomic datasets
        """
        stmt = select(PhenomicDataset).where(
            PhenomicDataset.organization_id == organization_id
        )
        
        if crop:
            stmt = stmt.where(func.lower(PhenomicDataset.crop) == crop.lower())
        if platform:
            stmt = stmt.where(func.lower(PhenomicDataset.platform) == platform.lower())
            
        result = await db.execute(stmt)
        datasets = result.scalars().all()
        
        return [
            {
                "id": str(d.id),
                "dataset_code": d.dataset_code,
                "name": d.name,
                "crop": d.crop,
                "platform": d.platform,
                "samples": d.samples,
                "wavelengths": d.wavelengths,
                "traits_predicted": d.traits_predicted or [],
                "accuracy": d.accuracy,
                "created_at": d.created_at.isoformat() if d.created_at else None,
                "status": d.status
            }
            for d in datasets
        ]
    
    async def get_dataset(
        self,
        db: AsyncSession,
        organization_id: int,
        dataset_id: str
    ) -> Optional[dict]:
        """
        Get single dataset by ID.
        
        Args:
            db: Database session
            organization_id: Organization ID for multi-tenant isolation
            dataset_id: Dataset ID (can be numeric ID or dataset_code)
            
        Returns:
            Dataset dict or None if not found
        """
        # Try to parse as integer ID first
        try:
            numeric_id = int(dataset_id)
            stmt = select(PhenomicDataset).where(
                PhenomicDataset.id == numeric_id,
                PhenomicDataset.organization_id == organization_id
            )
        except ValueError:
            # Treat as dataset_code
            stmt = select(PhenomicDataset).where(
                PhenomicDataset.dataset_code == dataset_id,
                PhenomicDataset.organization_id == organization_id
            )
        
        result = await db.execute(stmt)
        d = result.scalar_one_or_none()
        
        if not d:
            return None
            
        return {
            "id": str(d.id),
            "dataset_code": d.dataset_code,
            "name": d.name,
            "crop": d.crop,
            "platform": d.platform,
            "samples": d.samples,
            "wavelengths": d.wavelengths,
            "traits_predicted": d.traits_predicted or [],
            "accuracy": d.accuracy,
            "description": d.description,
            "notes": d.notes,
            "created_at": d.created_at.isoformat() if d.created_at else None,
            "status": d.status
        }
    
    async def get_models(
        self,
        db: AsyncSession,
        organization_id: int,
        dataset_id: Optional[int] = None,
        status: Optional[str] = None
    ) -> list:
        """
        Get prediction models.
        
        Args:
            db: Database session
            organization_id: Organization ID for multi-tenant isolation
            dataset_id: Optional dataset ID filter
            status: Optional status filter (training, deployed, archived)
            
        Returns:
            List of phenomic models
        """
        stmt = select(PhenomicModel).where(
            PhenomicModel.organization_id == organization_id
        )
        
        if dataset_id:
            stmt = stmt.where(PhenomicModel.dataset_id == dataset_id)
        if status:
            stmt = stmt.where(func.lower(PhenomicModel.status) == status.lower())
            
        result = await db.execute(stmt)
        models = result.scalars().all()
        
        return [
            {
                "id": str(m.id),
                "model_code": m.model_code,
                "name": m.name,
                "type": m.model_type,
                "dataset_id": str(m.dataset_id),
                "target_trait": m.target_trait,
                "r_squared": m.r_squared,
                "rmse": m.rmse,
                "accuracy": m.accuracy,
                "f1_score": m.f1_score,
                "parameters": m.parameters or {},
                "status": m.status
            }
            for m in models
        ]
    
    async def get_model(
        self,
        db: AsyncSession,
        organization_id: int,
        model_id: str
    ) -> Optional[dict]:
        """
        Get single model by ID.
        
        Args:
            db: Database session
            organization_id: Organization ID for multi-tenant isolation
            model_id: Model ID (can be numeric ID or model_code)
            
        Returns:
            Model dict or None if not found
        """
        try:
            numeric_id = int(model_id)
            stmt = select(PhenomicModel).where(
                PhenomicModel.id == numeric_id,
                PhenomicModel.organization_id == organization_id
            )
        except ValueError:
            stmt = select(PhenomicModel).where(
                PhenomicModel.model_code == model_id,
                PhenomicModel.organization_id == organization_id
            )
        
        result = await db.execute(stmt)
        m = result.scalar_one_or_none()
        
        if not m:
            return None
            
        return {
            "id": str(m.id),
            "model_code": m.model_code,
            "name": m.name,
            "type": m.model_type,
            "dataset_id": str(m.dataset_id),
            "target_trait": m.target_trait,
            "r_squared": m.r_squared,
            "rmse": m.rmse,
            "accuracy": m.accuracy,
            "f1_score": m.f1_score,
            "parameters": m.parameters or {},
            "description": m.description,
            "notes": m.notes,
            "status": m.status
        }
    
    async def predict_traits(
        self,
        db: AsyncSession,
        organization_id: int,
        model_id: str,
        sample_ids: list[str]
    ) -> dict:
        """
        Predict traits for samples using a model.
        
        Note: Actual prediction would require the trained model weights
        and spectral data. This returns a placeholder indicating the
        model was found but prediction requires compute infrastructure.
        
        Args:
            db: Database session
            organization_id: Organization ID for multi-tenant isolation
            model_id: Model ID to use for prediction
            sample_ids: List of sample IDs to predict
            
        Returns:
            Prediction result dict
        """
        model = await self.get_model(db, organization_id, model_id)
        if not model:
            return {"error": "Model not found"}
        
        # In production, this would:
        # 1. Load the trained model weights
        # 2. Fetch spectral data for the samples
        # 3. Run inference
        # For now, return a placeholder indicating infrastructure needed
        return {
            "model_id": model_id,
            "model_name": model["name"],
            "target_trait": model["target_trait"],
            "sample_count": len(sample_ids),
            "status": "pending",
            "message": "Prediction requires compute infrastructure. Model found and validated.",
            "timestamp": datetime.now().isoformat()
        }
    
    async def get_spectral_data(
        self,
        db: AsyncSession,
        organization_id: int,
        dataset_id: str,
        sample_id: Optional[str] = None
    ) -> dict:
        """
        Get spectral data for visualization.
        
        Note: Actual spectral data would be stored in a separate
        time-series or blob storage system. This returns dataset
        metadata indicating the data structure.
        
        Args:
            db: Database session
            organization_id: Organization ID for multi-tenant isolation
            dataset_id: Dataset ID
            sample_id: Optional specific sample ID
            
        Returns:
            Spectral data metadata
        """
        dataset = await self.get_dataset(db, organization_id, dataset_id)
        if not dataset:
            return {"error": "Dataset not found"}
        
        return {
            "dataset_id": dataset_id,
            "dataset_name": dataset["name"],
            "platform": dataset["platform"],
            "wavelengths": dataset["wavelengths"],
            "total_samples": dataset["samples"],
            "status": "metadata_only",
            "message": "Spectral data stored in blob storage. Use data export API for full data."
        }
    
    async def get_statistics(
        self,
        db: AsyncSession,
        organization_id: int
    ) -> dict:
        """
        Get phenomic selection statistics.
        
        Args:
            db: Database session
            organization_id: Organization ID for multi-tenant isolation
            
        Returns:
            Statistics dict
        """
        # Count datasets
        dataset_stmt = select(func.count(PhenomicDataset.id)).where(
            PhenomicDataset.organization_id == organization_id
        )
        dataset_result = await db.execute(dataset_stmt)
        total_datasets = dataset_result.scalar() or 0
        
        # Count models
        model_stmt = select(func.count(PhenomicModel.id)).where(
            PhenomicModel.organization_id == organization_id
        )
        model_result = await db.execute(model_stmt)
        total_models = model_result.scalar() or 0
        
        # Count deployed models
        deployed_stmt = select(func.count(PhenomicModel.id)).where(
            PhenomicModel.organization_id == organization_id,
            PhenomicModel.status == "deployed"
        )
        deployed_result = await db.execute(deployed_stmt)
        deployed_models = deployed_result.scalar() or 0
        
        # Sum samples
        samples_stmt = select(func.sum(PhenomicDataset.samples)).where(
            PhenomicDataset.organization_id == organization_id
        )
        samples_result = await db.execute(samples_stmt)
        total_samples = samples_result.scalar() or 0
        
        # Get distinct platforms
        platforms_stmt = select(PhenomicDataset.platform).where(
            PhenomicDataset.organization_id == organization_id
        ).distinct()
        platforms_result = await db.execute(platforms_stmt)
        platforms = [p[0] for p in platforms_result.fetchall()]
        
        # Get distinct crops
        crops_stmt = select(PhenomicDataset.crop).where(
            PhenomicDataset.organization_id == organization_id
        ).distinct()
        crops_result = await db.execute(crops_stmt)
        crops = [c[0] for c in crops_result.fetchall()]
        
        # Calculate average accuracy
        avg_stmt = select(func.avg(PhenomicDataset.accuracy)).where(
            PhenomicDataset.organization_id == organization_id,
            PhenomicDataset.accuracy.isnot(None)
        )
        avg_result = await db.execute(avg_stmt)
        avg_accuracy = avg_result.scalar()
        
        return {
            "total_datasets": total_datasets,
            "total_models": total_models,
            "deployed_models": deployed_models,
            "total_samples": total_samples,
            "platforms": platforms,
            "crops": crops,
            "avg_accuracy": round(avg_accuracy, 2) if avg_accuracy else None
        }


# Singleton instance
phenomic_selection_service = PhenomicSelectionService()
