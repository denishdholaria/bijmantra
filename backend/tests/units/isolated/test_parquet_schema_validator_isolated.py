# BIJMANTRA JULES JOB CARD: D04
import unittest
import tempfile
import os
import shutil
import sys
from typing import Optional, List
import polars as pl
from pydantic import BaseModel

# Add script location to path to import ParquetValidator
current_dir = os.path.dirname(os.path.abspath(__file__))
scripts_dir = os.path.abspath(os.path.join(current_dir, "../../../scripts"))
if scripts_dir not in sys.path:
    sys.path.append(scripts_dir)

try:
    from parquet_schema_validator_script import ParquetValidator
except ImportError:
    # Handle case where script name is different or path is wrong
    sys.path.append(os.path.join(current_dir, "../../../backend/scripts"))
    from parquet_schema_validator_script import ParquetValidator

class TestModel(BaseModel):
    id: int
    name: str
    value: float
    optional_field: Optional[str] = None
    list_field: List[int]

class TestParquetValidator(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.validator = ParquetValidator(TestModel)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_valid_parquet(self):
        # Create a valid parquet file
        data = {
            "id": [1, 2],
            "name": ["A", "B"],
            "value": [1.1, 2.2],
            "optional_field": ["X", None],
            "list_field": [[1, 2], [3, 4]]
        }
        df = pl.DataFrame(data, schema_overrides={"id": pl.Int64, "name": pl.Utf8, "value": pl.Float64, "optional_field": pl.Utf8, "list_field": pl.List(pl.Int64)})
        file_path = os.path.join(self.test_dir, "valid.parquet")
        df.write_parquet(file_path)

        errors = self.validator.validate(file_path)
        self.assertEqual(errors, [])

    def test_missing_column(self):
        # Missing 'name' column
        data = {
            "id": [1],
            "value": [1.1],
            "optional_field": ["X"],
            "list_field": [[1]]
        }
        df = pl.DataFrame(data, schema_overrides={"id": pl.Int64, "value": pl.Float64, "optional_field": pl.Utf8, "list_field": pl.List(pl.Int64)})
        file_path = os.path.join(self.test_dir, "missing_col.parquet")
        df.write_parquet(file_path)

        errors = self.validator.validate(file_path)
        # Check that error message mentions missing column
        self.assertTrue(any("Missing required column: name" in e for e in errors), f"Errors: {errors}")

    def test_null_in_required_field(self):
        # 'id' is required (int), should not have nulls
        data = {
            "id": [1, None],
            "name": ["A", "B"],
            "value": [1.1, 2.2],
            "optional_field": ["X", None],
            "list_field": [[1, 2], [3, 4]]
        }
        df = pl.DataFrame(data, schema_overrides={"id": pl.Int64, "name": pl.Utf8, "value": pl.Float64, "optional_field": pl.Utf8, "list_field": pl.List(pl.Int64)})
        file_path = os.path.join(self.test_dir, "null_required.parquet")
        df.write_parquet(file_path)

        errors = self.validator.validate(file_path)
        self.assertTrue(any("contains 1 null values" in e and "field 'id'" in e for e in errors), f"Errors: {errors}")

    def test_wrong_type(self):
        # 'id' is int, pass string
        data = {
            "id": ["not an int"],
            "name": ["A"],
            "value": [1.1],
            "optional_field": ["X"],
            "list_field": [[1]]
        }
        df = pl.DataFrame(data, schema_overrides={"id": pl.Utf8, "name": pl.Utf8, "value": pl.Float64, "optional_field": pl.Utf8, "list_field": pl.List(pl.Int64)})
        file_path = os.path.join(self.test_dir, "wrong_type.parquet")
        df.write_parquet(file_path)

        errors = self.validator.validate(file_path)
        # Polars String/Utf8 vs Integer
        # Polars 0.19 might use Utf8, newer uses String. Check error message.
        self.assertTrue(any(("has type String" in e or "has type Utf8" in e) and "expected compatible type for Integer" in e for e in errors), f"Errors: {errors}")

if __name__ == "__main__":
    unittest.main()
