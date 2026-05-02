# BIJMANTRA JULES JOB CARD: D01
import sys
import unittest
from unittest.mock import MagicMock, patch
from pathlib import Path

# Add backend/scripts to path to allow importing the script as a module
PROJECT_ROOT = Path(__file__).resolve().parents[3] # backend/
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
sys.path.append(str(SCRIPTS_DIR))

# Mock app modules before importing the script to avoid dependency issues
sys.modules["app"] = MagicMock()
sys.modules["app.services"] = MagicMock()
sys.modules["app.services.reevu"] = MagicMock()
sys.modules["app.services.reevu.planner"] = MagicMock()

# Now import the script under test
import eval_domain_accuracy_matrix as evaluator

class TestEvalDomainAccuracyMatrix(unittest.TestCase):
    def setUp(self):
        # Reset any global state if necessary (none apparent in the script)
        pass

    def test_compute_metrics_perfect_match(self):
        results = [
            evaluator.EvalDomainResult(
                case_id="1",
                query="q1",
                expected_domains=["breeding"],
                predicted_domains=["breeding"],
                is_compound=False
            )
        ]
        summary = evaluator._compute_metrics(results)
        scores = summary["domain_scores"]["breeding"]
        self.assertEqual(scores["tp"], 1)
        self.assertEqual(scores["fp"], 0)
        self.assertEqual(scores["fn"], 0)
        self.assertEqual(scores["precision"], 1.0)
        self.assertEqual(scores["recall"], 1.0)
        self.assertEqual(scores["f1"], 1.0)

    def test_compute_metrics_mismatch(self):
        results = [
            evaluator.EvalDomainResult(
                case_id="2",
                query="q2",
                expected_domains=["breeding"],
                predicted_domains=["weather"],
                is_compound=False
            )
        ]
        summary = evaluator._compute_metrics(results)

        b_scores = summary["domain_scores"]["breeding"]
        self.assertEqual(b_scores["tp"], 0)
        self.assertEqual(b_scores["fn"], 1, "Breeding should be False Negative")

        w_scores = summary["domain_scores"]["weather"]
        self.assertEqual(w_scores["tp"], 0)
        self.assertEqual(w_scores["fp"], 1, "Weather should be False Positive")

    def test_compute_metrics_partial_match(self):
        results = [
            evaluator.EvalDomainResult(
                case_id="3",
                query="q3",
                expected_domains=["breeding", "genomics"],
                predicted_domains=["breeding"],
                is_compound=True
            )
        ]
        summary = evaluator._compute_metrics(results)

        b_scores = summary["domain_scores"]["breeding"]
        self.assertEqual(b_scores["tp"], 1)

        g_scores = summary["domain_scores"]["genomics"]
        self.assertEqual(g_scores["fn"], 1)

    def test_confusion_matrix_structure(self):
        # breeding -> weather
        results = [
            evaluator.EvalDomainResult(
                case_id="4",
                query="q4",
                expected_domains=["breeding"],
                predicted_domains=["weather"],
                is_compound=False
            )
        ]
        summary = evaluator._compute_metrics(results)
        matrix = summary["matrix"]

        # breeding expected, weather predicted
        # matrix[expected][predicted]
        self.assertEqual(matrix["breeding"]["weather"], 1)
        self.assertEqual(matrix["breeding"]["breeding"], 0)

    def test_confusion_matrix_multi_label(self):
        # Expected: A, B; Predicted: A, C
        # A -> A (TP for A)
        # B -> A (confusion/miss) and B -> C (confusion/miss)
        # We iterate expected and log all predicted.
        # Expected A: Predicted A, C -> matrix[A][A]++, matrix[A][C]++
        # Expected B: Predicted A, C -> matrix[B][A]++, matrix[B][C]++

        results = [
            evaluator.EvalDomainResult(
                case_id="5",
                query="q5",
                expected_domains=["breeding", "weather"],
                predicted_domains=["breeding", "analytics"],
                is_compound=True
            )
        ]
        summary = evaluator._compute_metrics(results)
        matrix = summary["matrix"]

        # Breeding expected
        self.assertEqual(matrix["breeding"]["breeding"], 1)
        self.assertEqual(matrix["breeding"]["analytics"], 1)

        # Weather expected
        self.assertEqual(matrix["weather"]["breeding"], 1)
        self.assertEqual(matrix["weather"]["analytics"], 1)

if __name__ == "__main__":
    unittest.main()
