from unittest.mock import AsyncMock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.deps import get_current_user
from app.api.v2 import ld as ld_module
from app.middleware.tenant_context import get_tenant_db


app = FastAPI()
app.include_router(ld_module.router)


async def override_get_tenant_db():
    yield object()


app.dependency_overrides[get_current_user] = lambda: {"id": 1, "organization_id": 1}
app.dependency_overrides[get_tenant_db] = override_get_tenant_db

client = TestClient(app)


def test_calculate_requires_variant_set_id():
    response = client.post("/ld/calculate", json={"window_size": 50})

    assert response.status_code == 400
    assert response.json()["detail"] == ld_module.LD_VARIANT_SET_REQUIRED_DETAIL


def test_matrix_requires_variant_set_id():
    response = client.get("/ld/matrix/region-1")

    assert response.status_code == 400
    assert response.json()["detail"] == ld_module.LD_VARIANT_SET_REQUIRED_DETAIL


def test_calculate_returns_empty_result_when_variant_set_has_no_usable_calls():
    with patch.object(
        ld_module.ld_service,
        "get_genotype_matrix",
        new=AsyncMock(return_value=([], ["M1", "M2"], [100, 200], 0)),
    ):
        response = client.post(
            "/ld/calculate",
            json={"variant_set_id": "vs-1", "window_size": 50},
        )

    assert response.status_code == 200
    assert response.json() == {
        "pairs": [],
        "mean_r2": 0.0,
        "marker_count": 2,
        "sample_count": 0,
    }