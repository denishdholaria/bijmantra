"""Public Plant Vision dataset catalog and label normalization helpers."""

import re
from dataclasses import asdict, dataclass
from pathlib import Path


PROJECT_USE_OPEN_SOURCE_NON_COMMERCIAL = "open_source_non_commercial"
PROJECT_USE_ACADEMIC_RESEARCH = "academic_research"
PROJECT_USE_COMPETITION = "competition"
PROJECT_USE_COMMERCIAL = "commercial"


@dataclass(frozen=True)
class PublicVisionDataset:
    slug: str
    rank: int
    name: str
    source_url: str
    license: str
    license_url: str
    license_verified: bool
    allowed_uses: list[str]
    commercial_use_allowed: bool
    requires_attribution: bool
    requires_sharealike: bool
    requires_manual_access_acceptance: bool
    task_types: list[str]
    crops_or_scope: list[str]
    image_count_note: str
    classes_note: str
    quality_concerns: list[str]
    preprocessing: list[str]
    provenance_notes: str

    def to_dict(self) -> dict:
        return asdict(self)


PUBLIC_DATASETS = [
    PublicVisionDataset(
        slug="plantvillage",
        rank=1,
        name="PlantVillage",
        source_url="https://huggingface.co/datasets/mohanty/PlantVillage",
        license="CC-BY-SA-3.0",
        license_url="https://creativecommons.org/licenses/by-sa/3.0/",
        license_verified=True,
        allowed_uses=[
            PROJECT_USE_OPEN_SOURCE_NON_COMMERCIAL,
            PROJECT_USE_ACADEMIC_RESEARCH,
            PROJECT_USE_COMMERCIAL,
        ],
        commercial_use_allowed=True,
        requires_attribution=True,
        requires_sharealike=True,
        requires_manual_access_acceptance=False,
        task_types=["classification"],
        crops_or_scope=[
            "apple",
            "corn",
            "grape",
            "potato",
            "tomato",
            "multi-crop",
        ],
        image_count_note="Original release is commonly cited at about 54k leaf images.",
        classes_note="Crop-condition compound disease and healthy labels.",
        quality_concerns=[
            "controlled backgrounds",
            "leaf-centered images",
            "field generalization risk",
        ],
        preprocessing=[
            "split crop-condition labels",
            "preserve original label text",
            "reserve field-like datasets for validation",
        ],
        provenance_notes=(
            "Use for bootstrap training with ShareAlike obligations tracked; "
            "field robustness still requires external validation."
        ),
    ),
    PublicVisionDataset(
        slug="plant-pathology-fgvc",
        rank=2,
        name="Plant Pathology FGVC",
        source_url="https://www.kaggle.com/competitions/plant-pathology-2020-fgvc7",
        license="kaggle-competition-terms",
        license_url="https://www.kaggle.com/competitions/plant-pathology-2020-fgvc7/rules",
        license_verified=True,
        allowed_uses=[PROJECT_USE_ACADEMIC_RESEARCH, PROJECT_USE_COMPETITION],
        commercial_use_allowed=False,
        requires_attribution=True,
        requires_sharealike=False,
        requires_manual_access_acceptance=True,
        task_types=["classification", "multi-label-classification"],
        crops_or_scope=["apple"],
        image_count_note="Low-thousands competition image scale.",
        classes_note="Healthy, scab, rust, and multi-disease labels.",
        quality_concerns=["narrow crop scope", "competition-specific access terms"],
        preprocessing=["preserve multi-label rows", "stratify validation by label combination"],
        provenance_notes="Manual download through Kaggle required.",
    ),
    PublicVisionDataset(
        slug="cassava-leaf-disease",
        rank=3,
        name="Cassava Leaf Disease",
        source_url="https://www.kaggle.com/competitions/cassava-leaf-disease-classification",
        license="kaggle-competition-terms",
        license_url="https://www.kaggle.com/competitions/cassava-leaf-disease-classification/rules",
        license_verified=True,
        allowed_uses=[PROJECT_USE_OPEN_SOURCE_NON_COMMERCIAL, PROJECT_USE_ACADEMIC_RESEARCH],
        commercial_use_allowed=False,
        requires_attribution=True,
        requires_sharealike=False,
        requires_manual_access_acceptance=True,
        task_types=["classification"],
        crops_or_scope=["cassava"],
        image_count_note="Commonly referenced at about 21k labeled training images.",
        classes_note="Cassava bacterial blight, brown streak, green mite, mosaic, healthy.",
        quality_concerns=["single-crop scope", "competition-specific access terms"],
        preprocessing=["preserve label map", "stratify split by disease class"],
        provenance_notes="Manual download through Kaggle required.",
    ),
    PublicVisionDataset(
        slug="plantdoc",
        rank=4,
        name="PlantDoc",
        source_url="https://github.com/pratikkayal/PlantDoc-Dataset",
        license="CC-BY-4.0",
        license_url="https://creativecommons.org/licenses/by/4.0/",
        license_verified=True,
        allowed_uses=[
            PROJECT_USE_OPEN_SOURCE_NON_COMMERCIAL,
            PROJECT_USE_ACADEMIC_RESEARCH,
            PROJECT_USE_COMMERCIAL,
        ],
        commercial_use_allowed=True,
        requires_attribution=True,
        requires_sharealike=False,
        requires_manual_access_acceptance=False,
        task_types=["classification", "detection"],
        crops_or_scope=["multi-crop"],
        image_count_note="Common references describe about 2.5k field-like images.",
        classes_note="Multiple crop and disease labels with noisier field imagery.",
        quality_concerns=["small dataset", "label noise", "broken references possible"],
        preprocessing=[
            "deduplicate",
            "validate image files",
            "preserve bounding boxes where available",
        ],
        provenance_notes="Useful as field robustness validation data.",
    ),
    PublicVisionDataset(
        slug="cvppp-leaf-segmentation",
        rank=5,
        name="CVPPP Leaf Segmentation",
        source_url="https://www.plant-phenotyping.org/datasets-home",
        license="academic-challenge-terms",
        license_url="https://www.plant-phenotyping.org/datasets-home",
        license_verified=False,
        allowed_uses=[],
        commercial_use_allowed=False,
        requires_attribution=True,
        requires_sharealike=False,
        requires_manual_access_acceptance=True,
        task_types=["segmentation"],
        crops_or_scope=["arabidopsis", "tobacco", "phenotyping"],
        image_count_note="Small benchmark subsets with careful mask annotations.",
        classes_note="Leaf instance masks rather than disease classes.",
        quality_concerns=["controlled imaging", "not disease diagnosis"],
        preprocessing=["convert masks to segmentation manifest", "keep series metadata"],
        provenance_notes="Best for future growth and leaf-instance segmentation work.",
    ),
    PublicVisionDataset(
        slug="ip102",
        rank=6,
        name="IP102 Pest Recognition",
        source_url="https://github.com/xpwu95/IP102",
        license="verify-academic-dataset-terms",
        license_url="https://github.com/xpwu95/IP102",
        license_verified=False,
        allowed_uses=[],
        commercial_use_allowed=False,
        requires_attribution=True,
        requires_sharealike=False,
        requires_manual_access_acceptance=True,
        task_types=["classification"],
        crops_or_scope=["pests"],
        image_count_note="Commonly cited at about 75k images across 102 pest classes.",
        classes_note="Pest taxa labels, not crop disease labels.",
        quality_concerns=["taxonomic label complexity", "not disease-only"],
        preprocessing=["map taxonomy separately from crop labels", "review class imbalance"],
        provenance_notes="Future pest extension dataset.",
    ),
    PublicVisionDataset(
        slug="deepweeds",
        rank=7,
        name="DeepWeeds",
        source_url="https://github.com/AlexOlsen/DeepWeeds",
        license="verify-repository-and-publication-terms",
        license_url="https://github.com/AlexOlsen/DeepWeeds",
        license_verified=False,
        allowed_uses=[],
        commercial_use_allowed=False,
        requires_attribution=True,
        requires_sharealike=False,
        requires_manual_access_acceptance=True,
        task_types=["classification"],
        crops_or_scope=["weeds"],
        image_count_note="Commonly cited at about 17k images.",
        classes_note="Eight weed species plus negative class in common references.",
        quality_concerns=["weed scope, not leaf disease", "geography-specific imagery"],
        preprocessing=["preserve species labels", "keep location metadata if available"],
        provenance_notes="Future weed scouting extension dataset.",
    ),
]


def get_public_dataset_catalog() -> list[PublicVisionDataset]:
    return sorted(PUBLIC_DATASETS, key=lambda entry: entry.rank)


def dataset_allows_project_use(
    dataset: PublicVisionDataset,
    project_use: str = PROJECT_USE_OPEN_SOURCE_NON_COMMERCIAL,
) -> bool:
    if not dataset.license_verified:
        return False
    return project_use in dataset.allowed_uses


def normalize_label(label: str) -> dict:
    original = label.strip()
    cleaned = original.replace("___", " ").replace("__", " ").replace("_", " ")
    cleaned = re.sub(r"[^A-Za-z0-9]+", " ", cleaned).strip().lower()
    parts = cleaned.split()

    if not parts:
        return {
            "normalized_crop": "unknown",
            "normalized_condition": "unknown",
            "is_healthy": False,
        }

    crop = parts[0]
    condition_parts = parts[1:] or ["unknown"]
    condition = "_".join(condition_parts)
    if "healthy" in condition_parts:
        condition = "healthy"

    return {
        "normalized_crop": crop,
        "normalized_condition": condition,
        "is_healthy": condition == "healthy",
    }


def build_manifest_row(
    *,
    dataset: PublicVisionDataset,
    image_path: Path,
    original_label: str,
    split: str,
) -> dict:
    normalized = normalize_label(original_label)
    return {
        "dataset_id": dataset.slug,
        "source_name": dataset.name,
        "source_url": dataset.source_url,
        "source_license": dataset.license,
        "source_license_url": dataset.license_url,
        "source_license_verified": dataset.license_verified,
        "allowed_uses": dataset.allowed_uses,
        "commercial_use_allowed": dataset.commercial_use_allowed,
        "requires_attribution": dataset.requires_attribution,
        "requires_sharealike": dataset.requires_sharealike,
        "requires_manual_access_acceptance": dataset.requires_manual_access_acceptance,
        "source_version": "manual-export",
        "image_path": str(image_path),
        "original_label": original_label,
        "task_type": dataset.task_types[0],
        "split": split,
        "provenance_notes": dataset.provenance_notes,
        **normalized,
    }
