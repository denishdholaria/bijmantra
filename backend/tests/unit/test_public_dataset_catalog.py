from pathlib import Path

from app.modules.phenotyping.services.vision.public_dataset_catalog import (
    PROJECT_USE_COMMERCIAL,
    PROJECT_USE_OPEN_SOURCE_NON_COMMERCIAL,
    build_manifest_row,
    dataset_allows_project_use,
    get_public_dataset_catalog,
    normalize_label,
)


def test_public_dataset_catalog_entries_have_required_provenance():
    catalog = get_public_dataset_catalog()

    assert len(catalog) >= 5
    for entry in catalog:
        assert entry.name
        assert entry.source_url.startswith("https://")
        assert entry.license
        assert isinstance(entry.allowed_uses, list)
        assert isinstance(entry.commercial_use_allowed, bool)
        assert entry.task_types
        assert entry.quality_concerns
        assert entry.preprocessing
        assert entry.rank >= 1


def test_normalize_label_splits_crop_condition_and_health():
    label = normalize_label("Tomato___Late_blight")

    assert label["normalized_crop"] == "tomato"
    assert label["normalized_condition"] == "late_blight"
    assert label["is_healthy"] is False

    healthy = normalize_label("Apple healthy")
    assert healthy["normalized_crop"] == "apple"
    assert healthy["normalized_condition"] == "healthy"
    assert healthy["is_healthy"] is True


def test_build_manifest_row_preserves_source_and_original_label():
    catalog = get_public_dataset_catalog()
    plantvillage = next(entry for entry in catalog if entry.slug == "plantvillage")

    row = build_manifest_row(
        dataset=plantvillage,
        image_path=Path("/data/PlantVillage/Tomato___Late_blight/leaf001.jpg"),
        original_label="Tomato___Late_blight",
        split="train",
    )

    assert row["source_name"] == plantvillage.name
    assert row["source_url"] == plantvillage.source_url
    assert row["source_license"] == plantvillage.license
    assert PROJECT_USE_OPEN_SOURCE_NON_COMMERCIAL in row["allowed_uses"]
    assert row["commercial_use_allowed"] is True
    assert row["original_label"] == "Tomato___Late_blight"
    assert row["normalized_crop"] == "tomato"
    assert row["normalized_condition"] == "late_blight"
    assert row["split"] == "train"


def test_catalog_policy_distinguishes_noncommercial_and_commercial_use():
    catalog = get_public_dataset_catalog()
    cassava = next(entry for entry in catalog if entry.slug == "cassava-leaf-disease")
    plant_pathology = next(entry for entry in catalog if entry.slug == "plant-pathology-fgvc")

    assert dataset_allows_project_use(cassava, PROJECT_USE_OPEN_SOURCE_NON_COMMERCIAL) is True
    assert dataset_allows_project_use(cassava, PROJECT_USE_COMMERCIAL) is False
    assert cassava.commercial_use_allowed is False

    assert (
        dataset_allows_project_use(plant_pathology, PROJECT_USE_OPEN_SOURCE_NON_COMMERCIAL) is False
    )
    assert dataset_allows_project_use(plant_pathology, "academic_research") is True
