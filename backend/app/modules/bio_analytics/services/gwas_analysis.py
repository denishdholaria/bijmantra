from typing import List, Dict, Any, Optional
import numpy as np
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timezone
import json

from app.modules.bio_analytics.models import GWASRun, GWASResult
from app.models.core import User
from app.services.gwas import get_gwas_service

class GWASAnalysisService:
    """
    Service for running and persisting GWAS analyses.
    Wraps the core statistical logic.
    """

    async def run_gwas(
        self,
        db: AsyncSession,
        user: User,
        run_name: str,
        trait_name: str,
        method: str, # "glm" or "mlm"
        markers: List[Dict], # {points: name, chromosome, position}
        genotypes: List[List[float]],
        phenotypes: List[float],
        covariates: Optional[List[List[float]]] = None,
        kinship: Optional[List[List[float]]] = None
    ) -> Dict[str, Any]:
        """
        Run GWAS and save results.
        """
        # 1. Validation
        if len(phenotypes) != len(genotypes):
            return {"success": False, "error": "Dimension mismatch: phenotypes vs genotypes"}

        # 2. Run Analysis (Compute Bound)
        core_service = get_gwas_service()

        try:
            geno_arr = np.array(genotypes)
            pheno_arr = np.array(phenotypes)
            cov_arr = np.array(covariates) if covariates else None

            marker_names = [m["name"] for m in markers]
            chromosomes = [str(m["chromosome"]) for m in markers]
            positions = [int(m["position"]) for m in markers]

            if method.lower() == "mlm":
                if kinship is None:
                    kinship_arr = core_service.calculate_kinship(geno_arr)
                else:
                    kinship_arr = np.array(kinship)

                result = core_service.mlm_gwas(
                    genotypes=geno_arr,
                    phenotypes=pheno_arr,
                    kinship=kinship_arr,
                    marker_names=marker_names,
                    chromosomes=chromosomes,
                    positions=positions,
                    covariates=cov_arr
                )
            else:
                # Default GLM
                result = core_service.glm_gwas(
                    genotypes=geno_arr,
                    phenotypes=pheno_arr,
                    marker_names=marker_names,
                    chromosomes=chromosomes,
                    positions=positions,
                    covariates=cov_arr
                )

            # 3. Persist Results
            res_dict = result.to_dict()

            gwas_run = GWASRun(
                organization_id=user.organization_id,
                run_name=run_name,
                trait_name=trait_name,
                method=method.upper(),
                sample_size=result.n_samples,
                marker_count=result.n_markers,
                significance_threshold=result.significance_threshold,
                significant_marker_count=res_dict["n_significant"],
                manhattan_plot_data=res_dict["manhattan_data"], # Storing huge JSON blob
                qq_plot_data=res_dict["qq_data"]
            )
            db.add(gwas_run)
            await db.flush()

            # Save only significant or top hits to relational table
            # Storing ALL markers in SQL is anti-pattern (too many rows)
            # We suggest storing top 1000 + all significant

            # Filter logic: p < (threshold * 10) or top 1000
            # For simplicity, let's store significant markers + random subset if none

            sig_markers = []
            for i in range(result.n_markers):
                # Optimization: In real world, iterate numpy arrays, not python list loop
                p_val = result.p_values[i]
                if p_val < (result.significance_threshold * 100): # Relaxed threshold for viewing
                    sig_markers.append(GWASResult(
                        organization_id=user.organization_id,
                        run_id=gwas_run.id,
                        marker_name=result.marker_names[i],
                        chromosome=result.chromosomes[i],
                        position=result.positions[i],
                        p_value=p_val,
                        neg_log10_p=-np.log10(p_val) if p_val > 0 else 300,
                        effect_size=result.effect_sizes[i],
                        standard_error=result.standard_errors[i],
                        maf=result.maf[i],
                        is_significant=p_val < result.significance_threshold
                    ))

            # Batch Insert
            if sig_markers:
                batch_size = 5000
                for i in range(0, len(sig_markers), batch_size):
                    db.add_all(sig_markers[i:i+batch_size])

            await db.commit()

            return {
                "success": True,
                "run_id": gwas_run.id,
                "significant_markers": res_dict["n_significant"]
            }

        except Exception as e:
            await db.rollback()
            return {"success": False, "error": str(e)}

gwas_service = GWASAnalysisService()
