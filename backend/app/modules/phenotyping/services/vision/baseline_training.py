"""Deterministic baseline image classifier for Plant Vision.

This module is deliberately lightweight: it uses a deterministic image feature
extractor and scikit-learn classifier so the production pipeline can be tested
and operated without adding an unreviewed heavyweight ML runtime.
"""

import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import joblib
import numpy as np
from PIL import Image
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


PREPROCESSING_CONFIG = {
    "feature_extractor": "rgb_histogram_luminance_grid",
    "feature_version": "vision-preprocess-v1",
    "image_mode": "RGB",
    "histogram_bins": 8,
    "thumbnail_size": [16, 16],
}


@dataclass(frozen=True)
class TrainingRecord:
    image_path: Path
    label: str
    split: str
    sha256: str
    metadata: dict[str, Any]


def extract_image_features(image: Image.Image) -> np.ndarray:
    rgb = image.convert("RGB").resize((96, 96))
    array = np.asarray(rgb, dtype=np.float32) / 255.0
    channel_means = array.mean(axis=(0, 1))
    channel_stds = array.std(axis=(0, 1))

    histograms = []
    for channel in range(3):
        hist, _ = np.histogram(array[:, :, channel], bins=8, range=(0.0, 1.0), density=True)
        histograms.extend(hist.astype(np.float32))

    luminance = np.asarray(rgb.convert("L").resize((16, 16)), dtype=np.float32) / 255.0
    luminance_mean = float(luminance.mean())
    luminance_std = float(luminance.std())
    entropy = 0.0
    values, counts = np.unique((luminance * 255).astype(np.uint8), return_counts=True)
    total = counts.sum()
    for count in counts:
        probability = count / total
        entropy -= probability * math.log2(probability)

    return np.concatenate(
        [
            channel_means,
            channel_stds,
            np.array(histograms, dtype=np.float32),
            np.array([luminance_mean, luminance_std, entropy], dtype=np.float32),
            luminance.flatten(),
        ]
    )


def features_from_path(path: Path) -> np.ndarray:
    with Image.open(path) as image:
        return extract_image_features(image)


def features_from_bytes(payload: bytes) -> np.ndarray:
    from io import BytesIO

    with Image.open(BytesIO(payload)) as image:
        return extract_image_features(image)


class BaselineImageClassifierTrainer:
    """Train and persist a deterministic baseline classifier."""

    def _matrix(self, records: list[TrainingRecord]) -> tuple[np.ndarray, np.ndarray]:
        features = [features_from_path(record.image_path) for record in records]
        labels = [record.label for record in records]
        return np.vstack(features), np.asarray(labels)

    def _split_records(self, records: list[TrainingRecord], split: str) -> list[TrainingRecord]:
        return [record for record in records if record.split == split]

    def train(
        self,
        *,
        records: list[TrainingRecord],
        artifact_dir: Path,
        config: dict[str, Any],
    ) -> dict[str, Any]:
        labels = sorted({record.label for record in records})
        if len(labels) < 2:
            return {"error": "At least two classes are required for baseline training"}

        train_records = self._split_records(records, "train")
        val_records = self._split_records(records, "val")
        test_records = self._split_records(records, "test")
        if len({record.label for record in train_records}) < 2:
            return {"error": "Training split must contain at least two classes"}
        if not val_records:
            val_records = train_records
        if not test_records:
            test_records = val_records

        seed = int(config.get("seed", 42))
        max_iter = int(config.get("epochs", 50))
        classifier = Pipeline(
            [
                ("scaler", StandardScaler()),
                (
                    "classifier",
                    LogisticRegression(
                        class_weight="balanced",
                        max_iter=max(25, max_iter),
                        random_state=seed,
                        solver="liblinear",
                    ),
                ),
            ]
        )

        train_x, train_y = self._matrix(train_records)
        val_x, val_y = self._matrix(val_records)
        test_x, test_y = self._matrix(test_records)
        classifier.fit(train_x, train_y)

        val_predictions = classifier.predict(val_x)
        test_predictions = classifier.predict(test_x)
        val_accuracy = float(accuracy_score(val_y, val_predictions))
        test_accuracy = float(accuracy_score(test_y, test_predictions))
        matrix = confusion_matrix(test_y, test_predictions, labels=labels)

        artifact_dir.mkdir(parents=True, exist_ok=True)
        model_path = artifact_dir / "model.joblib"
        joblib.dump(classifier, model_path)

        label_mapping = {str(index): label for index, label in enumerate(labels)}
        preprocessing = {
            **PREPROCESSING_CONFIG,
            "confidence_threshold": float(config.get("confidence_threshold", 0.55)),
        }
        metrics = {
            "val_accuracy": val_accuracy,
            "test_accuracy": test_accuracy,
            "class_count": len(labels),
            "train_count": len(train_records),
            "val_count": len(val_records),
            "test_count": len(test_records),
            "classification_report": classification_report(
                test_y,
                test_predictions,
                labels=labels,
                output_dict=True,
                zero_division=0,
            ),
        }
        evaluation_report = {
            "metrics": metrics,
            "labels": labels,
            "confusion_matrix": matrix.tolist(),
            "confusion_matrix_labels": labels,
            "calibration": {
                "method": "logistic_regression_probabilities",
                "confidence_threshold": preprocessing["confidence_threshold"],
            },
        }
        training_provenance = {
            "seed": seed,
            "trainer": "sklearn_logistic_regression_baseline",
            "base_model": config.get("base_model", "sklearn-image-baseline"),
            "record_count": len(records),
            "source_checksums": sorted({record.sha256 for record in records}),
            "crop": config.get("crop"),
            "task": "classification",
        }

        artifacts = {
            "config.json": config,
            "metrics.json": metrics,
            "label_mapping.json": label_mapping,
            "preprocessing.json": preprocessing,
            "training_provenance.json": training_provenance,
            "evaluation_report.json": evaluation_report,
            "confusion_matrix.json": {
                "labels": labels,
                "matrix": matrix.tolist(),
            },
        }
        for filename, payload in artifacts.items():
            (artifact_dir / filename).write_text(
                json.dumps(payload, indent=2, sort_keys=True),
                encoding="utf-8",
            )

        (artifact_dir / "model_card.md").write_text(
            "\n".join(
                [
                    "# Plant Vision Baseline Model",
                    "",
                    f"- Trainer: {training_provenance['trainer']}",
                    f"- Classes: {', '.join(labels)}",
                    f"- Validation accuracy: {val_accuracy:.4f}",
                    f"- Test accuracy: {test_accuracy:.4f}",
                    f"- Confidence threshold: {preprocessing['confidence_threshold']:.2f}",
                    "",
                    "This model is eligible for serving only after registry validation and promotion.",
                ]
            ),
            encoding="utf-8",
        )

        return {
            "model_path": str(model_path),
            "artifact_dir": str(artifact_dir),
            "metrics": metrics,
            "label_mapping": label_mapping,
            "preprocessing_config": preprocessing,
            "training_provenance": training_provenance,
            "evaluation_report": evaluation_report,
            "size_bytes": sum(
                path.stat().st_size for path in artifact_dir.glob("*") if path.is_file()
            ),
        }


baseline_image_classifier_trainer = BaselineImageClassifierTrainer()
