
import pytest
from app.modules.genomics.compute.analytics.ssp_scenario_parser import parse_ssp_csv, SSPScenario, SSPDataPoint

def test_parse_valid_csv():
    csv_content = """Model,Scenario,Region,Variable,Unit,2020,2030,2050
ModelA,SSP1-1.9,World,Temperature,C,1.1,1.3,1.5
ModelB,SSP5-8.5,World,Temperature,C,1.1,1.5,2.0
"""
    result = parse_ssp_csv(csv_content)

    assert len(result.errors) == 0
    assert len(result.data) == 6 # 2 rows * 3 years

    # Check first row logic
    d1 = result.data[0]
    assert d1.scenario == SSPScenario.SSP1_19
    assert d1.year == 2020
    assert d1.value == 1.1

    d2 = result.data[1]
    assert d2.scenario == SSPScenario.SSP1_19
    assert d2.year == 2030
    assert d2.value == 1.3

    d3 = result.data[2]
    assert d3.scenario == SSPScenario.SSP1_19
    assert d3.year == 2050
    assert d3.value == 1.5

def test_parse_filter_years():
    csv_content = """Model,Scenario,Region,Variable,Unit,2020,2030,2050
ModelA,SSP1-1.9,World,Temperature,C,1.1,1.3,1.5
"""
    result = parse_ssp_csv(csv_content, target_years=[2030, 2050])

    assert len(result.errors) == 0
    assert len(result.data) == 2

    years = [d.year for d in result.data]
    assert 2030 in years
    assert 2050 in years
    assert 2020 not in years

def test_parse_invalid_scenario():
    csv_content = """Model,Scenario,Region,Variable,Unit,2030
ModelA,UnknownScenario,World,Temperature,C,1.3
"""
    result = parse_ssp_csv(csv_content)

    assert len(result.data) == 0
    assert len(result.errors) == 1
    assert "Invalid scenario 'UnknownScenario'" in result.errors[0]

def test_parse_invalid_value():
    csv_content = """Model,Scenario,Region,Variable,Unit,2030
ModelA,SSP1-1.9,World,Temperature,C,NotANumber
"""
    result = parse_ssp_csv(csv_content)

    assert len(result.data) == 0
    assert len(result.errors) == 1
    assert "Invalid value 'NotANumber'" in result.errors[0]

def test_parse_empty_content():
    result = parse_ssp_csv("")
    assert len(result.errors) > 0
    assert "Empty content" in result.errors[0]

def test_parse_missing_columns():
    csv_content = """Model,Region,Variable,Unit,2030
ModelA,World,Temperature,C,1.3
"""
    result = parse_ssp_csv(csv_content)
    assert len(result.errors) > 0
    assert "Missing required columns" in result.errors[0]

def test_scenario_normalization():
    csv_content = """Model,Scenario,Region,Variable,Unit,2030
ModelA,ssp119,World,Var,U,1.0
ModelB,SSP585,World,Var,U,1.0
"""
    result = parse_ssp_csv(csv_content)
    assert len(result.data) == 2
    assert result.data[0].scenario == SSPScenario.SSP1_19
    assert result.data[1].scenario == SSPScenario.SSP5_85

def test_case_insensitive_headers():
    csv_content = """model,scenario,region,variable,unit,2030
ModelA,SSP1-1.9,World,Temperature,C,1.3
"""
    result = parse_ssp_csv(csv_content)
    assert len(result.data) == 1
    assert result.data[0].year == 2030
