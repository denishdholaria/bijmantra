import asyncio
import os
import shutil
from typing import Any

from fastapi import HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.core import User
from app.models.genotyping import CallSet, VariantSet


# Lazy imports — scikit-allel + zarr are heavy optional dependencies
# They are only needed when actually importing VCF files, not at module load
try:
    import allel as _allel
    import numpy as _np
    import zarr as _zarr
    _HAS_ALLEL = True
except ImportError:
    _allel = None  # type: ignore
    _zarr = None  # type: ignore
    _np = None  # type: ignore
    _HAS_ALLEL = False

DATA_DIR = "data/genotyping"


class VCFImportService:
    def __init__(self):
        os.makedirs(DATA_DIR, exist_ok=True)

    async def import_vcf(
        self,
        db: AsyncSession,
        user: User,
        variant_set_name: str,
        vcf_file: UploadFile,
        study_id: int = None
    ) -> dict[str, Any]:
        """
        Import a VCF file, convert to Zarr, and register in DB.
        """
        # 1. Save VCF to temp
        temp_path = f"{DATA_DIR}/temp_{vcf_file.filename}"

        def _save_vcf():
            with open(temp_path, "wb") as buffer:
                shutil.copyfileobj(vcf_file.file, buffer)

        await asyncio.to_thread(_save_vcf)

        try:
            if not _HAS_ALLEL:
                raise HTTPException(
                    status_code=501,
                    detail="VCF import requires scikit-allel and zarr packages. "
                    "Install with: pip install scikit-allel zarr",
                )

            # 2. Parse VCF using scikit-allel
            zarr_path = f"{DATA_DIR}/{variant_set_name}.zarr"

            def _process_vcf():
                if os.path.exists(zarr_path):
                    shutil.rmtree(zarr_path)

                # Convert VCF to Zarr directly (efficient for large files)
                _allel.vcf_to_zarr(temp_path, zarr_path, fields="*", overwrite=True)

                # Load metadata to verify and get counts
                callset = _zarr.open_group(zarr_path, mode="r")
                return (
                    callset["samples"][:],
                    callset["variants/POS"][:],
                    callset["variants/CHROM"][:],
                )

            samples, variants_pos, chromosomes = await asyncio.to_thread(_process_vcf)

            n_samples = len(samples)
            n_variants = len(variants_pos)

            # 3. Create VariantSet in DB
            variant_set = VariantSet(
                organization_id=user.organization_id,
                variant_set_name=variant_set_name,
                call_set_count=n_samples,
                variant_count=n_variants,
                storage_path=zarr_path,
                study_id=study_id,
                additional_info={
                    "importer": "scikit-allel",
                    "zarr_path": zarr_path,
                    "original_filename": vcf_file.filename,
                },
            )
            db.add(variant_set)
            await db.flush()

            # 4. Create CallSets (Samples)
            # Converting numpy bytes/str to python strings
            sample_names = [s.decode("utf-8") if isinstance(s, bytes) else s for s in samples]

            call_set_objs = []
            for s_name in sample_names:
                call_set_objs.append(
                    CallSet(
                        organization_id=user.organization_id,
                        call_set_name=s_name,
                        call_set_db_id=f"{variant_set.id}_{s_name}",  # simple ID gen
                        additional_info={"variant_set_id": variant_set.id},
                    )
                )

            # Batch insert call sets
            db.add_all(call_set_objs)

            # Link VariantSet <-> CallSet
            # We skip explicit Many-to-Many table population for now as it requires
            # iterating inputs which is slow. We assume implicit link via naming/metadata
            # or we can do it later.

            await db.commit()

            return {
                "success": True,
                "variant_set_id": variant_set.id,
                "sample_count": n_samples,
                "variant_count": n_variants,
                "storage_path": zarr_path,
            }

        except Exception as e:
            await db.rollback()
            raise HTTPException(status_code=500, detail=f"VCF Import Failed: {str(e)}")
        finally:
            # Cleanup temp VCF
            def _cleanup():
                if os.path.exists(temp_path):
                    os.remove(temp_path)

            await asyncio.to_thread(_cleanup)


vcf_service = VCFImportService()
