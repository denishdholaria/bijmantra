import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add backend directory to sys.path
BASE_DIR = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(BASE_DIR))

# Import the module to be tested
# We need to make sure the import works even if dependencies are missing in the environment
# Since the script uses only standard libraries (except maybe 'typing'), it should be fine.
try:
    from scripts.simulate_nightly_etl import NightlyETLSimulator, WeatherData, SensorReading, GenomicVariant, TrialObservation
except ImportError:
    # Fallback for environments where the script path isn't resolving correctly
    sys.path.append(str(BASE_DIR / "scripts"))
    from simulate_nightly_etl import NightlyETLSimulator, WeatherData, SensorReading, GenomicVariant, TrialObservation

class TestNightlyETLSimulator(unittest.TestCase):
    def setUp(self):
        self.test_report_path = "test_etl_report.json"
        self.etl = NightlyETLSimulator(report_path=self.test_report_path)

    def tearDown(self):
        # Clean up report file if it exists
        Path(self.test_report_path).unlink(missing_ok=True)

    def test_generate_weather_data(self):
        data = self.etl.generate_weather_data(count=5)
        self.assertEqual(len(data), 5)
        self.assertIsInstance(data[0], WeatherData)
        self.assertTrue(10.0 <= data[0].temperature <= 35.0)

    def test_generate_sensor_readings(self):
        data = self.etl.generate_sensor_readings(count=5)
        self.assertEqual(len(data), 5)
        self.assertIsInstance(data[0], SensorReading)
        self.assertIn(data[0].sensor_type, ["soil_moisture", "leaf_wetness", "solar_radiation"])

    def test_generate_genomic_variants(self):
        data = self.etl.generate_genomic_variants(count=5)
        self.assertEqual(len(data), 5)
        self.assertIsInstance(data[0], GenomicVariant)
        # It's possible for ref and alt to be same if random chooses so?
        # Let's check the logic: alt = random.choice([b for b in bases if b != ref])
        # So they should be different.
        self.assertNotEqual(data[0].reference_allele, data[0].alternate_allele)

    def test_generate_trial_observations(self):
        data = self.etl.generate_trial_observations(count=5)
        self.assertEqual(len(data), 5)
        self.assertIsInstance(data[0], TrialObservation)
        self.assertTrue(data[0].trial_id.startswith("TRIAL-"))

    def test_extract(self):
        self.etl.extract()
        self.assertEqual(len(self.etl.extracted_data["weather"]), 10)
        self.assertEqual(len(self.etl.extracted_data["sensors"]), 20)
        self.assertEqual(len(self.etl.extracted_data["genomics"]), 5)
        self.assertEqual(len(self.etl.extracted_data["trials"]), 15)

    def test_transform(self):
        self.etl.extract()
        self.etl.transform()
        # Transformation might drop some records (5% chance), so check <= extracted
        # Since we extract 10, 20, 5, 15 records, total 50.
        # It's statistically unlikely to drop all, but let's just check bounds.
        self.assertLessEqual(len(self.etl.transformed_data["weather"]), 10)
        self.assertLessEqual(len(self.etl.transformed_data["sensors"]), 20)
        self.assertLessEqual(len(self.etl.transformed_data["genomics"]), 5)
        self.assertLessEqual(len(self.etl.transformed_data["trials"]), 15)

    def test_load(self):
        # We need to populate transformed_data first
        self.etl.transformed_data = {
            "weather": [1], # Dummy data
            "sensors": [1],
            "genomics": [1],
            "trials": [1]
        }

        with patch("time.sleep", return_value=None): # Mock sleep to speed up test
            self.etl.load()

        self.assertEqual(self.etl.load_status["weather"], "SUCCESS")
        self.assertEqual(self.etl.load_status["sensors"], "SUCCESS")
        self.assertIn(self.etl.load_status["reevu_kb"], ["UPDATED", "SKIPPED"])

    def test_generate_report(self):
        self.etl.extract()
        # Skip transform/load for speed, just populate required fields if needed
        # generate_report reads from extracted and transformed and load_status

        with patch("builtins.print"), patch("time.sleep", return_value=None):
            self.etl.generate_report()

        self.assertTrue(Path(self.test_report_path).exists())
        # Check content
        with open(self.test_report_path, "r") as f:
            content = f.read()
            self.assertIn("status", content)
            self.assertIn("SUCCESS", content)

if __name__ == "__main__":
    unittest.main()
