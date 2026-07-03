
import csv
import io
from enum import StrEnum
from typing import List, Optional, Dict, Any

from pydantic import BaseModel, Field, field_validator


class SSPScenario(StrEnum):
    """
    Standard Shared Socioeconomic Pathways (SSPs) scenarios.
    Focuses on the core scenarios used in CMIP6 and IPCC AR6.
    """
    SSP1_19 = "SSP1-1.9"
    SSP1_26 = "SSP1-2.6"
    SSP2_45 = "SSP2-4.5"
    SSP3_70 = "SSP3-7.0"
    SSP4_34 = "SSP4-3.4"
    SSP4_60 = "SSP4-6.0"
    SSP5_85 = "SSP5-8.5"

    # Legacy/Alternative naming
    SSP119 = "ssp119"
    SSP126 = "ssp126"
    SSP245 = "ssp245"
    SSP370 = "ssp370"
    SSP585 = "ssp585"

    @classmethod
    def normalize(cls, value: str) -> "SSPScenario":
        """Normalize scenario string to enum member."""
        normalized = value.strip().upper().replace(" ", "")
        # Map common variations
        if normalized in ["SSP1-19", "SSP119"]:
            return cls.SSP1_19
        if normalized in ["SSP1-26", "SSP126"]:
            return cls.SSP1_26
        if normalized in ["SSP2-45", "SSP245"]:
            return cls.SSP2_45
        if normalized in ["SSP3-70", "SSP370"]:
            return cls.SSP3_70
        if normalized in ["SSP4-34", "SSP434"]:
            return cls.SSP4_34
        if normalized in ["SSP4-60", "SSP460"]:
            return cls.SSP4_60
        if normalized in ["SSP5-85", "SSP585"]:
            return cls.SSP5_85

        # Fallback for exact match
        try:
            return cls(value)
        except ValueError:
            # Try to match by value
            for member in cls:
                if member.value == value:
                    return member
            raise ValueError(f"Unknown SSP scenario: {value}")


class SSPDataPoint(BaseModel):
    """
    Represents a single data point for an SSP scenario.
    """
    scenario: SSPScenario
    model: str
    region: str
    variable: str
    unit: str
    year: int
    value: float

    @field_validator('year')
    @classmethod
    def validate_year(cls, v: int) -> int:
        if v < 1900 or v > 2300:
            raise ValueError(f"Year {v} is out of expected range (1900-2300)")
        return v


class SSPParserResult(BaseModel):
    data: List[SSPDataPoint]
    errors: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


def parse_ssp_csv(content: str, target_years: Optional[List[int]] = None) -> SSPParserResult:
    """
    Parses CSV content in the standard IAM/IIASA format.
    Expected columns: Model, Scenario, Region, Variable, Unit, <Years...>

    Args:
        content: The CSV content as a string.
        target_years: List of years to extract (e.g., [2030, 2050]). If None, extracts all found years.

    Returns:
        SSPParserResult object containing parsed data points and any errors.
    """
    result = SSPParserResult(data=[])

    if not content:
        result.errors.append("Empty content")
        return result

    try:
        # Use csv.DictReader to handle headers automatically
        reader = csv.DictReader(io.StringIO(content))

        if not reader.fieldnames:
            result.errors.append("No headers found in CSV")
            return result

        # Identify year columns
        # Year columns are usually integers (e.g., "2020", "2030")
        year_columns = []
        metadata_columns = ["Model", "Scenario", "Region", "Variable", "Unit"]

        # Mapping for case-insensitive column matching
        header_map = {h.lower(): h for h in reader.fieldnames}

        # Validate required columns exist
        missing_cols = []
        mapped_cols = {}
        for req in metadata_columns:
            if req.lower() not in header_map:
                missing_cols.append(req)
            else:
                mapped_cols[req] = header_map[req.lower()]

        if missing_cols:
            result.errors.append(f"Missing required columns: {', '.join(missing_cols)}")
            return result

        # Find year columns
        for col in reader.fieldnames:
            if col not in mapped_cols.values():
                try:
                    year = int(col)
                    if target_years is None or year in target_years:
                        year_columns.append(col)
                except ValueError:
                    # Not a year column, ignore or treat as extra metadata
                    pass

        if not year_columns:
            result.errors.append("No valid year columns found")
            return result

        row_num = 1 # Header is 0, start counting rows from 1 for user visibility (actually 2 in editor)
        for row in reader:
            row_num += 1

            # Extract metadata
            try:
                scenario_raw = row[mapped_cols["Scenario"]]
                model = row[mapped_cols["Model"]]
                region = row[mapped_cols["Region"]]
                variable = row[mapped_cols["Variable"]]
                unit = row[mapped_cols["Unit"]]

                try:
                    scenario = SSPScenario.normalize(scenario_raw)
                except ValueError as e:
                    # Log warning but maybe skip row or track error
                    result.errors.append(f"Row {row_num}: Invalid scenario '{scenario_raw}'")
                    continue

                # Iterate over year columns
                for year_col in year_columns:
                    val_str = row.get(year_col, "").strip()
                    if not val_str:
                        continue # Skip empty values

                    try:
                        value = float(val_str)
                        year = int(year_col)

                        point = SSPDataPoint(
                            scenario=scenario,
                            model=model,
                            region=region,
                            variable=variable,
                            unit=unit,
                            year=year,
                            value=value
                        )
                        result.data.append(point)
                    except ValueError:
                         result.errors.append(f"Row {row_num}: Invalid value '{val_str}' for year {year_col}")

            except Exception as e:
                result.errors.append(f"Row {row_num}: Unexpected error: {str(e)}")

    except csv.Error as e:
        result.errors.append(f"CSV parsing error: {str(e)}")
    except Exception as e:
        result.errors.append(f"General error: {str(e)}")

    return result
