import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.modules.genotyping.services.vcf_import import vcf_service
from app.modules.bio_analytics.services.genomic_prediction import export_service
from app.models.core import User
from fastapi import UploadFile

# Mock user
mock_user = User(id=1, email="test@bijmantra.org", organization_id=1)

# Mock UploadFile
class MockUploadFile(UploadFile):
    def __init__(self, filename, path):
        self.filename = filename
        self.file = open(path, "rb")

async def test_import():
    engine = create_async_engine(settings.DATABASE_URL)
    AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with AsyncSessionLocal() as db:
        vcf_path = "test_data/test.vcf"
        upload_file = MockUploadFile("test.vcf", vcf_path)

        print("Starting VCF Import...")
        try:
            # 1. Import
            import_result = await vcf_service.import_vcf(
                db=db,
                user=mock_user,
                variant_set_name=f"Verification_Set_{os.getpid()}",
                vcf_file=upload_file
            )
            print("Import Success!")
            print(import_result)

            # 2. Train Model
            print("\nStarting Model Training (from storage)...")

            # Simulated phenotypes for the samples in VCF (Sample1, Sample2, Sample3)
            # Genotypes in VCF (test.vcf):
            # Sample1: 0, 1, 2 = 3 dosage
            # Sample2: 1, 2, 0 = 3 dosage
            # Sample3: 2, 0, 1 = 3 dosage
            # Let's give them random phenotypes
            phenos = {
                "Sample1": 10.5,
                "Sample2": 12.0,
                "Sample3": 9.8
            }

            train_result = await export_service.train_from_variant_set(
                db=db,
                user=mock_user,
                variant_set_id=import_result['variant_set_id'],
                model_name=f"Test_Model_{os.getpid()}",
                trait_name="Yield",
                phenotype_data=phenos,
                heritability=0.5
            )
            print("Training Success!")
            print(train_result)

        except Exception as e:
            print(f"Pipeline Failed: {e}")
            import traceback
            traceback.print_exc()
        finally:
            upload_file.file.close()

if __name__ == "__main__":
    asyncio.run(test_import())
