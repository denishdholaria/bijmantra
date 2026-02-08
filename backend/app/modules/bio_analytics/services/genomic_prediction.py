from typing import List, Dict, Any, Optional
import numpy as np
from scipy import linalg
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timezone
import uuid

from app.modules.bio_analytics.models import GSModel, MarkerEffect, GEBVPrediction
from app.models.core import User
from app.models.genotyping import VariantSet

# Lazy imports — zarr + scikit-allel are heavy optional dependencies
try:
    import zarr as _zarr
    import allel as _allel
    _HAS_GENOMIC_DEPS = True
except ImportError:
    _zarr = None  # type: ignore
    _allel = None  # type: ignore
    _HAS_GENOMIC_DEPS = False
import asyncio


class GenomicPredictionService:
    """
    Service for Genomic Prediction using RR-BLUP and GBLUP.
    Handles model training, persistence, and prediction.
    """

    async def train_rrblup_model(
        self,
        db: AsyncSession,
        user: User,
        model_name: str,
        trait_name: str,
        markers: List[List[int]], # Matrix (0,1,2)
        phenotypes: List[float],
        marker_names: List[str],
        germplasm_ids: List[str],
        heritability: float = 0.5
    ) -> Dict[str, Any]:
        """
        Train a Ridge Regression BLUP (RR-BLUP) model.
        Estimates marker effects directly.
        
        Model: y = Xb + Zu + e
        RR-BLUP: u ~ N(0, I*sigma_u^2)
        """
        
        # 1. Prepare Data
        M = np.array(markers) # n_ind x n_markers
        y = np.array(phenotypes)
        n_ind, n_markers = M.shape
        
        # 2. Impute missing (naive mean imputation for now)
        # In real world, use proper imputation service
        if np.isnan(M).any():
             col_mean = np.nanmean(M, axis=0)
             inds = np.where(np.isnan(M))
             M[inds] = np.take(col_mean, inds[1])
             
        # 3. Calculate Allele Frequences & Center Z matrix
        # p = frequency of allele '1'
        p = np.mean(M, axis=0) / 2.0
        Z = M - 2 * p
        
        # 4. RR-BLUP Solution
        # Mixed Model Equations (MME) simplification for RR-BLUP:
        # [Z'Z + I*lambda] * a = Z'y
        # lambda = sigma_e^2 / sigma_a^2 = (1-h^2)/h^2 * (var_p?) -> Approx (1-h^2)/(h^2/m)
        
        # Ridge parameter lambda
        # Standard parametrization: lambda = var_e / var_marker
        # Using heritability h^2: var_g = h^2 * var_p, var_e = (1-h^2) * var_p
        # var_marker = var_g / n_markers (assuming equal contribution)
        # lambda = var_e / (var_g / n_markers) = n_markers * (1-h^2)/h^2
        
        var_p = np.var(y)
        lambda_val = n_markers * (1 - heritability) / heritability
        
        # Centering y
        mu = np.mean(y)
        y_centered = y - mu
        
        # Build LHS and RHS
        # LHS = Z'Z + I*lambda
        ZtZ = np.dot(Z.T, Z)
        I = np.eye(n_markers)
        LHS = ZtZ + (I * lambda_val)
        
        # RHS = Z'y
        RHS = np.dot(Z.T, y_centered)
        
        try:
            # Solve for marker effects (a)
            marker_effects = linalg.solve(LHS, RHS)
            
            # Predict GEBVs for training set
            # gebv = mu + Z * a
            gebv = mu + np.dot(Z, marker_effects)
            
            # Calculate accuracy (correlation between y and gebv)
            accuracy = float(np.corrcoef(y, gebv)[0, 1])
            
            # 5. Persist Model
            gs_model = GSModel(
                organization_id=user.organization_id,
                model_name=model_name,
                trait_name=trait_name,
                method="RR-BLUP",
                training_population_size=n_ind,
                marker_count=n_markers,
                accuracy=accuracy,
                heritability=heritability,
                genetic_variance=float(np.var(gebv)),
                error_variance=float(np.var(y - gebv)),
                is_active=True
            )
            db.add(gs_model)
            await db.flush() # get ID
            
            # 6. Persist Marker Effects (Batch insert)
            # This can be huge, so might need optimization for 50k chips
            # For now, assuming manageable size or limit
            effects_objs = []
            for i, effect in enumerate(marker_effects):
                effects_objs.append(MarkerEffect(
                    organization_id=user.organization_id,
                    model_id=gs_model.id,
                    marker_name=marker_names[i] if i < len(marker_names) else f"M{i}",
                    effect=float(effect),
                    position=i
                ))
            
            # Chunked insert if large
            batch_size = 1000
            for i in range(0, len(effects_objs), batch_size):
                db.add_all(effects_objs[i:i+batch_size])
                
            # 7. Persist GEBVs
            preds_objs = []
            for i, val in enumerate(gebv):
                preds_objs.append(GEBVPrediction(
                    organization_id=user.organization_id,
                    model_id=gs_model.id,
                    germplasm_id=germplasm_ids[i] if i < len(germplasm_ids) else f"UNK-{i}",
                    gebv=float(val),
                    reliability=0.0 # Approximation needed for RR-BLUP reliability
                ))
            db.add_all(preds_objs)
            
            await db.commit()
            
            return {
                "success": True,
                "model_id": gs_model.id,
                "accuracy": accuracy,
                "marker_effects_count": len(marker_effects)
            }
            
        except linalg.LinAlgError as e:
            await db.rollback()
            return {"success": False, "error": str(e)}

    async def train_from_variant_set(
        self,
        db: AsyncSession,
        user: User,
        variant_set_id: int,
        model_name: str,
        trait_name: str,
        phenotype_data: Dict[str, float], # {sample_name: value}
        heritability: float = 0.5
    ) -> Dict[str, Any]:
        """
        Train a model using data directly from Genotyping storage (Zarr).
        Efficiently loads genotype matrix and intersects with phenotypes.
        """
        # 1. Get VariantSet info
        variant_set = await db.get(VariantSet, variant_set_id)
        if not variant_set:
            raise ValueError("VariantSet not found")
            
        if not variant_set.storage_path:
            raise ValueError("VariantSet has no storage path")
            
        # 2. Load Data (in thread to avoid blocking)
        def load_and_align():
            if not _HAS_GENOMIC_DEPS:
                raise ValueError(
                    "Genomic prediction from Zarr requires scikit-allel and zarr. "
                    "Install with: pip install scikit-allel zarr"
                )
            callset = _zarr.open_group(variant_set.storage_path, mode='r')
            
            # Load samples
            # samples are usually bytes in Zarr from VCF
            raw_samples = callset['samples'][:]
            sample_names = [s.decode('utf-8') if isinstance(s, bytes) else str(s) for s in raw_samples]
            
            # Load Genotypes
            # calldata/GT shape: (variants, samples, ploidy)
            gt = _allel.GenotypeArray(callset['calldata/GT'])
            
            # Convert to dosage (0,1,2) -> shape (variants, samples)
            # We want (samples, variants) for the model
            n_alt = gt.to_n_alt(fill=-1) # -1 for missing
            dosage = n_alt.T # Now (samples, variants)
            
            # 3. Intersect Phenotypes and Genotypes
            # Find indices of samples that exist in both
            keep_indices = []
            aligned_y = []
            aligned_ids = []
            
            for i, s_name in enumerate(sample_names):
                if s_name in phenotype_data:
                    keep_indices.append(i)
                    aligned_y.append(phenotype_data[s_name])
                    aligned_ids.append(s_name)
            
            # Minimum sample size check (relaxed for testing)
            if len(keep_indices) < 2:
                raise ValueError(f"Insufficient overlap between Genotypes and Phenotypes. Found {len(keep_indices)} matches.")
                
            # Filter Genotype Matrix
            M_filtered = dosage[keep_indices, :]
            
            # Load Marker Names (optional, for result mapping)
            # Typically 'variants/ID' or created from POS
            if 'variants/ID' in callset:
                marker_ids = callset['variants/ID'][:]
                marker_names = [m.decode('utf-8') if isinstance(m, bytes) else str(m) for m in marker_ids]
            else:
                positions = callset['variants/POS'][:]
                chroms = callset['variants/CHROM'][:]
                marker_names = [f"{c}_{p}" for c, p in zip(chroms, positions)]
                
            return M_filtered, aligned_y, marker_names, aligned_ids
            
        # Run heavy lifting in thread
        M, y, m_names, germ_ids = await asyncio.to_thread(load_and_align)
        
        # 4. Delegate to training logic
        return await self.train_rrblup_model(
            db=db,
            user=user,
            model_name=model_name,
            trait_name=trait_name,
            markers=M.tolist(), # Convert back to list for compatibility (or update train to accept numpy)
            phenotypes=y,
            marker_names=m_names,
            germplasm_ids=germ_ids,
            heritability=heritability
        )

    async def predict_new(
        self,
        db: AsyncSession,
        user: User,
        model_id: int,
        markers: List[List[int]], 
        germplasm_ids: List[str]
    ) -> Dict[str, Any]:
        """
        Predict GEBVs for new lines using stored marker effects.
        GEBV = sum(marker_genotype * marker_effect)
        """
        # Load model and effects
        model = await db.get(GSModel, model_id)
        if not model:
            raise ValueError("Model not found")
            
        # Fetch effects (ordered by position/id - MUST MATCH input marker order)
        # Warning: This assumes input markers match validation order exactly.
        # In production, we'd alignment by marker names.
        stmt = select(MarkerEffect).where(MarkerEffect.model_id == model_id).order_by(MarkerEffect.position)
        result = await db.execute(stmt)
        effects = result.scalars().all()
        
        effect_vector = np.array([e.effect for e in effects])
        
        # Calculate
        M = np.array(markers)
        # Note: We should center M using the Training Population means (p) ideally.
        # If we just do M * effect, we capture the additive value relative to 0, 
        # but often we want relative to population mean.
        # For simplicity in this v1:
        gebvs = np.dot(M, effect_vector)
        
        return {
            "predictions": [
                {"id": gid, "gebv": float(val)} 
                for gid, val in zip(germplasm_ids, gebvs)
            ]
        }

export_service = GenomicPredictionService()
