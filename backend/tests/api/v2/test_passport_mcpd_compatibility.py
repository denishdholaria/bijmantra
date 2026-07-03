from __future__ import annotations

import ast
from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.bijmantra.germplasm import passport as passport_api
from app.api.deps import get_current_user
from app.middleware.tenant_context import get_tenant_db
from app.modules.germplasm.services import passport_service as passport_service_module
from app.modules.germplasm.services.passport_service import GermplasmPassportService


ACCESSION_PASSPORT_CAPABILITY_ID = "germplasm_global_seed_registry.accession_passport"


def _backend_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _actor(
    *,
    organization_id: int = 7,
    installed_capabilities: tuple[str, ...] = (ACCESSION_PASSPORT_CAPABILITY_ID,),
    permissions: tuple[str, ...] = (
        "germplasm.read",
        "germplasm.passport.manage",
    ),
    data_scopes: tuple[str, ...] = (
        "organization",
        "collection",
        "accession",
        "material_transfer",
    ),
) -> SimpleNamespace:
    return SimpleNamespace(
        id=1,
        organization_id=organization_id,
        installed_capabilities=installed_capabilities,
        permissions=permissions,
        data_scopes=data_scopes,
        roles=("germplasm_curator",),
    )


@pytest.fixture
def client() -> TestClient:
    app = FastAPI()
    app.include_router(passport_api.router, prefix="/api/v2")
    app.dependency_overrides[get_current_user] = _actor
    app.dependency_overrides[get_tenant_db] = lambda: object()
    passport_service_module._passport_service = GermplasmPassportService()

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
    passport_service_module._passport_service = None


def test_legacy_passport_code_table_payloads_remain_stable(client: TestClient) -> None:
    biological_status = client.get("/api/v2/passport/biological-status-codes")
    acquisition_source = client.get("/api/v2/passport/acquisition-source-codes")

    assert biological_status.status_code == 200
    assert biological_status.json() == {
        "codes": [
            {"code": "100", "name": "Wild", "description": "Wild material"},
            {"code": "200", "name": "Weedy", "description": "Weedy form"},
            {
                "code": "300",
                "name": "Traditional cultivar/Landrace",
                "description": "Traditional cultivar or landrace",
            },
            {
                "code": "400",
                "name": "Breeding/Research material",
                "description": "Breeding line or research material",
            },
            {
                "code": "500",
                "name": "Advanced/Improved cultivar",
                "description": "Advanced or improved cultivar",
            },
            {"code": "600", "name": "GMO", "description": "Genetically modified organism"},
            {"code": "999", "name": "Other", "description": "Other (elaborate in remarks)"},
        ]
    }

    assert acquisition_source.status_code == 200
    assert acquisition_source.json() == {
        "codes": [
            {"code": "10", "name": "Wild habitat", "description": "Collected from wild habitat"},
            {
                "code": "20",
                "name": "Farm/Field",
                "description": "Collected from farm or cultivated field",
            },
            {"code": "30", "name": "Market", "description": "Obtained from market"},
            {
                "code": "40",
                "name": "Institute/Genebank",
                "description": "Obtained from research institute or genebank",
            },
            {"code": "50", "name": "Seed company", "description": "Obtained from seed company"},
            {"code": "99", "name": "Other", "description": "Other (elaborate in remarks)"},
        ]
    }


def test_legacy_passport_mcpd_export_payload_remains_stable(client: TestClient) -> None:
    register = client.post(
        "/api/v2/passport/accessions",
        json={
            "accession_id": "ACC-001",
            "accession_name": "IR64",
            "genus": "Oryza",
            "species": "sativa",
            "species_authority": "L.",
            "subtaxa": "indica",
            "common_name": "Rice",
            "biological_status": "500",
            "sample_type": "seed",
            "acquisition_source": "40",
            "acquisition_date": "2020-06-15",
            "donor_institute": "IRRI",
            "donor_accession": "IR64-DONOR",
            "pedigree": "IR5657-33-2-1/IR2061-465-1-5-5",
            "remarks": "legacy passport export",
            "storage_location": "ROOM-A-SHELF-1",
            "mls_status": "1",
        },
    )
    assert register.status_code == 200

    collection_site = client.post(
        "/api/v2/passport/accessions/ACC-001/collection-site",
        json={
            "country": "IND",
            "state_province": "Odisha",
            "municipality": "Cuttack",
            "locality": "Near Mahanadi River",
            "latitude": 20.4625,
            "longitude": 85.883,
            "elevation": 26,
            "collection_date": "2019-11-15",
            "collector_name": "Dr. R. Sharma",
            "collector_institute": "NRRI",
        },
    )
    assert collection_site.status_code == 200

    export = client.get("/api/v2/passport/export/mcpd?accession_ids=ACC-001,ACC-MISSING")

    assert export.status_code == 200
    assert export.json() == {
        "success": True,
        "format": "MCPD",
        "count": 1,
        "data": [
            {
                "ACCENUMB": "ACC-001",
                "ACCENAME": "IR64",
                "GENUS": "Oryza",
                "SPECIES": "sativa",
                "SPAUTHOR": "L.",
                "SUBTAXA": "indica",
                "SAMPSTAT": "500",
                "COLLSRC": "40",
                "ACQDATE": "20200615",
                "DONORCODE": "IRRI",
                "DONORNUMB": "IR64-DONOR",
                "ANCEST": "IR5657-33-2-1/IR2061-465-1-5-5",
                "REMARKS": "legacy passport export",
                "MLSSTAT": "1",
                "ORIGCTY": "IND",
                "COLLSITE": "Near Mahanadi River",
                "LATITUDE": 20.4625,
                "LONGITUDE": 85.883,
                "ELEVATION": 26.0,
                "COLLDATE": "20191115",
                "COLLNUMB": "",
                "COLLCODE": "NRRI",
            }
        ],
    }


def test_legacy_passport_mcpd_export_without_collection_site_keeps_sparse_shape(
    client: TestClient,
) -> None:
    register = client.post(
        "/api/v2/passport/accessions",
        json={
            "accession_id": "ACC-SPARSE",
            "accession_name": "Sparse",
            "genus": "Triticum",
            "species": "aestivum",
            "biological_status": "999",
            "sample_type": "seed",
            "acquisition_source": "99",
        },
    )
    assert register.status_code == 200

    export = client.get("/api/v2/passport/export/mcpd")

    assert export.status_code == 200
    payload = export.json()
    assert payload["success"] is True
    assert payload["format"] == "MCPD"
    assert payload["count"] == 1
    assert payload["data"] == [
        {
            "ACCENUMB": "ACC-SPARSE",
            "ACCENAME": "Sparse",
            "GENUS": "Triticum",
            "SPECIES": "aestivum",
            "SPAUTHOR": "",
            "SUBTAXA": "",
            "SAMPSTAT": "999",
            "COLLSRC": "99",
            "ACQDATE": "",
            "DONORCODE": "",
            "DONORNUMB": "",
            "ANCEST": "",
            "REMARKS": "",
            "MLSSTAT": "",
        }
    ]


def test_legacy_passport_routes_are_isolated_by_organization() -> None:
    current_actor = {"value": _actor(organization_id=7)}
    app = FastAPI()
    app.include_router(passport_api.router, prefix="/api/v2")
    app.dependency_overrides[get_current_user] = lambda: current_actor["value"]
    app.dependency_overrides[get_tenant_db] = lambda: object()
    passport_service_module._passport_service = GermplasmPassportService()

    with TestClient(app) as test_client:
        org7_register = test_client.post(
            "/api/v2/passport/accessions",
            json={
                "accession_id": "ACC-SHARED",
                "accession_name": "Org Seven",
                "genus": "Oryza",
                "species": "sativa",
            },
        )
        assert org7_register.status_code == 200

        current_actor["value"] = _actor(organization_id=8)

        org8_list = test_client.get("/api/v2/passport/accessions")
        org8_get_org7 = test_client.get("/api/v2/passport/accessions/ACC-SHARED")
        org8_search = test_client.get("/api/v2/passport/search?q=Org")
        org8_export = test_client.get("/api/v2/passport/export/mcpd")
        org8_stats = test_client.get("/api/v2/passport/statistics")

        assert org8_list.status_code == 200
        assert org8_list.json()["count"] == 0
        assert org8_list.json()["accessions"] == []
        assert org8_get_org7.status_code == 404
        assert org8_search.status_code == 200
        assert org8_search.json()["count"] == 0
        assert org8_export.status_code == 200
        assert org8_export.json()["count"] == 0
        assert org8_export.json()["data"] == []
        assert org8_stats.status_code == 200
        assert org8_stats.json()["total_accessions"] == 0

        org8_register = test_client.post(
            "/api/v2/passport/accessions",
            json={
                "accession_id": "ACC-SHARED",
                "accession_name": "Org Eight",
                "genus": "Triticum",
                "species": "aestivum",
            },
        )
        assert org8_register.status_code == 200

        org8_collection_site = test_client.post(
            "/api/v2/passport/accessions/ACC-SHARED/collection-site",
            json={
                "country": "USA",
                "state_province": "Iowa",
                "municipality": "Ames",
                "locality": "Org Eight Field",
                "latitude": 42.0308,
                "longitude": -93.6319,
                "elevation": 287,
                "collection_date": "2022-08-10",
                "collector_name": "Org Eight Curator",
                "collector_institute": "ORG8",
            },
        )
        assert org8_collection_site.status_code == 200

        current_actor["value"] = _actor(organization_id=7)
        org7_list = test_client.get("/api/v2/passport/accessions")
        org7_get_shared = test_client.get("/api/v2/passport/accessions/ACC-SHARED")
        org7_export = test_client.get("/api/v2/passport/export/mcpd?accession_ids=ACC-SHARED")

        assert org7_list.status_code == 200
        assert org7_list.json()["count"] == 1
        assert org7_list.json()["accessions"][0]["accession_id"] == "ACC-SHARED"
        assert org7_list.json()["accessions"][0]["accession_name"] == "Org Seven"
        assert org7_get_shared.status_code == 200
        assert org7_get_shared.json()["accession_name"] == "Org Seven"
        assert org7_get_shared.json()["collection_site"] is None
        assert org7_export.status_code == 200
        assert org7_export.json()["count"] == 1
        assert org7_export.json()["data"][0]["ACCENUMB"] == "ACC-SHARED"
        assert org7_export.json()["data"][0]["ACCENAME"] == "Org Seven"

        current_actor["value"] = _actor(organization_id=8)
        org8_get_shared = test_client.get("/api/v2/passport/accessions/ACC-SHARED")
        org8_export = test_client.get("/api/v2/passport/export/mcpd?accession_ids=ACC-SHARED")

        assert org8_get_shared.status_code == 200
        assert org8_get_shared.json()["accession_name"] == "Org Eight"
        assert org8_get_shared.json()["collection_site"]["locality"] == "Org Eight Field"
        assert org8_export.status_code == 200
        assert org8_export.json()["count"] == 1
        assert org8_export.json()["data"][0]["ACCENAME"] == "Org Eight"
        assert org8_export.json()["data"][0]["COLLSITE"] == "Org Eight Field"

    app.dependency_overrides.clear()
    passport_service_module._passport_service = None


def test_legacy_passport_read_routes_reject_uninstalled_capability_before_payload() -> None:
    app = FastAPI()
    app.include_router(passport_api.router, prefix="/api/v2")
    app.dependency_overrides[get_current_user] = lambda: _actor(installed_capabilities=())
    app.dependency_overrides[get_tenant_db] = lambda: object()

    with TestClient(app) as denied_client:
        response = denied_client.get("/api/v2/passport/biological-status-codes")

    app.dependency_overrides.clear()

    assert response.status_code == 403
    assert response.json()["detail"] == {
        "reason": "capability_not_installed",
        "capabilityId": ACCESSION_PASSPORT_CAPABILITY_ID,
        "missingPermissions": [],
        "missingDataScopes": [],
    }


def test_legacy_passport_write_routes_reject_missing_manage_permission_before_service(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_if_service_is_touched():
        raise AssertionError("passport service should not be touched before access is allowed")

    app = FastAPI()
    app.include_router(passport_api.router, prefix="/api/v2")
    app.dependency_overrides[get_current_user] = lambda: _actor(permissions=("germplasm.read",))
    app.dependency_overrides[get_tenant_db] = lambda: object()
    monkeypatch.setattr(passport_api, "get_passport_service", fail_if_service_is_touched)

    with TestClient(app) as denied_client:
        response = denied_client.post(
            "/api/v2/passport/accessions",
            json={
                "accession_id": "ACC-DENIED",
                "accession_name": "Denied",
                "genus": "Oryza",
                "species": "sativa",
            },
        )

    app.dependency_overrides.clear()

    assert response.status_code == 403
    assert response.json()["detail"] == {
        "reason": "missing_permission",
        "capabilityId": ACCESSION_PASSPORT_CAPABILITY_ID,
        "missingPermissions": ["germplasm.passport.manage"],
        "missingDataScopes": [],
    }


def test_legacy_passport_read_routes_reject_missing_accession_scope_before_service(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_if_service_is_touched():
        raise AssertionError("passport service should not be touched before access is allowed")

    app = FastAPI()
    app.include_router(passport_api.router, prefix="/api/v2")
    app.dependency_overrides[get_current_user] = lambda: _actor(data_scopes=("organization",))
    app.dependency_overrides[get_tenant_db] = lambda: object()
    monkeypatch.setattr(passport_api, "get_passport_service", fail_if_service_is_touched)

    with TestClient(app) as denied_client:
        response = denied_client.get("/api/v2/passport/accessions")

    app.dependency_overrides.clear()

    assert response.status_code == 403
    assert response.json()["detail"] == {
        "reason": "missing_data_scope",
        "capabilityId": ACCESSION_PASSPORT_CAPABILITY_ID,
        "missingPermissions": [],
        "missingDataScopes": ["accession"],
    }


def test_legacy_passport_mcpd_ownership_delegates_to_accession_passport_capability() -> None:
    route_source = (_backend_root() / "app/api/bijmantra/germplasm/passport.py").read_text()
    service_source = (
        _backend_root() / "app/modules/germplasm/services/passport_service.py"
    ).read_text()

    assert "require_accession_passport_api_access" in route_source
    assert "required_permission=\"germplasm.read\"" in route_source
    assert "required_permission=\"germplasm.passport.manage\"" in route_source
    assert "legacy_bijmantra_passport_biological_status_codes" in route_source
    assert "legacy_bijmantra_passport_acquisition_source_codes" in route_source
    assert "Wild material" not in route_source
    assert "Obtained from research institute or genebank" not in route_source

    assert "legacy_bijmantra_passport_to_mcpd" in service_source
    assert "export_legacy_bijmantra_passports_to_mcpd" in service_source
    assert "passports_by_organization" in service_source
    assert '"ACCENUMB": self.accession_id' not in service_source
    assert '"COLLSITE": self.collection_site.locality' not in service_source


def test_legacy_passport_routes_remain_behind_accession_passport_policy() -> None:
    route_source = (_backend_root() / "app/api/bijmantra/germplasm/passport.py").read_text()
    module = ast.parse(route_source)
    route_functions = {}

    for node in module.body:
        if not isinstance(node, ast.AsyncFunctionDef):
            continue
        for decorator in node.decorator_list:
            if isinstance(decorator, ast.Call) and ast.unparse(decorator.func).startswith("router."):
                route_functions[node.name] = ast.get_source_segment(route_source, node) or ""

    read_routes = {
        "list_accessions",
        "get_passport",
        "search_accessions",
        "export_mcpd",
        "get_statistics",
        "list_biological_status_codes",
        "list_acquisition_source_codes",
    }
    manage_routes = {
        "register_accession",
        "add_collection_site",
    }

    assert set(route_functions) == read_routes | manage_routes
    for route_name in read_routes:
        assert "await _require_passport_read_access(current_user, db)" in route_functions[route_name]
    for route_name in manage_routes:
        assert "await _require_passport_manage_access(current_user, db)" in route_functions[route_name]

    for route_name in read_routes | manage_routes:
        route_source_segment = route_functions[route_name]
        if "get_passport_service()" in route_source_segment:
            assert route_source_segment.index("await _require_passport_") < route_source_segment.index(
                "get_passport_service()"
            )
