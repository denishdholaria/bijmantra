import pytest
import time
from app.schemas.compliance import SeedBatchInfo, ComplianceType
from app.services.compliance.rules import validate_batch
from app.services.compliance.pdf_generator import calculate_hash, generate_certificate_pdf

@pytest.fixture
def sample_batch():
    return SeedBatchInfo(
        batch_id="TEST-001",
        crop="Wheat",
        variety="SuperWheat",
        weight_kg=1000.0,
        germination_percentage=95.0,
        purity_percentage=99.0,
        moisture_percentage=12.0,
        origin_country="India"
    )

def test_rules_engine_valid(sample_batch):
    result = validate_batch(sample_batch, ComplianceType.ISTA)
    assert result["valid"] is True

def test_rules_engine_invalid_germination(sample_batch):
    sample_batch.germination_percentage = 50.0
    result = validate_batch(sample_batch, ComplianceType.ISTA)
    assert result["valid"] is False
    assert any("Germination" in err for err in result["errors"])

def test_rules_engine_invalid_crop_ista(sample_batch):
    sample_batch.crop = "AlienPlant"
    result = validate_batch(sample_batch, ComplianceType.ISTA)
    assert result["valid"] is False
    assert any("not covered by ISTA" in err for err in result["errors"])

def test_hash_calculation(sample_batch):
    hash1 = calculate_hash(sample_batch, ComplianceType.ISTA)
    time.sleep(0.01) # Ensure timestamp differs
    hash2 = calculate_hash(sample_batch, ComplianceType.ISTA)
    assert hash1 != hash2

def test_pdf_generation(sample_batch):
    cert_hash = "test_hash"
    pdf = generate_certificate_pdf(
        batch=sample_batch,
        compliance_type=ComplianceType.ISTA,
        issuer_name="Test Issuer",
        certificate_hash=cert_hash,
        verification_url="http://test.com"
    )
    assert len(pdf) > 0
    assert pdf.startswith(b"%PDF")
