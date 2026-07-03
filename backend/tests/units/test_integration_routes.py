from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.integrations import brapi  # noqa: F401
from app.integrations.routes import router


def test_list_available_integrations_includes_capability_metadata():
    app = FastAPI()
    app.include_router(router, prefix="/api/v2")

    with TestClient(app) as client:
        response = client.get("/api/v2/integrations/")

    assert response.status_code == 200
    payload = response.json()
    brapi_entry = next(item for item in payload["integrations"] if item["id"] == "brapi")
    assert brapi_entry["capability_tags"] == []
    assert brapi_entry["adapter_type"] == "external_service"


def test_get_integration_info_includes_capability_metadata():
    app = FastAPI()
    app.include_router(router, prefix="/api/v2")

    with TestClient(app) as client:
        response = client.get("/api/v2/integrations/brapi")

    assert response.status_code == 200
    payload = response.json()
    assert payload["capability_tags"] == ["germplasm", "trials", "observations", "seedlots", "programs"]
    assert payload["function_mappings"]["search_germplasm"] == "GET /brapi/v2/germplasm"
    assert payload["adapter_type"] == "api"
    assert payload["performance_profile"] == {
        "latency_ms": 200,
        "rate_limit_per_minute": 120,
        "timeout_seconds": 30,
        "concurrent_connections": 10,
    }