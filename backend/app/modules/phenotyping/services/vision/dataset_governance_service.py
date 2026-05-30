"""Governed Plant Vision dataset ingestion.

The governance service turns local, operator-acquired public dataset exports
into persisted, versioned manifests. It does not download data because several
agricultural datasets require manual acceptance of external terms.
"""

import hashlib
import json
import random
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from PIL import Image, UnidentifiedImageError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.vision import VisionDatasetAuditLog, VisionDatasetVersion
from app.modules.phenotyping.services.vision.datasets_service import (
    DatasetType,
    vision_dataset_service,
)
from app.modules.phenotyping.services.vision.public_dataset_catalog import (
    PROJECT_USE_OPEN_SOURCE_NON_COMMERCIAL,
    PublicVisionDataset,
    dataset_allows_project_use,
    get_public_dataset_catalog,
    normalize_label,
)


SUPPORTED_IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp"}
DEFAULT_SPLITS = {"train": 0.6, "val": 0.2, "test": 0.2}


def _version_code() -> str:
    return f"vision-dataset-version-{uuid4().hex[:12]}"


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return f"sha256:{digest.hexdigest()}"


def _sha256_json(payload: object) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return f"sha256:{hashlib.sha256(encoded).hexdigest()}"


def _find_catalog_entry(source_slug: str) -> PublicVisionDataset | None:
    return next(
        (entry for entry in get_public_dataset_catalog() if entry.slug == source_slug),
        None,
    )


class VisionDatasetGovernanceService:
    """License-aware ingestion and dataset versioning service."""

    def _discover_images(self, dataset_root: Path) -> list[Path]:
        return sorted(
            path
            for path in dataset_root.rglob("*")
            if path.is_file() and path.suffix.lower() in SUPPORTED_IMAGE_SUFFIXES
        )

    def _assign_splits(
        self,
        rows: list[dict],
        *,
        split_seed: int,
        train_split: float,
        val_split: float,
    ) -> list[dict]:
        grouped: dict[str, list[dict]] = defaultdict(list)
        for row in rows:
            grouped[row["canonical_label"]].append(row)

        rng = random.Random(split_seed)
        assigned: list[dict] = []
        for label_rows in grouped.values():
            label_rows = sorted(label_rows, key=lambda row: row["sha256"])
            rng.shuffle(label_rows)
            count = len(label_rows)
            train_count = max(1, round(count * train_split)) if count else 0
            val_count = max(0, round(count * val_split))
            if train_count + val_count > count:
                val_count = max(0, count - train_count)

            for index, row in enumerate(label_rows):
                if index < train_count:
                    split = "train"
                elif index < train_count + val_count:
                    split = "val"
                else:
                    split = "test"
                assigned.append({**row, "split": split})

        return sorted(assigned, key=lambda row: row["image_path"])

    def build_manifest(
        self,
        *,
        dataset_root: Path,
        source: PublicVisionDataset,
        crop: str,
        split_seed: int,
        train_split: float = DEFAULT_SPLITS["train"],
        val_split: float = DEFAULT_SPLITS["val"],
        preprocessing_version: str,
        project_use: str = PROJECT_USE_OPEN_SOURCE_NON_COMMERCIAL,
    ) -> dict:
        if not dataset_root.exists() or not dataset_root.is_dir():
            return {"error": f"Dataset root does not exist: {dataset_root}"}

        raw_rows: list[dict] = []
        for image_path in self._discover_images(dataset_root):
            original_label = image_path.parent.name
            normalized = normalize_label(original_label)
            canonical_label = normalized["normalized_condition"]
            try:
                with Image.open(image_path) as image:
                    image.verify()
                with Image.open(image_path) as image:
                    width, height = image.size
            except (UnidentifiedImageError, OSError) as exc:
                return {"error": f"Invalid image '{image_path}': {exc}"}

            raw_rows.append(
                {
                    "image_path": str(image_path.resolve()),
                    "filename": image_path.name,
                    "sha256": _sha256_file(image_path),
                    "source_slug": source.slug,
                    "source_name": source.name,
                    "source_url": source.source_url,
                    "source_license": source.license,
                    "source_license_url": source.license_url,
                    "license_verified": source.license_verified,
                    "allowed_uses": source.allowed_uses,
                    "project_use": project_use,
                    "commercial_use_allowed": source.commercial_use_allowed,
                    "requires_attribution": source.requires_attribution,
                    "requires_sharealike": source.requires_sharealike,
                    "requires_manual_access_acceptance": source.requires_manual_access_acceptance,
                    "source_version": "manual-export",
                    "original_label": original_label,
                    "normalized_crop": crop.lower().strip() or normalized["normalized_crop"],
                    "normalized_condition": normalized["normalized_condition"],
                    "canonical_label": canonical_label,
                    "is_healthy": normalized["is_healthy"],
                    "width": width,
                    "height": height,
                    "preprocessing_version": preprocessing_version,
                }
            )

        if not raw_rows:
            return {"error": f"No supported image files found under {dataset_root}"}

        rows = self._assign_splits(
            raw_rows,
            split_seed=split_seed,
            train_split=train_split,
            val_split=val_split,
        )
        class_distribution = dict(Counter(row["canonical_label"] for row in rows))
        split_distribution = dict(Counter(row["split"] for row in rows))
        source_checksum = _sha256_json([row["sha256"] for row in rows])
        manifest_checksum = _sha256_json(rows)

        return {
            "rows": rows,
            "source_checksum": source_checksum,
            "manifest_checksum": manifest_checksum,
            "class_distribution": class_distribution,
            "split_distribution": {
                "test": split_distribution.get("test", 0),
                "train": split_distribution.get("train", 0),
                "val": split_distribution.get("val", 0),
            },
            "classes": sorted(class_distribution),
        }

    async def _add_audit_log(
        self,
        db: AsyncSession,
        organization_id: int,
        *,
        dataset_id: str | int | None,
        event_type: str,
        actor: str | None,
        details: dict,
    ) -> None:
        db.add(
            VisionDatasetAuditLog(
                organization_id=organization_id,
                dataset_id=int(dataset_id) if dataset_id is not None else None,
                event_type=event_type,
                actor=actor,
                details=details,
            )
        )

    def _serialize_version(self, version: VisionDatasetVersion) -> dict:
        metadata = version.metadata_json or {}
        return {
            "id": str(version.id),
            "version_code": version.version_code,
            "dataset_id": str(version.dataset_id),
            "organization_id": version.organization_id,
            "source_slug": version.source_slug,
            "source_name": version.source_name,
            "source_url": version.source_url,
            "source_license": version.source_license,
            "source_license_url": version.source_license_url,
            "license_verified": version.license_verified,
            "source_version": version.source_version,
            "raw_root_uri": version.raw_root_uri,
            "source_checksum": version.source_checksum,
            "manifest_checksum": version.manifest_checksum,
            "preprocessing_version": version.preprocessing_version,
            "split_seed": version.split_seed,
            "image_count": version.image_count,
            "class_distribution": version.class_distribution or {},
            "split_distribution": version.split_distribution or {},
            "canonical_taxonomy": version.canonical_taxonomy or {},
            "allowed_uses": metadata.get("allowed_uses", []),
            "project_use": metadata.get("project_use"),
            "commercial_use_allowed": metadata.get("commercial_use_allowed", False),
            "requires_attribution": metadata.get("requires_attribution", True),
            "requires_sharealike": metadata.get("requires_sharealike", False),
            "requires_manual_access_acceptance": metadata.get(
                "requires_manual_access_acceptance", False
            ),
            "terms_accepted_by": metadata.get("terms_accepted_by"),
            "terms_acceptance_recorded_at": metadata.get("terms_acceptance_recorded_at"),
            "metadata": metadata,
            "created_by": version.created_by,
            "created_at": version.created_at.isoformat() if version.created_at else None,
        }

    def _serialize_audit_log(self, log: VisionDatasetAuditLog) -> dict:
        return {
            "id": str(log.id),
            "organization_id": log.organization_id,
            "dataset_id": str(log.dataset_id) if log.dataset_id is not None else None,
            "event_type": log.event_type,
            "actor": log.actor,
            "details": log.details or {},
            "created_at": log.created_at.isoformat() if log.created_at else None,
        }

    async def ingest_local_directory(
        self,
        db: AsyncSession,
        organization_id: int,
        *,
        dataset_root: Path,
        source_slug: str,
        dataset_name: str,
        crop: str,
        split_seed: int,
        preprocessing_version: str,
        created_by: str | None = None,
        project_use: str = PROJECT_USE_OPEN_SOURCE_NON_COMMERCIAL,
        terms_accepted_by: str | None = None,
        train_split: float = DEFAULT_SPLITS["train"],
        val_split: float = DEFAULT_SPLITS["val"],
        test_split: float = DEFAULT_SPLITS["test"],
    ) -> dict:
        source = _find_catalog_entry(source_slug)
        if not source:
            return {"error": "Dataset source is not in the approved public catalog"}
        if not dataset_allows_project_use(source, project_use):
            return {
                "error": "Dataset source terms are not approved for this project use",
                "source_slug": source.slug,
                "project_use": project_use,
                "allowed_uses": source.allowed_uses,
            }
        if source.requires_manual_access_acceptance and not terms_accepted_by:
            return {
                "error": "Dataset source requires manual access terms acceptance before ingestion",
                "source_slug": source.slug,
                "project_use": project_use,
                "license_url": source.license_url,
            }
        if abs(train_split + val_split + test_split - 1.0) > 0.01:
            return {"error": "Train, val, and test splits must sum to 1.0"}

        ingested_at = datetime.now(UTC).isoformat()
        manifest = self.build_manifest(
            dataset_root=dataset_root,
            source=source,
            crop=crop,
            split_seed=split_seed,
            train_split=train_split,
            val_split=val_split,
            preprocessing_version=preprocessing_version,
            project_use=project_use,
        )
        if "error" in manifest:
            return manifest

        dataset = await vision_dataset_service.create_dataset(
            db,
            organization_id,
            name=dataset_name,
            description=f"Governed ingestion from {source.name}",
            dataset_type=DatasetType.CLASSIFICATION,
            crop=crop,
            classes=manifest["classes"],
            train_split=train_split,
            val_split=val_split,
            test_split=test_split,
            created_by=created_by,
        )
        if "error" in dataset:
            return dataset

        await self._add_audit_log(
            db,
            organization_id,
            dataset_id=dataset["id"],
            event_type="dataset_ingestion_started",
            actor=created_by,
            details={
                "source_slug": source.slug,
                "source_license": source.license,
                "license_verified": source.license_verified,
                "allowed_uses": source.allowed_uses,
                "project_use": project_use,
                "commercial_use_allowed": source.commercial_use_allowed,
                "requires_attribution": source.requires_attribution,
                "requires_sharealike": source.requires_sharealike,
                "requires_manual_access_acceptance": source.requires_manual_access_acceptance,
                "terms_accepted_by": terms_accepted_by,
                "terms_acceptance_recorded_at": ingested_at if terms_accepted_by else None,
                "raw_root_uri": str(dataset_root.resolve()),
            },
        )
        await db.commit()

        images = [
            {
                "filename": row["filename"],
                "url": row["image_path"],
                "width": row["width"],
                "height": row["height"],
                "size_bytes": Path(row["image_path"]).stat().st_size,
                "split": row["split"],
                "metadata": {
                    "raw_path": row["image_path"],
                    "sha256": row["sha256"],
                    "source_slug": source.slug,
                    "source_name": source.name,
                    "source_url": source.source_url,
                    "source_license": source.license,
                    "source_license_url": source.license_url,
                    "license_verified": source.license_verified,
                    "allowed_uses": source.allowed_uses,
                    "project_use": project_use,
                    "commercial_use_allowed": source.commercial_use_allowed,
                    "requires_attribution": source.requires_attribution,
                    "requires_sharealike": source.requires_sharealike,
                    "requires_manual_access_acceptance": source.requires_manual_access_acceptance,
                    "terms_accepted_by": terms_accepted_by,
                    "terms_acceptance_recorded_at": ingested_at if terms_accepted_by else None,
                    "preprocessing_version": preprocessing_version,
                    "manifest_checksum": manifest["manifest_checksum"],
                },
                "annotation": {
                    "label": row["canonical_label"],
                    "crop": row["normalized_crop"],
                    "original_label": row["original_label"],
                    "is_healthy": row["is_healthy"],
                },
            }
            for row in manifest["rows"]
        ]
        image_result = await vision_dataset_service.add_images(
            db,
            organization_id,
            dataset_id=dataset["id"],
            images=images,
        )
        if "error" in image_result:
            return image_result

        version = VisionDatasetVersion(
            version_code=_version_code(),
            dataset_id=int(dataset["id"]),
            organization_id=organization_id,
            source_slug=source.slug,
            source_name=source.name,
            source_url=source.source_url,
            source_license=source.license,
            source_license_url=source.license_url,
            license_verified=source.license_verified,
            source_version="manual-export",
            raw_root_uri=str(dataset_root.resolve()),
            source_checksum=manifest["source_checksum"],
            manifest_checksum=manifest["manifest_checksum"],
            preprocessing_version=preprocessing_version,
            split_seed=split_seed,
            image_count=len(manifest["rows"]),
            class_distribution=manifest["class_distribution"],
            split_distribution=manifest["split_distribution"],
            canonical_taxonomy={
                "task": "classification",
                "crop": crop.lower().strip(),
                "classes": manifest["classes"],
            },
            metadata_json={
                "source_provenance": source.to_dict(),
                "allowed_uses": source.allowed_uses,
                "project_use": project_use,
                "commercial_use_allowed": source.commercial_use_allowed,
                "requires_attribution": source.requires_attribution,
                "requires_sharealike": source.requires_sharealike,
                "requires_manual_access_acceptance": source.requires_manual_access_acceptance,
                "terms_accepted_by": terms_accepted_by,
                "terms_acceptance_recorded_at": ingested_at if terms_accepted_by else None,
                "ingested_at": ingested_at,
            },
            created_by=created_by,
        )
        db.add(version)
        await db.flush()
        await self._add_audit_log(
            db,
            organization_id,
            dataset_id=dataset["id"],
            event_type="dataset_version_created",
            actor=created_by,
            details={
                "version_code": version.version_code,
                "manifest_checksum": manifest["manifest_checksum"],
                "image_count": len(manifest["rows"]),
                "class_distribution": manifest["class_distribution"],
                "split_distribution": manifest["split_distribution"],
            },
        )
        await db.commit()
        await db.refresh(version)

        refreshed_dataset = await vision_dataset_service.get_dataset(
            db,
            organization_id,
            dataset["id"],
        )
        return {
            "dataset": refreshed_dataset,
            "version": self._serialize_version(version),
            "images": image_result["images"],
        }

    async def list_audit_logs(
        self,
        db: AsyncSession,
        organization_id: int,
        dataset_id: str | int,
    ) -> list[dict]:
        result = await db.execute(
            select(VisionDatasetAuditLog)
            .where(
                VisionDatasetAuditLog.organization_id == organization_id,
                VisionDatasetAuditLog.dataset_id == int(dataset_id),
            )
            .order_by(VisionDatasetAuditLog.created_at.asc(), VisionDatasetAuditLog.id.asc())
        )
        return [self._serialize_audit_log(log) for log in result.scalars().all()]


vision_dataset_governance_service = VisionDatasetGovernanceService()
