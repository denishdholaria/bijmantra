# BIJMANTRA JULES JOB CARD: D04
import argparse
import logging
import os
import sys
from typing import Any, Union, get_args, get_origin

import polars as pl
from pydantic import BaseModel
from pydantic.fields import FieldInfo


# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Ensure backend root is in python path to allow app imports
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_root = os.path.dirname(current_dir)
if backend_root not in sys.path:
    sys.path.insert(0, backend_root)

# Try importing schemas
schemas_map = {}
try:
    from app.schemas.genotyping import (
        CallResponse,
        GenomeMap,
        LinkageGroup,
        MarkerPosition,
        ReferenceSet,
        VariantResponse,
        VendorOrder,
    )
    schemas_map = {
        "VariantResponse": VariantResponse,
        "CallResponse": CallResponse,
        "ReferenceSet": ReferenceSet,
        "GenomeMap": GenomeMap,
        "LinkageGroup": LinkageGroup,
        "MarkerPosition": MarkerPosition,
        "VendorOrder": VendorOrder,
    }
except ImportError as e:
    logger.warning(f"Could not import schemas from app: {e}")

class ParquetValidator:
    """
    Validates a Parquet file against a Pydantic schema.
    """
    def __init__(self, schema_model: type[BaseModel]):
        self.schema_model = schema_model
        # Pydantic 2.x: model_fields is a dict of FieldInfo
        self.field_definitions: dict[str, FieldInfo] = schema_model.model_fields

    def _get_type_info(self, annotation: Any) -> tuple[Any, bool]:
        """
        Unwraps Optional[T] or T | None to get T and checks if nullable.
        Returns (inner_type, is_nullable)
        """
        origin = get_origin(annotation)
        args = get_args(annotation)

        is_nullable = False
        inner_type = annotation

        # Handle Union (e.g., str | None, Union[str, None])
        # Pydantic 2 / Python 3.10+ uses types.UnionType for |
        if origin is Union or str(type(annotation)) == "<class 'types.UnionType'>":
             if type(None) in args:
                 is_nullable = True
                 # Filter out NoneType to get the actual type
                 non_none_args = [arg for arg in args if arg is not type(None)]
                 if non_none_args:
                     inner_type = non_none_args[0] # Simplification: assume single type + None
                     # If multiple types (Union[int, str]), we pick the first for type checking or handle broadly
                 else:
                     inner_type = Any

        return inner_type, is_nullable

    def validate(self, file_path: str) -> list[str]:
        errors = []
        if not os.path.exists(file_path):
            return [f"File not found: {file_path}"]

        try:
            # Lazy read to inspect schema first without loading all data?
            # read_parquet is eager. scan_parquet is lazy.
            # Using read_parquet for simplicity and full null checks.
            df = pl.read_parquet(file_path)
        except Exception as e:
            return [f"Failed to read parquet file: {e}"]

        schema_cols = df.columns
        df_schema = df.schema # dict of name -> DataType

        for name, field in self.field_definitions.items():
            # Determine column name (prefer alias if alias exists)
            # Logic: If alias is in columns, use it. Else if name is in columns, use it.
            # Else missing.

            col_name = None
            if field.alias and field.alias in schema_cols:
                col_name = field.alias
            elif name in schema_cols:
                col_name = name

            # Check required
            # In Pydantic 2, is_required() handles default values.
            if col_name is None:
                if field.is_required():
                    errors.append(f"Missing required column: {name} (alias: {field.alias})")
                continue

            # Get Type Info
            inner_type, is_nullable_type = self._get_type_info(field.annotation)

            # Check Nulls
            # Even if field is required (present in input), it might allow None as value.
            # If is_nullable_type is False, then no nulls allowed.
            if not is_nullable_type:
                null_count = df.select(pl.col(col_name).null_count()).item()
                if null_count > 0:
                    errors.append(f"Column '{col_name}' contains {null_count} null values but field '{name}' is not nullable.")

            # Type Compatibility Check (Basic)
            current_dtype = df_schema[col_name]

            # Map Python types to expected Polars categories
            # String -> String, Utf8, Categorical
            # Int -> Int8, Int16, Int32, Int64, UInt...
            # Float -> Float32, Float64
            # Bool -> Boolean
            # List -> List

            origin = get_origin(inner_type)

            type_error = False
            expected_desc = str(inner_type)

            if inner_type is int:
                if not (current_dtype.is_integer() or current_dtype.is_float()):
                    # Sometimes ints are stored as floats in parquet if they have nulls (pandas legacy),
                    # but Polars handles Int64 with nulls.
                    type_error = True
                    expected_desc = "Integer"
            elif inner_type is float:
                if not current_dtype.is_float():
                    type_error = True
                    expected_desc = "Float"
            elif inner_type is str:
                if not (current_dtype == pl.Utf8 or current_dtype == pl.String or current_dtype == pl.Categorical):
                    type_error = True
                    expected_desc = "String"
            elif inner_type is bool:
                if current_dtype != pl.Boolean:
                    type_error = True
                    expected_desc = "Boolean"
            elif origin is list:
                 if not isinstance(current_dtype, pl.List):
                     type_error = True
                     expected_desc = "List"

            if type_error:
                errors.append(f"Column '{col_name}' has type {current_dtype} but expected compatible type for {expected_desc}")

        return errors

def main():
    parser = argparse.ArgumentParser(description="Parquet Schema Validator")
    parser.add_argument("--file", help="Path to parquet file")
    parser.add_argument("--schema", help="Schema name")
    parser.add_argument("--list-schemas", action="store_true", help="List available schemas")

    args = parser.parse_args()

    if args.list_schemas:
        print("Available schemas:")
        for s in schemas_map:
            print(f"- {s}")
        return

    if not args.file or not args.schema:
        parser.print_help()
        sys.exit(1)

    if args.schema not in schemas_map:
        logger.error(f"Schema '{args.schema}' not found. Use --list-schemas to see available options.")
        sys.exit(1)

    logger.info(f"Validating {args.file} against schema {args.schema}...")
    validator = ParquetValidator(schemas_map[args.schema])
    errors = validator.validate(args.file)

    if errors:
        logger.error("Validation Failed:")
        for e in errors:
            logger.error(f"- {e}")
        sys.exit(1)
    else:
        logger.info("Validation Successful.")

if __name__ == "__main__":
    main()
