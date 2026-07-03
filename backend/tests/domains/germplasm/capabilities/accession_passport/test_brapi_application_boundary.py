from pathlib import Path

from tests.utils.capability_boundary import assert_no_forbidden_imports


def _backend_root() -> Path:
    return Path(__file__).resolve().parents[5]


def _capability_root() -> Path:
    return (
        _backend_root()
        / "app/domains/germplasm/capabilities/accession_passport"
    )


def test_brapi_germplasm_application_service_keeps_hexagonal_boundary() -> None:
    service_path = _capability_root() / "application/brapi_germplasm_service.py"

    assert_no_forbidden_imports(
        [service_path],
        (
            "app.api",
            "app.middleware",
            "app.models",
            "app.modules",
            "app.services",
            "fastapi",
            "sqlalchemy",
            "app.domains.germplasm.capabilities.accession_passport.adapters",
        ),
        repo_root=_backend_root(),
        boundary_name="AccessionPassportBrAPIApplication",
    )


def test_brapi_germplasm_application_service_owns_request_boundary() -> None:
    source = (
        _capability_root() / "application/brapi_germplasm_service.py"
    ).read_text()

    assert "build_brapi_germplasm_application_service" not in source
    assert "SqlAlchemyBrAPIGermplasmReadAdapter" not in source
    assert "SqlAlchemyBrAPIGermplasmWriteAdapter" not in source
    assert "HTTPException" not in source
    assert "Depends" not in source
    assert "APIRouter" not in source
    assert "get_current_user" not in source
    assert "get_tenant_db" not in source
    assert "BrAPIGermplasmCreateCommand" in source
    assert "BrAPIGermplasmUpdateCommand" in source
    assert "BrAPIGermplasmDeleteCommand" in source
    assert "BrAPIGermplasmListQuery" in source
    assert "BrAPIGermplasmPedigreeQuery" in source
    assert "BrAPIGermplasmProgenyQuery" in source
    assert "BrAPIGermplasmMCPDQuery" in source
    assert "brapi_germplasm_request_to_mutation_data" in source
    assert "create_germplasm_from_payload" in source
    assert "update_germplasm_from_payload" in source
    assert "delete_germplasm_for_request" in source
