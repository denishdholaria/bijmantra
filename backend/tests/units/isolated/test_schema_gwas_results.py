"""
Isolated tests for GWAS Results Schema
"""
import pytest
from pydantic import ValidationError
from app.schemas.schema_gwas_results import GWASResultCreate, GWASResult


class TestGWASResultSchema:

    def test_valid_creation(self):
        """Test creating a valid GWASResultCreate"""
        data = {
            "marker_name": "M001",
            "linkage_group_name": "1A",
            "position": 1000,
            "p_value": 0.05,
            "trait_name": "Yield"
        }
        result = GWASResultCreate(**data)
        assert result.marker_name == "M001"
        assert result.linkage_group_name == "1A"
        assert result.position == 1000
        assert result.p_value == 0.05
        assert result.trait_name == "Yield"

    def test_invalid_p_value(self):
        """Test that p_value must be between 0 and 1"""
        data = {
            "marker_name": "M001",
            "linkage_group_name": "1A",
            "position": 1000,
            "p_value": 1.5,
            "trait_name": "Yield"
        }
        with pytest.raises(ValidationError) as exc:
            GWASResultCreate(**data)
        assert "p_value must be between 0 and 1" in str(exc.value)

        data["p_value"] = -0.1
        with pytest.raises(ValidationError) as exc:
            GWASResultCreate(**data)
        assert "p_value must be between 0 and 1" in str(exc.value)

    def test_invalid_position(self):
        """Test that position must be non-negative"""
        data = {
            "marker_name": "M001",
            "linkage_group_name": "1A",
            "position": -5,
            "p_value": 0.5,
            "trait_name": "Yield"
        }
        with pytest.raises(ValidationError) as exc:
            GWASResultCreate(**data)
        assert "position must be non-negative" in str(exc.value)

    def test_alias_population(self):
        """Test that we can populate using camelCase aliases (BrAPI style)"""
        data = {
            "markerName": "M002",
            "linkageGroupName": "1B",
            "position": 2000,
            "pValue": 0.01,
            "traitName": "Height"
        }
        result = GWASResultCreate(**data)
        assert result.marker_name == "M002"
        assert result.linkage_group_name == "1B"
        assert result.p_value == 0.01

    def test_serialization_aliases(self):
        """Test that serialization uses aliases by default if configured"""
        data = {
            "marker_name": "M003",
            "linkage_group_name": "2A",
            "position": 3000,
            "p_value": 0.001,
            "trait_name": "Protein",
            "result_db_id": "R001"
        }
        result = GWASResult(**data)
        dumped = result.model_dump(by_alias=True)
        assert "markerName" in dumped
        assert "linkageGroupName" in dumped
        assert "pValue" in dumped
        assert "resultDbId" in dumped
        assert dumped["markerName"] == "M003"
