# backend/tests/services/test_cross_domain_gdd_service.py
import pytest
from sqlalchemy.orm import Session
from backend.app.services.cross_domain_gdd_service import CrossDomainGDDService
from datetime import date

def test_analyze_gdd_requirements(db_session: Session):
    service = CrossDomainGDDService(db_session)
    result = service.analyze_gdd_requirements(["maize_variety_1"])
    assert "gdd_requirements" in result
    assert "maize_variety_1" in result["gdd_requirements"]
    assert "uncertainty" in result

def test_match_varieties_to_thermal_history(db_session: Session):
    service = CrossDomainGDDService(db_session)
    result = service.match_varieties_to_thermal_history(1, ["maize_variety_1"])
    assert "variety_matches" in result
    assert "maize_variety_1" in result["variety_matches"]
    assert "uncertainty" in result

def test_recommend_varieties(db_session: Session):
    service = CrossDomainGDDService(db_session)
    result = service.recommend_varieties(1)
    assert "recommendations" in result
    assert len(result["recommendations"]) > 0
    assert "uncertainty" in result

def test_analyze_planting_windows(db_session: Session):
    service = CrossDomainGDDService(db_session)
    result = service.analyze_planting_windows(1, "maize")
    assert "planting_windows" in result
    assert len(result["planting_windows"]) > 0
    assert "uncertainty" in result

def test_predict_harvest_timing(db_session: Session):
    service = CrossDomainGDDService(db_session)
    planting_date = date(2023, 5, 1)
    result = service.predict_harvest_timing(1, planting_date, "maize")
    assert "predicted_harvest_date" in result
    assert "market_analysis" in result
    assert "uncertainty" in result

def test_create_climate_risk_alerts(db_session: Session):
    service = CrossDomainGDDService(db_session)
    result = service.create_climate_risk_alerts(1)
    assert "risk_alerts" in result
    assert len(result["risk_alerts"]) > 0
    assert "uncertainty" in result
