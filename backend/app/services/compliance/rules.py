from app.schemas.compliance import SeedBatchInfo, ComplianceType

# Mock standards for demonstration
CROP_STANDARDS = {
    "Wheat": {"germination": 85.0, "purity": 98.0, "moisture": 14.0},
    "Maize": {"germination": 90.0, "purity": 99.0, "moisture": 14.0},
    "Rice": {"germination": 80.0, "purity": 98.0, "moisture": 13.0},
}

ISTA_CROPS = ["Wheat", "Maize", "Rice", "Barley", "Soybean"]
OECD_COUNTRIES = ["India", "USA", "France", "Germany", "Australia", "Canada"]

def check_ista_rules(batch: SeedBatchInfo) -> list[str]:
    errors = []
    if batch.crop not in ISTA_CROPS:
        errors.append(f"Crop {batch.crop} is not covered by ISTA rules.")

    # Check if standards exist
    if batch.crop in CROP_STANDARDS:
        std = CROP_STANDARDS[batch.crop]
        if batch.purity_percentage < std["purity"]:
             errors.append(f"Purity {batch.purity_percentage}% is below ISTA standard {std['purity']}%.")

    return errors

def check_oecd_scheme(batch: SeedBatchInfo) -> list[str]:
    errors = []
    if batch.origin_country not in OECD_COUNTRIES:
        errors.append(f"Origin {batch.origin_country} is not a participating OECD country.")

    if not batch.variety:
        errors.append("Variety must be specified for OECD certification.")

    return errors

def validate_germination(batch: SeedBatchInfo) -> list[str]:
    errors = []
    if batch.crop in CROP_STANDARDS:
        std = CROP_STANDARDS[batch.crop]
        if batch.germination_percentage < std["germination"]:
            errors.append(f"Germination {batch.germination_percentage}% is below standard {std['germination']}%.")
    else:
        # Default fallback
        if batch.germination_percentage < 75.0:
            errors.append(f"Germination {batch.germination_percentage}% is below general standard 75.0%.")

    return errors

def validate_batch(batch: SeedBatchInfo, compliance_type: ComplianceType) -> dict:
    errors = []

    # Common validation
    errors.extend(validate_germination(batch))

    if compliance_type == ComplianceType.ISTA:
        errors.extend(check_ista_rules(batch))
    elif compliance_type == ComplianceType.OECD:
        errors.extend(check_oecd_scheme(batch))

    return {
        "valid": len(errors) == 0,
        "errors": errors
    }
