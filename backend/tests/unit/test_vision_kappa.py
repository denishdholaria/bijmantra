import unittest
import asyncio
from unittest.mock import MagicMock
from backend.app.services.vision_annotation import QualityControlService

class TestKappaCalculationService(unittest.TestCase):

    def setUp(self):
        self.service = QualityControlService()
        self.db = MagicMock()
        self.org_id = 1

    def run_async(self, coro):
        return asyncio.run(coro)

    def test_perfect_agreement(self):
        annotations = [
            {"image_id": "1", "annotator_id": "A", "data": {"label": "cat"}},
            {"image_id": "1", "annotator_id": "B", "data": {"label": "cat"}},
            {"image_id": "2", "annotator_id": "A", "data": {"label": "dog"}},
            {"image_id": "2", "annotator_id": "B", "data": {"label": "dog"}},
        ]
        result = self.run_async(self.service.calculate_inter_annotator_agreement(
            self.db, self.org_id, annotations
        ))
        self.assertEqual(result["kappa"], 1.0)
        self.assertEqual(result["agreement_percent"], 100.0)
        self.assertEqual(result["interpretation"], "Almost perfect agreement")

    def test_random_agreement(self):
        # 4 items, 50% agreement by chance and observation
        annotations = [
            {"image_id": "1", "annotator_id": "A", "data": {"label": "cat"}},
            {"image_id": "1", "annotator_id": "B", "data": {"label": "cat"}},

            {"image_id": "2", "annotator_id": "A", "data": {"label": "cat"}},
            {"image_id": "2", "annotator_id": "B", "data": {"label": "dog"}},

            {"image_id": "3", "annotator_id": "A", "data": {"label": "dog"}},
            {"image_id": "3", "annotator_id": "B", "data": {"label": "cat"}},

            {"image_id": "4", "annotator_id": "A", "data": {"label": "dog"}},
            {"image_id": "4", "annotator_id": "B", "data": {"label": "dog"}},
        ]
        result = self.run_async(self.service.calculate_inter_annotator_agreement(
            self.db, self.org_id, annotations
        ))
        self.assertAlmostEqual(result["kappa"], 0.0)
        self.assertEqual(result["agreement_percent"], 50.0)
        self.assertEqual(result["interpretation"], "Poor agreement") # 0.0 is <= 0.2? Wait, 0.0 is Poor?
        # My logic: > 0.2 is Fair. <= 0.2 and > 0 is Slight. <= 0 is Poor.
        # Wait, if Kappa is exactly 0.0, it falls into "Poor agreement" per my code:
        # elif kappa > 0: interpretation = "Slight"
        # else: interpretation = "Poor"
        # So 0.0 is Poor. Correct.

    def test_insufficient_annotators(self):
        annotations = [
            {"image_id": "1", "annotator_id": "A", "data": {"label": "cat"}},
        ]
        result = self.run_async(self.service.calculate_inter_annotator_agreement(
            self.db, self.org_id, annotations
        ))
        self.assertIsNone(result["kappa"])
        self.assertIn("Need at least 2", result["message"])

    def test_too_many_annotators(self):
        annotations = [
            {"image_id": "1", "annotator_id": "A", "data": {"label": "cat"}},
            {"image_id": "1", "annotator_id": "B", "data": {"label": "cat"}},
            {"image_id": "1", "annotator_id": "C", "data": {"label": "cat"}},
        ]
        result = self.run_async(self.service.calculate_inter_annotator_agreement(
            self.db, self.org_id, annotations
        ))
        self.assertIsNone(result["kappa"])
        self.assertIn("Need exactly 2 unique annotators", result["message"])

    def test_ignore_invalid_data(self):
        annotations = [
            {"image_id": "1", "annotator_id": "A", "data": {"label": "cat"}},
            {"image_id": "1", "annotator_id": "B", "data": {"label": "cat"}},
            {"image_id": "2", "annotator_id": "A", "data": {}}, # No label
            {"image_id": "2", "annotator_id": "B", "data": {"label": "dog"}},
        ]
        # Only image 1 is valid common
        # 1 item, perfect agreement. Kappa=1.0.
        result = self.run_async(self.service.calculate_inter_annotator_agreement(
            self.db, self.org_id, annotations
        ))
        self.assertEqual(result["kappa"], 1.0)
        self.assertEqual(result["annotations_compared"], 1)

if __name__ == "__main__":
    unittest.main()
