import pytest
from app.services.infra.csv_enterprise_regex_mapper import (
    CsvRegexMapper,
    MapperConfig,
    MappingRule,
    TransformationRule,
    TransformationType
)

@pytest.fixture
def mapper():
    return CsvRegexMapper()

@pytest.fixture
def sample_csv():
    return """id,name,value,date
1,Apple,10.5,2023-01-01
2,Banana,20.0,2023-01-02
3,Cherry,,2023-01-03
"""

def test_basic_mapping(mapper, sample_csv):
    config = MapperConfig(
        rules=[
            MappingRule(target_column="product_id", source_column="id"),
            MappingRule(target_column="product_name", source_column="name"),
        ]
    )
    result = mapper.process(sample_csv, config)
    assert len(result) == 3
    assert result[0]["product_id"] == "1"
    assert result[0]["product_name"] == "Apple"

def test_transformations(mapper, sample_csv):
    config = MapperConfig(
        rules=[
            MappingRule(
                target_column="upper_name",
                source_column="name",
                transformations=[
                    TransformationRule(type=TransformationType.UPPERCASE)
                ]
            ),
            MappingRule(
                target_column="year",
                source_column="date",
                transformations=[
                    TransformationRule(
                        type=TransformationType.REGEX_EXTRACT,
                        pattern=r"^(\d{4})",
                        group=1
                    )
                ]
            )
        ]
    )
    result = mapper.process(sample_csv, config)
    assert result[0]["upper_name"] == "APPLE"
    assert result[0]["year"] == "2023"

def test_static_and_default(mapper, sample_csv):
    config = MapperConfig(
        rules=[
            MappingRule(
                target_column="source",
                transformations=[
                    TransformationRule(type=TransformationType.STATIC, value="csv_import")
                ]
            ),
            MappingRule(
                target_column="default_val",
                source_column="missing_col",
                default_value="N/A"
            ),
             MappingRule(
                target_column="filled_val",
                source_column="value",
                default_value="0.0" # "Cherry" has empty value
            )
        ]
    )
    result = mapper.process(sample_csv, config)
    assert result[0]["source"] == "csv_import"
    assert result[0]["default_val"] == "N/A"

    # Check 3rd row (Cherry) for empty value default
    # Note: empty string is not None, but process logic handles empty string as needing default
    assert result[2]["filled_val"] == "0.0"
    assert result[1]["filled_val"] == "20.0"

def test_missing_column_behavior(mapper, sample_csv):
    config = MapperConfig(
        rules=[
            MappingRule(target_column="test", source_column="non_existent")
        ]
    )
    result = mapper.process(sample_csv, config)
    # Missing column results in None
    assert result[0]["test"] is None

def test_regex_sub(mapper):
    csv = "code\nABC-123\nXYZ-456"
    config = MapperConfig(
        rules=[
            MappingRule(
                target_column="clean_code",
                source_column="code",
                transformations=[
                    TransformationRule(
                        type=TransformationType.REGEX_SUB,
                        pattern=r"-",
                        replacement=""
                    )
                ]
            )
        ]
    )
    result = mapper.process(csv, config)
    assert result[0]["clean_code"] == "ABC123"

def test_required_field_validation(mapper, sample_csv):
    config = MapperConfig(
        rules=[
            MappingRule(target_column="req_val", source_column="value", required=True),
            MappingRule(target_column="req_date", source_column="date", required=True)
        ]
    )
    # The 3rd row (Cherry) has empty "value". Should raise ValueError.
    with pytest.raises(ValueError, match="Required field 'req_val' is missing or empty"):
        mapper.process(sample_csv, config)
