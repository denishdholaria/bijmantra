"""Plant Vision upload validation and fail-closed inference facade."""

import os
import time
from dataclasses import asdict, dataclass
from io import BytesIO
from pathlib import Path
from typing import Any

import joblib
from PIL import Image, UnidentifiedImageError

from app.modules.phenotyping.services.vision.artifact_utils import validate_artifact_checksum
from app.modules.phenotyping.services.vision.baseline_training import features_from_bytes


@dataclass(frozen=True)
class ValidatedImage:
    filename: str
    content_type: str
    format: str
    width: int
    height: int
    size_bytes: int
    quality_warnings: list[str]


class VisionImageValidationError(ValueError):
    """Validation error carrying the HTTP status the API should return."""

    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.status_code = status_code


class VisionInferenceService:
    allowed_mime_types = {
        "image/jpeg": {"JPEG"},
        "image/png": {"PNG"},
        "image/webp": {"WEBP"},
    }
    max_file_size_bytes = 10 * 1024 * 1024
    min_recommended_dimension = 128
    max_dimension = 12000

    def __init__(self) -> None:
        self._model_cache: dict[tuple[str, str], Any] = {}

    def _clean_filename(self, filename: str) -> str:
        cleaned = os.path.basename(filename or "").replace("\x00", "").strip()
        return cleaned or "upload"

    def _quality_warnings(self, image: Image.Image) -> list[str]:
        warnings: list[str] = []
        width, height = image.size
        if width < self.min_recommended_dimension or height < self.min_recommended_dimension:
            warnings.append("image_resolution_below_recommended_minimum")

        sample = image.convert("L").resize((1, 1))
        luminance = sample.getpixel((0, 0))
        if luminance < 35:
            warnings.append("image_appears_underexposed")
        elif luminance > 235:
            warnings.append("image_appears_overexposed")

        return warnings

    def validate_image_upload(
        self,
        *,
        filename: str,
        content_type: str | None,
        payload: bytes,
    ) -> ValidatedImage:
        if not payload:
            raise VisionImageValidationError("Image payload is empty")

        if len(payload) > self.max_file_size_bytes:
            raise VisionImageValidationError(
                "Image exceeds the 10 MB upload limit", status_code=413
            )

        normalized_content_type = (content_type or "").split(";")[0].strip().lower()
        if normalized_content_type not in self.allowed_mime_types:
            raise VisionImageValidationError(f"Unsupported image MIME type '{content_type}'")

        try:
            with Image.open(BytesIO(payload)) as image:
                image.verify()
            with Image.open(BytesIO(payload)) as image:
                image.load()
                image_format = image.format or ""
                if image_format not in self.allowed_mime_types[normalized_content_type]:
                    raise VisionImageValidationError(
                        f"Image format '{image_format}' does not match MIME type '{normalized_content_type}'"
                    )
                width, height = image.size
                if width <= 0 or height <= 0:
                    raise VisionImageValidationError("Image dimensions are invalid")
                if width > self.max_dimension or height > self.max_dimension:
                    raise VisionImageValidationError("Image dimensions exceed the supported limit")
                warnings = self._quality_warnings(image)
        except VisionImageValidationError:
            raise
        except (UnidentifiedImageError, OSError) as exc:
            raise VisionImageValidationError("Invalid or corrupted image") from exc

        return ValidatedImage(
            filename=self._clean_filename(filename),
            content_type=normalized_content_type,
            format=image_format,
            width=width,
            height=height,
            size_bytes=len(payload),
            quality_warnings=warnings,
        )

    async def analyze_image(
        self,
        *,
        filename: str,
        content_type: str | None,
        payload: bytes,
        organization_id: int,
        crop: str | None = None,
        model: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        started = time.perf_counter()
        image = self.validate_image_upload(
            filename=filename,
            content_type=content_type,
            payload=payload,
        )

        if not model:
            return {
                "status": "runtime_unavailable",
                "image": asdict(image),
                "predictions": [],
                "explainability": {
                    "message": (
                        "Image validated, but no production Plant Vision runtime is deployed "
                        "for this organization."
                    ),
                    "crop": crop,
                    "organization_id": organization_id,
                },
                "model": None,
                "latency_ms": round((time.perf_counter() - started) * 1000, 2),
            }

        lifecycle_state = model.get("lifecycle_state")
        if lifecycle_state and lifecycle_state != "production":
            return {
                "status": "runtime_unavailable",
                "image": asdict(image),
                "predictions": [],
                "explainability": {
                    "message": "Selected model is not approved for production inference.",
                    "crop": crop,
                    "organization_id": organization_id,
                    "lifecycle_state": lifecycle_state,
                },
                "model": model,
                "latency_ms": round((time.perf_counter() - started) * 1000, 2),
            }

        if not model.get("runtime_available"):
            return {
                "status": "runtime_unavailable",
                "image": asdict(image),
                "predictions": [],
                "explainability": {
                    "message": "Selected model has no configured inference runtime.",
                    "crop": crop,
                    "organization_id": organization_id,
                },
                "model": model,
                "latency_ms": round((time.perf_counter() - started) * 1000, 2),
            }

        if model.get("format") != "sklearn_image_classifier":
            return {
                "status": "runtime_unavailable",
                "image": asdict(image),
                "predictions": [],
                "explainability": {
                    "message": "Selected model format has no registered inference adapter.",
                    "crop": crop,
                    "organization_id": organization_id,
                },
                "model": model,
                "latency_ms": round((time.perf_counter() - started) * 1000, 2),
            }

        artifact_dir = Path(model.get("file_path") or "")
        artifact_checksum = model.get("artifact_checksum")
        if not artifact_dir.exists() or not validate_artifact_checksum(
            artifact_dir,
            artifact_checksum,
        ):
            return {
                "status": "runtime_unavailable",
                "image": asdict(image),
                "predictions": [],
                "explainability": {
                    "message": "Selected model artifact integrity validation failed.",
                    "crop": crop,
                    "organization_id": organization_id,
                },
                "model": model,
                "latency_ms": round((time.perf_counter() - started) * 1000, 2),
            }

        model_path = artifact_dir / "model.joblib"
        if not model_path.exists():
            return {
                "status": "runtime_unavailable",
                "image": asdict(image),
                "predictions": [],
                "explainability": {
                    "message": "Selected model artifact is missing model.joblib.",
                    "crop": crop,
                    "organization_id": organization_id,
                },
                "model": model,
                "latency_ms": round((time.perf_counter() - started) * 1000, 2),
            }

        cache_key = (str(model_path), artifact_checksum or "")
        classifier = self._model_cache.get(cache_key)
        if classifier is None:
            classifier = joblib.load(model_path)
            self._model_cache[cache_key] = classifier

        features = features_from_bytes(payload).reshape(1, -1)
        probabilities = classifier.predict_proba(features)[0]
        classes = list(classifier.classes_)
        ranked = sorted(
            [
                {"label": str(label), "confidence": float(confidence)}
                for label, confidence in zip(classes, probabilities, strict=True)
            ],
            key=lambda item: item["confidence"],
            reverse=True,
        )
        threshold = float(
            (model.get("preprocessing_config") or {}).get("confidence_threshold", 0.55)
        )
        top = ranked[0]
        latency_ms = round((time.perf_counter() - started) * 1000, 2)
        if top["confidence"] < threshold:
            return {
                "status": "low_confidence",
                "image": asdict(image),
                "predictions": [],
                "candidates": ranked[:3],
                "explainability": {
                    "message": "Prediction confidence is below the serving threshold.",
                    "threshold": threshold,
                    "crop": crop,
                    "organization_id": organization_id,
                    "adapter": "sklearn_image_classifier",
                },
                "model": model,
                "latency_ms": latency_ms,
            }

        return {
            "status": "success",
            "image": asdict(image),
            "predictions": [
                {
                    "type": "disease",
                    "label": top["label"],
                    "confidence": top["confidence"],
                    "description": "Plant Vision baseline classifier prediction",
                    "severity": None,
                    "recommendations": [],
                }
            ],
            "candidates": ranked[:3],
            "explainability": {
                "message": "Prediction generated by the approved Plant Vision inference adapter.",
                "crop": crop,
                "organization_id": organization_id,
                "adapter": "sklearn_image_classifier",
                "threshold": threshold,
            },
            "model": model,
            "latency_ms": latency_ms,
        }


vision_inference_service = VisionInferenceService()
