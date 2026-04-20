import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_grin_search(authenticated_client: AsyncClient):
    """Test GRIN-Global search endpoint (should return empty list as it's a stub)"""
    response = await authenticated_client.get(
        "/api/v2/grin/grin-global/search", params={"genus": "Triticum"}
    )
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_gwas_glm(authenticated_client: AsyncClient):
    """Test GWAS GLM endpoint with dummy data"""
    data = {
        "genotypes": [[0, 1, 2], [1, 1, 0], [2, 0, 1]],
        "phenotypes": [5.2, 4.8, 5.5],
        "markers": [
            {"name": "SNP1", "chromosome": "1", "position": 1000},
            {"name": "SNP2", "chromosome": "1", "position": 2000},
            {"name": "SNP3", "chromosome": "2", "position": 1500},
        ],
    }
    response = await authenticated_client.post("/api/v2/gwas/glm", json=data)
    assert response.status_code == 200
    result = response.json()
    assert result["method"] == "GLM"
    assert result["n_markers"] == 3
    assert "markers" in result


@pytest.mark.asyncio
async def test_gxe_finlay_wilkinson(authenticated_client: AsyncClient):
    """Test GxE Finlay-Wilkinson endpoint with dummy data"""
    data = {
        "yield_matrix": [
            [4.5, 5.2, 3.8, 4.9],
            [5.1, 4.8, 4.2, 5.5],
            [3.9, 4.5, 3.5, 4.2],
        ],
        "genotype_names": ["G1", "G2", "G3"],
        "environment_names": ["E1", "E2", "E3", "E4"],
    }
    response = await authenticated_client.post("/api/v2/gxe/finlay-wilkinson", json=data)
    assert response.status_code == 200
    result = response.json()
    assert result["method"] == "Finlay-Wilkinson"
    assert len(result["slopes"]) == 3


@pytest.mark.asyncio
async def test_haplotype_statistics(authenticated_client: AsyncClient):
    """Test Haplotype statistics endpoint"""
    response = await authenticated_client.get("/api/v2/haplotype/statistics")
    assert response.status_code == 200
    result = response.json()
    assert result["success"] is True
    assert "data" in result


@pytest.mark.asyncio
async def test_harvest_plan_async(authenticated_client: AsyncClient):
    """Test creating a harvest plan (verifies async conversion)"""
    data = {
        "trial_id": "TRL-TEST",
        "plot_id": "PLT-TEST",
        "crop": "Rice",
        "variety": "TestVar",
        "planned_date": "2024-12-01",
        "area_ha": 1.5,
        "notes": "Async test",
    }
    response = await authenticated_client.post("/api/v2/harvest/harvests", json=data)
    assert response.status_code == 200
    result = response.json()
    assert result["status"] == "success"
    assert result["data"]["crop"] == "Rice"
