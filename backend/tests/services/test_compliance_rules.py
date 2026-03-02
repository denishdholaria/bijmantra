import pytest
from app.schemas.compliance import SeedBatchInfo
from app.services.compliance.rules import check_oecd_scheme, OECD_COUNTRIES

@pytest.fixture
def base_batch():
    return SeedBatchInfo(
        batch_id="TEST-BATCH",
        crop="Wheat",
        variety="Variety A",
        weight_kg=100.0,
        germination_percentage=98.0,
        purity_percentage=99.0,
        moisture_percentage=12.0,
        origin_country="USA",
    )

def test_oecd_valid_country_and_variety(base_batch):
    """Test that a valid OECD country and variety returns no errors."""
    # Ensure USA is in OECD_COUNTRIES for the base case
    assert "USA" in OECD_COUNTRIES
    errors = check_oecd_scheme(base_batch)
    assert len(errors) == 0

def test_oecd_invalid_country(base_batch):
    """Test that an invalid country returns an error."""
    base_batch.origin_country = "InvalidCountry"
    errors = check_oecd_scheme(base_batch)
    assert len(errors) == 1
    assert "Origin InvalidCountry is not a participating OECD country." in errors[0]

def test_oecd_missing_variety(base_batch):
    """Test that a missing variety returns an error."""
    base_batch.variety = ""
    errors = check_oecd_scheme(base_batch)
    assert len(errors) == 1
    assert "Variety must be specified for OECD certification." in errors[0]

def test_oecd_invalid_country_and_missing_variety(base_batch):
    """Test that both invalid country and missing variety return errors."""
    base_batch.origin_country = "InvalidCountry"
    base_batch.variety = ""
    errors = check_oecd_scheme(base_batch)
    assert len(errors) == 2
    assert any("Origin InvalidCountry is not a participating OECD country." in err for err in errors)
    assert any("Variety must be specified for OECD certification." in err for err in errors)

def test_oecd_all_oecd_countries(base_batch):
    """Test that all defined OECD countries are considered valid."""
    for country in OECD_COUNTRIES:
        base_batch.origin_country = country
        errors = check_oecd_scheme(base_batch)
        assert len(errors) == 0, f"Country {country} should be valid"
