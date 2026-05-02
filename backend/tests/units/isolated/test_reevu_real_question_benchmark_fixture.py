import json
import unittest
from pathlib import Path


BACKEND_ROOT = Path(__file__).resolve().parents[3]
REPO_ROOT = BACKEND_ROOT.parent
FIXTURE_PATH = BACKEND_ROOT / "tests" / "fixtures" / "reevu" / "real_question_benchmark.json"


class TestReevuRealQuestionBenchmarkFixture(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        with FIXTURE_PATH.open(encoding="utf-8") as fixture_file:
            try:
                cls.cases = json.load(fixture_file)
            except json.JSONDecodeError as exc:
                raise AssertionError(f"Failed to parse benchmark fixture {FIXTURE_PATH}: {exc}") from exc

    def test_fixture_exists_and_is_not_empty(self) -> None:
        self.assertTrue(FIXTURE_PATH.exists())
        self.assertIsInstance(self.cases, list)
        self.assertGreaterEqual(len(self.cases), 10)

    def test_cases_have_required_grounding_fields(self) -> None:
        required_keys = {
            "benchmark_id",
            "query",
            "use_case",
            "source_capability",
            "source_tests",
            "domain_group",
            "cross_domain_class",
            "expected_domains",
            "expected_function",
            "safe_failure_expected",
            "pass_criteria",
            "description",
        }

        ids: set[str] = set()
        capabilities: set[str] = set()
        domain_groups: set[str] = set()
        cross_domain_classes: set[str] = set()
        safe_failure_cases = 0
        deterministic_compute_cases = 0
        allowed_domain_groups = {"analytics", "breeding", "genomics", "trials", "weather"}
        allowed_pass_criteria_keys = {
            "factuality",
            "evidence_quality",
            "deterministic_compute",
            "safe_failure",
        }

        for case in self.cases:
            self.assertTrue(required_keys.issubset(case.keys()), msg=f"missing required keys in {case}")
            self.assertIsInstance(case["benchmark_id"], str)
            self.assertTrue(case["benchmark_id"].strip())
            self.assertNotIn(case["benchmark_id"], ids)
            ids.add(case["benchmark_id"])

            self.assertIsInstance(case["query"], str)
            self.assertTrue(case["query"].strip())
            self.assertIsInstance(case["use_case"], str)
            self.assertTrue(case["use_case"].strip())
            self.assertIsInstance(case["source_capability"], str)
            self.assertTrue(case["source_capability"].strip())
            capabilities.add(case["source_capability"])

            self.assertIsInstance(case["source_tests"], list)
            self.assertGreater(len(case["source_tests"]), 0)
            for source_test in case["source_tests"]:
                self.assertIsInstance(source_test, str)
                self.assertTrue(source_test.strip())
                self.assertTrue(
                    (REPO_ROOT / source_test).exists(),
                    msg=f"source test file not found: {source_test}",
                )

            self.assertIsInstance(case["domain_group"], str)
            self.assertIn(case["domain_group"], allowed_domain_groups)
            domain_groups.add(case["domain_group"])

            self.assertIsInstance(case["cross_domain_class"], str)
            self.assertTrue(case["cross_domain_class"].strip())
            cross_domain_classes.add(case["cross_domain_class"])

            self.assertIsInstance(case["expected_domains"], list)
            self.assertGreater(len(case["expected_domains"]), 0)
            self.assertTrue(all(isinstance(domain, str) and domain.strip() for domain in case["expected_domains"]))
            self.assertIn(case["domain_group"], case["expected_domains"])

            if len(case["expected_domains"]) == 1:
                self.assertEqual(case["cross_domain_class"], "single_domain")
            else:
                self.assertNotEqual(case["cross_domain_class"], "single_domain")

            self.assertIsInstance(case["expected_function"], str)
            self.assertTrue(case["expected_function"].strip())
            self.assertIsInstance(case["safe_failure_expected"], bool)
            self.assertIsInstance(case["pass_criteria"], dict)
            self.assertEqual(set(case["pass_criteria"].keys()), allowed_pass_criteria_keys)

            for criteria_name, criteria_checks in case["pass_criteria"].items():
                self.assertIsInstance(criteria_checks, list)
                self.assertTrue(
                    all(isinstance(check, str) and check.strip() for check in criteria_checks),
                    msg=f"invalid pass criteria list for {criteria_name} in {case['benchmark_id']}",
                )

            self.assertGreater(len(case["pass_criteria"]["factuality"]), 0)
            self.assertGreater(len(case["pass_criteria"]["evidence_quality"]), 0)

            if case["safe_failure_expected"]:
                self.assertIn("structured_safe_failure_required", case["pass_criteria"]["safe_failure"])
                self.assertIn("failure_reason_must_be_explicit", case["pass_criteria"]["safe_failure"])
                self.assertIn("retrieval_audit_required", case["pass_criteria"]["evidence_quality"])
            else:
                self.assertEqual(case["pass_criteria"]["safe_failure"], [])
                self.assertIn("evidence_envelope_required", case["pass_criteria"]["evidence_quality"])

            if case["expected_function"] == "calculate_breeding_value":
                deterministic_compute_cases += 1
                self.assertIn(
                    "deterministic_method_refs_required",
                    case["pass_criteria"]["deterministic_compute"],
                )
                self.assertIn(
                    "deterministic_compute_evidence_required",
                    case["pass_criteria"]["deterministic_compute"],
                )
            else:
                self.assertEqual(case["pass_criteria"]["deterministic_compute"], [])

            self.assertIsInstance(case["description"], str)
            self.assertTrue(case["description"].strip())

            if case["safe_failure_expected"]:
                safe_failure_cases += 1

        self.assertGreaterEqual(len(capabilities), 5)
        self.assertGreaterEqual(len(domain_groups), 3)
        self.assertGreaterEqual(len(cross_domain_classes), 5)
        self.assertGreaterEqual(safe_failure_cases, 3)
        self.assertGreaterEqual(deterministic_compute_cases, 1)


if __name__ == "__main__":
    unittest.main()
