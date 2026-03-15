import pytest
from app.modules.breeding.services.selection_index_service import selection_index_service

def test_smith_hazel_basic():
    phenotypes = [
        {"id": "IND1", "yield": 100, "protein": 12},
        {"id": "IND2", "yield": 90, "protein": 14},
    ]
    traits = ["yield", "protein"]
    weights = [1.0, 0.5]
    h2 = [0.4, 0.6]
    
    result = selection_index_service.smith_hazel_index(
        phenotypic_values=phenotypes,
        trait_names=traits,
        economic_weights=weights,
        heritabilities=h2
    )
    
    assert result["method"] == "smith_hazel"
    assert len(result["results"]) == 2
    # Check if results are sorted descending
    assert result["results"][0]["index_value"] >= result["results"][1]["index_value"]

def test_desired_gains():
    phenotypes = [
        {"id": "IND1", "yield": 100},
        {"id": "IND2", "yield": 90},
    ]
    traits = ["yield"]
    gains = [10.0]
    h2 = [0.5]
    
    result = selection_index_service.desired_gains_index(
        phenotypic_values=phenotypes,
        trait_names=traits,
        desired_gains=gains,
        heritabilities=h2
    )
    
    assert result["method"] == "desired_gains"
    assert "calculated_weights" in result

def test_predict_response_phenotypic():
    # R = i * h^2 * sigma_p
    # i=1.0, h^2=0.5, sigma_p=10
    # R = 1.0 * 0.5 * 10 = 5.0
    result = selection_index_service.predict_response(
        selection_intensity=1.0,
        heritability=0.5,
        phenotypic_std=10.0
    )
    
    assert result["predicted_response"] == 5.0
    assert result["annual_response"] == 5.0 # Default L=1
    assert "i × h² × σp" in result["formula"]

def test_predict_response_genomic():
    # R = i * r * h * sigma_p / L
    # i=1.0, h^2=0.25 -> h=0.5, sigma_p=10, r=0.8, L=2
    # R_cycle = 1.0 * 0.8 * 0.5 * 10 = 4.0
    # Annual = 4.0 / 2 = 2.0
    result = selection_index_service.predict_response(
        selection_intensity=1.0,
        heritability=0.25,
        phenotypic_std=10.0,
        accuracy=0.8,
        generation_interval=2.0
    )
    
    assert result["response_per_cycle"] == 4.0
    assert result["annual_response"] == 2.0
    assert "i × r × h × σp" in result["formula"]

def test_predict_response_annual():
    # Phenotypic with L=5
    # R = 1 * 0.5 * 10 = 5.0
    # Annual = 1.0
    result = selection_index_service.predict_response(
        selection_intensity=1.0,
        heritability=0.5,
        phenotypic_std=10.0,
        generation_interval=5.0
    )
    
    assert result["response_per_cycle"] == 5.0
    assert result["annual_response"] == 1.0
