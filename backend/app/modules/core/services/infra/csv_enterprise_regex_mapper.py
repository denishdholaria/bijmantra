import re
from enum import StrEnum
from io import BytesIO
from typing import Any

import pandas as pd
from pydantic import BaseModel, ConfigDict, Field


class TransformationType(StrEnum):
    REGEX_SUB = "regex_sub"
    REGEX_EXTRACT = "regex_extract"
    STATIC = "static"
    UPPERCASE = "uppercase"
    LOWERCASE = "lowercase"
    TRIM = "trim"

class TransformationRule(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    type: TransformationType
    pattern: str | None = None  # For regex
    replacement: str | None = None # For sub
    group: int = 0 # For extract
    value: Any | None = None # For static

class MappingRule(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    target_column: str
    source_column: str | None = None
    transformations: list[TransformationRule] = Field(default_factory=list)
    default_value: Any | None = None
    required: bool = False

class MapperConfig(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    rules: list[MappingRule]
    skip_rows: int = 0
    delimiter: str = ","
    encoding: str = "utf-8"

class CsvRegexMapper:
    def process(self, file_content: bytes | str, config: MapperConfig) -> list[dict[str, Any]]:
        # Handle string input by encoding to bytes for consistency
        if isinstance(file_content, str):
            stream = BytesIO(file_content.encode(config.encoding))
        else:
            stream = BytesIO(file_content)

        try:
            # Read all as string to preserve formatting (e.g. leading zeros)
            df = pd.read_csv(
                stream,
                sep=config.delimiter,
                skiprows=config.skip_rows,
                encoding=config.encoding,
                dtype=str,
                keep_default_na=False # Keep empty strings as empty strings, don't convert to NaN
            )
        except Exception as e:
            raise ValueError(f"Failed to parse CSV: {e}")

        result_rows = []

        # Convert to list of dicts directly for iteration, might be faster than iterrows
        records = df.to_dict(orient='records')

        for row_dict in records:
            mapped_row = {}

            for rule in config.rules:
                value = None

                # 1. Extract raw value
                if rule.source_column:
                    # check if column exists in the row
                    if rule.source_column in row_dict:
                        value = row_dict[rule.source_column]
                    else:
                        # Column missing from CSV entirely
                        value = None

                # 2. Apply transformations
                # We apply transforms even if value is None, to support STATIC
                if rule.transformations:
                    for transform in rule.transformations:
                        value = self._apply_transform(value, transform)

                # 3. Apply default if empty/None
                if (value is None or value == "") and rule.default_value is not None:
                    value = rule.default_value

                # 4. Strict validation for required fields
                if rule.required and (value is None or value == ""):
                    raise ValueError(f"Required field '{rule.target_column}' is missing or empty in row {row_dict}.")

                mapped_row[rule.target_column] = value

            result_rows.append(mapped_row)

        return result_rows

    def _apply_transform(self, value: Any, rule: TransformationRule) -> Any:
        # Static overrides everything
        if rule.type == TransformationType.STATIC:
            return rule.value

        if value is None:
            return None

        val_str = str(value)

        if rule.type == TransformationType.REGEX_SUB:
            if rule.pattern is None:
                return val_str
            return re.sub(rule.pattern, rule.replacement or "", val_str)

        elif rule.type == TransformationType.REGEX_EXTRACT:
            if rule.pattern is None:
                return val_str
            match = re.search(rule.pattern, val_str)
            if match:
                try:
                    return match.group(rule.group)
                except IndexError:
                    return None
            return None

        elif rule.type == TransformationType.UPPERCASE:
            return val_str.upper()

        elif rule.type == TransformationType.LOWERCASE:
            return val_str.lower()

        elif rule.type == TransformationType.TRIM:
            return val_str.strip()

        return value
