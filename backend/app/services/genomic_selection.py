"""
Genomic Selection Service

Provides GS model training, GEBV prediction, and selection tools
for genomic-assisted breeding programs.

Methods:
- GBLUP: Genomic BLUP (individual-based, estimates GEBVs from G-matrix)
- rrBLUP: Ridge Regression BLUP (marker-based, estimates marker effects directly)
- Cross-validation: k-fold CV for prediction accuracy assessment
- Persistence: Save and load trained models via GSModel

This service queries real database data.
"""

from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from app.models.germplasm import Germplasm
from app.models.genotyping import CallSet, Call, Variant, VariantSet
from app.models.phenotyping import Observation, ObservationVariable
from app.models.core import Program, Trial, Study
from app.models.biometrics import BiometricsGSModel as GSModel
import numpy as np
from scipy import linalg, stats
import logging

logger = logging.getLogger(__name__)


class GenomicSelectionService:
    """
    Service for genomic selection analysis.
    
    Genomic Selection (GS) uses genome-wide marker data to predict
    breeding values without requiring phenotypic data on selection candidates.
    
    Key Methods:
    - GBLUP: Genomic Best Linear Unbiased Prediction
    - BayesA/B/C: Bayesian regression methods
    - RKHS: Reproducing Kernel Hilbert Space
    
    GEBV Calculation:
        GEBV = Σ(marker_effect × genotype)
    
    Selection Response:
        R = i × r × σg
        
        Where:
        - i = selection intensity
        - r = prediction accuracy
        - σg = genetic standard deviation
    """
    
    def calculate_g_matrix(
        self,
        markers: List[List[int]],
        ploidy: int = 2
    ) -> Dict[str, Any]:
        """
        Calculate VanRaden Genomic Relationship Matrix (G).

        G = ZZ' / 2Σp(1-p)

        Where:
        - Z = M - P (Centered genotype matrix)
        - M = Marker matrix (0, 1, 2)
        - P = 2(p - 0.5) matrix where p is allele frequency

        Args:
            markers: Genotype matrix (n_ind x n_markers)
            ploidy: Ploidy level (default 2)

        Returns:
            Dictionary with G matrix and stats
        """
        M = np.array(markers)
        n_ind, n_markers = M.shape

        # Calculate allele frequencies
        # If M has values 0, 1, 2. Sum / (2*N) = p.
        p = np.sum(M, axis=0) / (ploidy * n_ind)

        # Z = M - 2p (for diploid)
        Z = M - (ploidy * p)

        # Denominator: 2 * sum(p * (1-p))
        denominator = ploidy * np.sum(p * (1 - p))

        if denominator == 0:
            return {
                "matrix": np.zeros((n_ind, n_ind)).tolist(),
                "mean_diagonal": 0.0,
                "n_markers_used": n_markers
            }

        # G = ZZ' / denominator
        G = np.dot(Z, Z.T) / denominator

        return {
            "matrix": G.tolist(),
            "mean_diagonal": float(np.mean(np.diag(G))),
            "n_markers_used": n_markers
        }

    def run_gblup(
        self,
        phenotypes: List[float],
        g_matrix: List[List[float]],
        heritability: float
    ) -> Dict[str, Any]:
        """
        Run GBLUP analysis.

        Args:
            phenotypes: Vector of phenotypes (y)
            g_matrix: Genomic relationship matrix (G)
            heritability: Trait heritability (h^2)

        Returns:
            Dictionary with GEBVs and stats
        """
        y = np.array(phenotypes)
        G = np.array(g_matrix)
        n = len(y)

        # Lambda = (1 - h^2) / h^2
        lambda_val = (1 - heritability) / heritability

        # Mean centering
        mu = np.mean(y)
        y_centered = y - mu

        I = np.eye(n)
        V_star = G + I * lambda_val

        try:
            # Step 1: Solve V_star * x = y_centered
            x = linalg.solve(V_star, y_centered)

            # Step 2: u_hat = G * x
            gebv = np.dot(G, x)

            # Reliability calculation
            # Reliability = 1 - lambda * diag(V_star^-1 * G)
            M_inv_G = linalg.solve(V_star, G)
            reliabilities = 1 - lambda_val * np.diag(M_inv_G)

            # Clip reliabilities to [0, 1] just in case of numerical issues
            reliabilities = np.clip(reliabilities, 0.0, 1.0)

            # Variance of GEBVs
            var_gebv = float(np.var(gebv))

            # Error variance
            residuals = y_centered - gebv
            var_e = float(np.var(residuals))

            return {
                "gebv": gebv.tolist(),
                "reliability": reliabilities.tolist(),
                "genetic_variance": var_gebv,
                "error_variance": var_e,
                "mean": float(mu)
            }

        except linalg.LinAlgError:
             return {
                "gebv": [0.0] * n,
                "reliability": [0.0] * n,
                "genetic_variance": 0.0,
                "error_variance": 0.0,
                "mean": float(mu),
                "error": "Singular matrix encountered"
            }

    def run_rrblup(
        self,
        markers: List[List[int]],
        phenotypes: List[float],
        ploidy: int = 2,
    ) -> Dict[str, Any]:
        """
        Ridge Regression BLUP (rrBLUP) — marker-effect model.

        Estimates individual marker effects directly, complementing
        GBLUP which estimates individual breeding values.

        Model:
            y = 1μ + Zα + ε

        Where:
            Z = centered marker matrix (n × m)
            α = marker effects (m × 1)
            λ = σ²_e / σ²_α  (shrinkage parameter)

        Solution:
            α̂ = (Z'Z + λI)⁻¹ Z'(y - 1μ̂)
            GEBV = Z × α̂

        Variance Components (spectral decomposition):
            σ²_α = σ²_g / m  (genetic variance per marker)
            σ²_e = (1 - h²) × σ²_p
            λ = σ²_e / σ²_α

        Reference:
            Endelman, J.B. (2011). Ridge regression and other kernels
            for genomic selection with R package rrBLUP. Plant Genome 4:250-255.

        Args:
            markers: Genotype matrix (n_ind × n_markers), coded 0/1/2
            phenotypes: Phenotypic observations (n_ind,)
            ploidy: Ploidy level (default 2 for diploid)

        Returns:
            Dictionary with marker effects, GEBVs, variance components,
            and per-marker significance tests
        """
        M = np.array(markers, dtype=float)
        y = np.array(phenotypes, dtype=float)
        n, m = M.shape

        if n != len(y):
            return {"error": f"Dimension mismatch: {n} genotypes vs {len(y)} phenotypes"}

        if n < 3:
            return {"error": "Need at least 3 individuals for rrBLUP"}

        # 1. Calculate allele frequencies and center marker matrix
        p = np.mean(M, axis=0) / ploidy
        Z = M - (ploidy * p)

        # 2. Estimate variance components via spectral decomposition
        # Following Kang et al. (2008) / rrBLUP::mixed.solve()
        mu_hat = np.mean(y)
        y_centered = y - mu_hat

        # Eigendecomposition of ZZ' for efficient REML
        ZZt = Z @ Z.T
        eigenvalues, eigenvectors = np.linalg.eigh(ZZt)
        eigenvalues = np.maximum(eigenvalues, 0)  # Numerical stability

        # Transform observations
        Uty = eigenvectors.T @ y_centered

        # Grid search for lambda (ratio σ²_e/σ²_α)
        # Optimize REML log-likelihood
        best_lambda = 1.0
        best_ll = -np.inf

        for log_lambda in np.linspace(-5, 5, 100):
            lam = np.exp(log_lambda)
            denom = eigenvalues + lam
            denom = np.maximum(denom, 1e-10)

            # REML log-likelihood (up to constant)
            ll = -0.5 * np.sum(np.log(denom)) - \
                 0.5 * (n - 1) * np.log(np.sum(Uty**2 / denom))

            if ll > best_ll:
                best_ll = ll
                best_lambda = lam

        # 3. Estimate variance components from optimal lambda
        denom_opt = eigenvalues + best_lambda
        var_e = np.sum(Uty**2 / denom_opt) / (n - 1)
        var_alpha = var_e / best_lambda  # Per-marker genetic variance
        var_g = var_alpha * m  # Total genetic variance
        heritability = var_g / (var_g + var_e)

        # 4. Solve for marker effects: α̂ = (Z'Z + λI)⁻¹ Z'y_centered
        ZtZ = Z.T @ Z
        reg_matrix = ZtZ + best_lambda * np.eye(m)

        try:
            marker_effects = linalg.solve(reg_matrix, Z.T @ y_centered)
        except linalg.LinAlgError:
            return {"error": "Singular matrix in rrBLUP solve"}

        # 5. Calculate GEBVs
        gebvs = Z @ marker_effects

        # 6. Per-marker significance tests
        # SE of marker effects: sqrt(diag((Z'Z + λI)⁻¹) × σ²_e)
        try:
            reg_inv_diag = np.diag(linalg.inv(reg_matrix))
            se_effects = np.sqrt(np.abs(reg_inv_diag) * var_e)
            t_stats = marker_effects / np.maximum(se_effects, 1e-10)
            p_values = 2 * (1 - stats.t.cdf(np.abs(t_stats), df=n - 1))
        except linalg.LinAlgError:
            se_effects = np.full(m, np.nan)
            p_values = np.full(m, np.nan)

        # 7. Proportion of variance explained per marker
        # PVE_i ≈ 2pᵢ(1-pᵢ) × α̂ᵢ² / σ²_p
        var_p = np.var(y)
        pve = ploidy * p * (1 - p) * marker_effects**2 / max(var_p, 1e-10)

        # 8. Reliability of GEBVs
        # r² = 1 - PEV/Vg ≈ cor(GEBV, y)²
        if np.std(gebvs) > 0 and np.std(y_centered) > 0:
            accuracy = float(np.corrcoef(gebvs, y_centered)[0, 1])
        else:
            accuracy = 0.0

        return {
            "marker_effects": marker_effects.tolist(),
            "se_effects": se_effects.tolist(),
            "p_values": p_values.tolist(),
            "pve": pve.tolist(),
            "gebv": gebvs.tolist(),
            "mean": float(mu_hat),
            "accuracy": accuracy,
            "variance_components": {
                "var_marker": float(var_alpha),
                "var_genetic": float(var_g),
                "var_residual": float(var_e),
                "heritability": float(heritability),
                "lambda": float(best_lambda),
            },
            "n_individuals": n,
            "n_markers": m,
            "n_significant_markers": int(np.sum(p_values < 0.05)),
            "method": "rrBLUP",
        }

    def cross_validate(
        self,
        markers: List[List[int]],
        phenotypes: List[float],
        method: str = "gblup",
        n_folds: int = 5,
        n_repeats: int = 1,
        seed: int = 42,
    ) -> Dict[str, Any]:
        """
        k-fold cross-validation for genomic selection models.

        Evaluates prediction accuracy by training on (k-1) folds
        and predicting the held-out fold.

        Predictive Ability:
            r = cor(GEBV_pred, y_observed)

        Prediction Accuracy:
            r / h  (where h = sqrt(heritability))

        Reference:
            Lorenz et al. (2011) Potential and Optimization of Genomic
            Selection. Crop Science 51:397-408.

        Args:
            markers: Genotype matrix (n_ind × n_markers), coded 0/1/2
            phenotypes: Phenotypic observations (n_ind,)
            method: "gblup" or "rrblup"
            n_folds: Number of CV folds (default 5)
            n_repeats: Number of repeated CV rounds (default 1)
            seed: Random seed for reproducibility

        Returns:
            Dictionary with per-fold accuracies, mean, SE,
            and overall predictive ability
        """
        M = np.array(markers, dtype=float)
        y = np.array(phenotypes, dtype=float)
        n = len(y)

        if n < n_folds:
            return {"error": f"Need at least {n_folds} individuals for {n_folds}-fold CV"}

        rng = np.random.RandomState(seed)
        all_accuracies = []

        for rep in range(n_repeats):
            # Shuffle indices for this repeat
            indices = rng.permutation(n)
            folds = np.array_split(indices, n_folds)

            for fold_idx in range(n_folds):
                test_idx = folds[fold_idx]
                train_idx = np.concatenate(
                    [folds[j] for j in range(n_folds) if j != fold_idx]
                )

                M_train = M[train_idx]
                y_train = y[train_idx]
                M_test = M[test_idx]
                y_test = y[test_idx]

                try:
                    if method == "rrblup":
                        # Train rrBLUP on training set
                        result = self.run_rrblup(
                            M_train.tolist(), y_train.tolist()
                        )
                        if "error" in result:
                            all_accuracies.append(0.0)
                            continue

                        effects = np.array(result["marker_effects"])
                        mu = result["mean"]

                        # Predict test set: GEBV = Z_test × α̂
                        p_train = np.mean(M_train, axis=0) / 2
                        Z_test = M_test - 2 * p_train
                        predicted = Z_test @ effects + mu

                    else:  # gblup
                        # Build G-matrix from training set
                        g_result = self.calculate_g_matrix(M_train.tolist())
                        G_train = np.array(g_result["matrix"])

                        # Run GBLUP on training set
                        h2_est = 0.5  # Default; could be estimated
                        gblup_result = self.run_gblup(
                            y_train.tolist(), G_train.tolist(), h2_est
                        )
                        if "error" in gblup_result:
                            all_accuracies.append(0.0)
                            continue

                        gebv_train = np.array(gblup_result["gebv"])
                        mu = gblup_result["mean"]

                        # Predict test from G_train_test relationship
                        # G_test_train = Z_test × Z_train' / denom
                        p_all = np.mean(M_train, axis=0) / 2
                        Z_train = M_train - 2 * p_all
                        Z_test = M_test - 2 * p_all
                        denom = 2 * np.sum(p_all * (1 - p_all))
                        denom = max(denom, 1e-10)

                        G_test_train = (Z_test @ Z_train.T) / denom
                        G_train_inv_approx = G_train + (
                            (1 - h2_est) / h2_est
                        ) * np.eye(len(y_train))

                        # GEBV_test = G_test_train × V⁻¹ × y_centered
                        y_centered_train = y_train - mu
                        v = linalg.solve(G_train_inv_approx, y_centered_train)
                        predicted = G_test_train @ v + mu

                    # Calculate fold accuracy
                    if len(y_test) > 1 and np.std(predicted) > 0 and np.std(y_test) > 0:
                        r = float(np.corrcoef(predicted, y_test)[0, 1])
                        if np.isnan(r):
                            r = 0.0
                    else:
                        r = 0.0

                    all_accuracies.append(r)

                except Exception as e:
                    logger.warning(f"CV fold {fold_idx} failed: {e}")
                    all_accuracies.append(0.0)

        accuracies = np.array(all_accuracies)
        mean_accuracy = float(np.mean(accuracies))
        se_accuracy = float(np.std(accuracies) / np.sqrt(len(accuracies)))

        return {
            "method": method,
            "n_folds": n_folds,
            "n_repeats": n_repeats,
            "per_fold_accuracy": accuracies.tolist(),
            "mean_accuracy": mean_accuracy,
            "se_accuracy": se_accuracy,
            "ci_lower": mean_accuracy - 1.96 * se_accuracy,
            "ci_upper": mean_accuracy + 1.96 * se_accuracy,
            "n_individuals": n,
            "n_markers": M.shape[1],
        }

    async def list_models(
        self,
        db: AsyncSession,
        organization_id: int,
        trait: Optional[str] = None,
        method: Optional[str] = None,
        status: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        List GS models with optional filters.
        
        Currently returns empty list as GS model storage is not yet implemented.
        Future: Query gs_models table when created.
        
        Args:
            db: Database session
            organization_id: Organization ID for multi-tenant filtering
            trait: Filter by trait name
            method: Filter by GS method (GBLUP, BayesB, etc.)
            status: Filter by model status (trained, training, failed)
        
        Returns:
            List of GS model dictionaries
        """
        if status:
            stmt = stmt.where(GSModel.status == status)
        if trait:
            stmt = stmt.where(GSModel.trait_name == trait)
        if method:
            stmt = stmt.where(GSModel.method == method)
            
        result = await db.execute(stmt)
        models = result.scalars().all()
        
        return [
            {
                "id": str(m.id),
                "model_db_id": m.model_db_id,
                "name": m.model_name,
                "trait": m.trait_name,
                "method": m.method,
                "engine": m.engine,
                "accuracy": m.accuracy,
                "status": m.status,
                "created_at": m.created_at.isoformat() if m.created_at else None,
                "metrics": m.metrics
            }
            for m in models
        ]
    
    async def get_model(
        self,
        db: AsyncSession,
        organization_id: int,
        model_id: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Get a single GS model by ID.
        
        Args:
            db: Database session
            organization_id: Organization ID for multi-tenant filtering
            model_id: GS model identifier
        
        Returns:
            GS model dictionary or None if not found
        """
        stmt = (
            select(GSModel)
            .where(GSModel.organization_id == organization_id)
            .where(GSModel.id == int(model_id))
        )
        
        result = await db.execute(stmt)
        model = result.scalar_one_or_none()
        
        if not model:
            return None
            
        return {
            "id": str(model.id),
            "model_db_id": model.model_db_id,
            "name": model.model_name,
            "trait": model.trait_name,
            "method": model.method,
            "engine": model.engine,
            "training_population_size": model.training_population_size,
            "marker_count": model.marker_count,
            "cv_folds": model.cv_folds,
            "accuracy": model.accuracy,
            "heritability": model.heritability,
            "genetic_variance": model.genetic_variance,
            "error_variance": model.error_variance,
            "metrics": model.metrics,
            "file_path": model.file_path,
            "status": model.status,
            "error_message": model.error_message,
            "created_at": model.created_at.isoformat() if model.created_at else None,
            "updated_at": model.updated_at.isoformat() if model.updated_at else None,
        }

    async def create_model_record(
        self,
        db: AsyncSession,
        organization_id: int,
        model_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create a new GS model record.
        """
        import uuid
        
        new_model = GSModel(
            organization_id=organization_id,
            model_db_id=model_data.get("model_db_id", str(uuid.uuid4())),
            model_name=model_data["name"],
            trait_name=model_data["trait"],
            method=model_data["method"],
            engine=model_data.get("engine", "sklearn"),
            training_population_size=model_data.get("training_population_size"),
            marker_count=model_data.get("marker_count"),
            cv_folds=model_data.get("cv_folds", 5),
            training_set_ids=model_data.get("training_set_ids"),
            accuracy=model_data.get("accuracy"),
            heritability=model_data.get("heritability"),
            genetic_variance=model_data.get("genetic_variance"),
            error_variance=model_data.get("error_variance"),
            metrics=model_data.get("metrics"),
            file_path=model_data.get("file_path"),
            status=model_data.get("status", "TRAINING")
        )
        
        db.add(new_model)
        await db.commit()
        await db.refresh(new_model)
        
        return {"id": str(new_model.id), "status": "created"}
    
    async def get_predictions(
        self,
        db: AsyncSession,
        organization_id: int,
        model_id: str,
        min_gebv: Optional[float] = None,
        min_reliability: Optional[float] = None,
        selected_only: bool = False,
    ) -> List[Dict[str, Any]]:
        """
        Get GEBV predictions for a model.
        
        GEBV (Genomic Estimated Breeding Value):
            GEBV = Σ(aᵢ × gᵢ)
            
            Where:
            - aᵢ = effect of marker i
            - gᵢ = genotype at marker i (0, 1, or 2)
        
        Reliability:
            r² = 1 - (PEV / σ²g)
            
            Where:
            - PEV = Prediction Error Variance
            - σ²g = Genetic variance
        
        Args:
            db: Database session
            organization_id: Organization ID for multi-tenant filtering
            model_id: GS model identifier
            min_gebv: Minimum GEBV threshold
            min_reliability: Minimum reliability threshold
            selected_only: Return only selected candidates
        
        Returns:
            List of GEBV prediction dictionaries
        """
        # GEBV predictions table not yet implemented
        return []
    
    async def get_yield_predictions(
        self,
        db: AsyncSession,
        organization_id: int,
        environment: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get yield predictions from genomic models.
        
        Args:
            db: Database session
            organization_id: Organization ID for multi-tenant filtering
            environment: Filter by environment type
        
        Returns:
            List of yield prediction dictionaries
        """
        # Yield predictions table not yet implemented
        return []
    
    async def get_model_comparison(
        self,
        db: AsyncSession,
        organization_id: int,
    ) -> List[Dict[str, Any]]:
        """
        Compare accuracy across GS models.
        
        Model Accuracy:
            r = cor(GEBV, TBV)
            
            Where:
            - GEBV = Genomic Estimated Breeding Value
            - TBV = True Breeding Value (from validation)
        
        Args:
            db: Database session
            organization_id: Organization ID for multi-tenant filtering
        
        Returns:
            List of model comparison dictionaries
        """
        # GS models table not yet implemented
        return []
    
    def calculate_selection_response(
        self,
        accuracy: float,
        heritability: float,
        selection_intensity: float = 0.1,
        genetic_std: float = 1.5,
    ) -> Dict[str, Any]:
        """
        Calculate expected selection response.
        
        Selection Response Formula:
            R = i × r × σg
            
            Where:
            - i = selection intensity (from selection proportion)
            - r = prediction accuracy (correlation between GEBV and TBV)
            - σg = genetic standard deviation
        
        Selection Intensity (i) for common proportions:
            - Top 1%: i ≈ 2.67
            - Top 5%: i ≈ 2.06
            - Top 10%: i ≈ 1.76
            - Top 20%: i ≈ 1.40
            - Top 50%: i ≈ 0.80
        
        Args:
            accuracy: Prediction accuracy (0-1)
            heritability: Trait heritability (0-1)
            selection_intensity: Proportion selected (0-1)
            genetic_std: Genetic standard deviation
        
        Returns:
            Dictionary with selection response metrics
        """
        # Calculate selection intensity from proportion
        # Using approximation: i ≈ 2.67 - 1.87 × p (for p < 0.5)
        if selection_intensity <= 0.01:
            i = 2.67
        elif selection_intensity <= 0.05:
            i = 2.06
        elif selection_intensity <= 0.10:
            i = 1.755
        elif selection_intensity <= 0.20:
            i = 1.40
        else:
            i = 0.80
        
        # Calculate response
        response = i * accuracy * genetic_std
        
        return {
            "selection_intensity": selection_intensity,
            "selection_differential": round(i, 3),
            "accuracy": accuracy,
            "heritability": heritability,
            "genetic_variance": round(genetic_std ** 2, 3),
            "expected_response": round(response, 3),
            "response_percent": round((response / 5) * 100, 1),  # Assuming mean of 5
        }
    
    async def get_cross_predictions(
        self,
        db: AsyncSession,
        organization_id: int,
        parent1_id: str,
        parent2_id: str,
    ) -> Dict[str, Any]:
        """
        Predict progeny performance from cross.
        
        Mid-Parent Value:
            μ = (GEBV₁ + GEBV₂) / 2
        
        Mendelian Sampling Variance:
            σ²ms = 0.5 × σ²g × (1 - F)
            
            Where:
            - σ²g = genetic variance
            - F = average inbreeding of parents
        
        Args:
            db: Database session
            organization_id: Organization ID for multi-tenant filtering
            parent1_id: First parent germplasm ID
            parent2_id: Second parent germplasm ID
        
        Returns:
            Dictionary with cross prediction metrics
        """
        # Query parent germplasm
        stmt1 = select(Germplasm).where(
            Germplasm.organization_id == organization_id,
            Germplasm.germplasm_db_id == parent1_id
        )
        stmt2 = select(Germplasm).where(
            Germplasm.organization_id == organization_id,
            Germplasm.germplasm_db_id == parent2_id
        )
        
        result1 = await db.execute(stmt1)
        result2 = await db.execute(stmt2)
        
        parent1 = result1.scalar_one_or_none()
        parent2 = result2.scalar_one_or_none()
        
        if not parent1 or not parent2:
            return {"error": "One or both parents not found"}
        
        # GEBV data not yet stored in database
        # Return structure with null values
        return {
            "parent1": {
                "id": parent1_id,
                "name": parent1.germplasm_name,
                "gebv": None,  # Not yet implemented
            },
            "parent2": {
                "id": parent2_id,
                "name": parent2.germplasm_name,
                "gebv": None,  # Not yet implemented
            },
            "mid_parent_value": None,
            "progeny_mean": None,
            "progeny_variance": None,
            "progeny_std": None,
            "top_10_percent_expected": None,
            "probability_exceeds_best_parent": None,
            "note": "GEBV data not yet available. Train a GS model first.",
        }
    
    async def get_summary(
        self,
        db: AsyncSession,
        organization_id: int,
    ) -> Dict[str, Any]:
        """
        Get summary statistics for genomic selection.
        
        Args:
            db: Database session
            organization_id: Organization ID for multi-tenant filtering
        
        Returns:
            Dictionary with summary statistics
        """
        # Count germplasm with genotype data
        stmt = select(func.count(CallSet.id)).where(
            CallSet.organization_id == organization_id
        )
        result = await db.execute(stmt)
        genotyped_count = result.scalar() or 0
        
        # Count variants
        stmt_variants = select(func.count(Variant.id)).where(
            Variant.organization_id == organization_id
        )
        result_variants = await db.execute(stmt_variants)
        variant_count = result_variants.scalar() or 0
        
        return {
            "total_models": 0,  # GS models table not yet implemented
            "trained_models": 0,
            "training_models": 0,
            "average_accuracy": None,
            "best_model": None,
            "traits_covered": [],
            "methods_used": [],
            "total_predictions": 0,
            "selected_candidates": 0,
            "genotyped_samples": genotyped_count,
            "total_variants": variant_count,
            "note": "GS model storage not yet implemented. Use /api/v2/compute/gblup for real-time GBLUP calculations.",
        }
    
    def get_methods(self) -> List[Dict[str, Any]]:
        """
        Get available GS methods.
        
        Returns:
            List of available genomic selection methods
        """
        return [
            {
                "id": "gblup",
                "name": "GBLUP",
                "description": "Genomic Best Linear Unbiased Prediction (individual-based)",
                "formula": "GEBV = G × (G + λI)⁻¹ × y",
                "requirements": ["genotype_matrix", "phenotypes"],
                "status": "available",
            },
            {
                "id": "rrblup",
                "name": "rrBLUP",
                "description": "Ridge Regression BLUP (marker-effect model)",
                "formula": "α̂ = (Z'Z + λI)⁻¹ Z'y, GEBV = Zα̂",
                "requirements": ["genotype_matrix", "phenotypes"],
                "status": "available",
            },
            {
                "id": "bayesa",
                "name": "BayesA",
                "description": "Bayesian regression with scaled inverse chi-square prior",
                "formula": "y = μ + Σ(xᵢ × aᵢ) + e",
                "requirements": ["genotype_matrix", "phenotypes"],
                "status": "planned",
            },
            {
                "id": "bayesb",
                "name": "BayesB",
                "description": "Bayesian regression with mixture prior (π markers have zero effect)",
                "formula": "y = μ + Σ(xᵢ × aᵢ × δᵢ) + e",
                "requirements": ["genotype_matrix", "phenotypes"],
                "status": "planned",
            },
            {
                "id": "bayesc",
                "name": "BayesC",
                "description": "Bayesian regression with common variance",
                "formula": "y = μ + Σ(xᵢ × aᵢ) + e, aᵢ ~ N(0, σ²)",
                "requirements": ["genotype_matrix", "phenotypes"],
                "status": "planned",
            },
            {
                "id": "rkhs",
                "name": "RKHS",
                "description": "Reproducing Kernel Hilbert Space for non-additive effects",
                "formula": "y = μ + K × α + e",
                "requirements": ["genotype_matrix", "phenotypes"],
                "status": "planned",
            },
            {
                "id": "rf",
                "name": "Random Forest",
                "description": "Machine learning ensemble method",
                "requirements": ["genotype_matrix", "phenotypes"],
                "status": "planned",
            },
            {
                "id": "multitrait",
                "name": "Multi-trait",
                "description": "Multi-trait genomic selection using correlated traits",
                "formula": "GEBV = G × (G + R⁻¹ ⊗ λI)⁻¹ × y",
                "requirements": ["genotype_matrix", "phenotypes", "trait_correlations"],
                "status": "planned",
            },
        ]
    
    async def get_traits(
        self,
        db: AsyncSession,
        organization_id: int,
    ) -> List[str]:
        """
        Get available traits for genomic selection.
        
        Args:
            db: Database session
            organization_id: Organization ID for multi-tenant filtering
        
        Returns:
            List of trait names
        """
        stmt = select(ObservationVariable.trait_name).where(
            ObservationVariable.organization_id == organization_id
        ).distinct()
        
        result = await db.execute(stmt)
        traits = [row[0] for row in result.fetchall() if row[0]]
        
        return sorted(traits)


# Factory function for dependency injection
def get_genomic_selection_service() -> GenomicSelectionService:
    """Get the genomic selection service instance."""
    return GenomicSelectionService()
