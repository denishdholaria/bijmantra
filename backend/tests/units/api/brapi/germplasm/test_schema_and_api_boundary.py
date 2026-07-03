import inspect

from app.api.brapi.v2 import germplasm as legacy_brapi_germplasm
from app.api.brapi.v2.germplasm import GermplasmCreate
from app.domains.germplasm.capabilities.accession_passport import (
    schemas as accession_passport_schemas,
)
from app.domains.germplasm.capabilities.accession_passport.adapters.api import (
    brapi_germplasm as capability_brapi_germplasm,
)
from app.domains.germplasm.capabilities.accession_passport.ports import (
    BrAPIGermplasmMCPDRecord,
    BrAPIGermplasmMutationData,
    BrAPIGermplasmPedigreeRecord,
    BrAPIGermplasmPedigreeRelation,
    BrAPIGermplasmProgenyRecord,
    BrAPIGermplasmProgenyResult,
    BrAPIGermplasmRecord,
)

from .support import backend_root as _backend_root


def test_brapi_germplasm_routes_use_accession_passport_policy_guards():
    source = (
        _backend_root()
        / "app/domains/germplasm/capabilities/accession_passport/adapters/api/brapi_germplasm.py"
    ).read_text()

    assert 'required_permission="germplasm.read"' in source
    assert 'required_permission="germplasm.passport.manage"' in source
    assert source.count("await _require_brapi_germplasm_read_access(current_user, db)") == 5
    assert source.count("await _require_brapi_germplasm_manage_access(current_user, db)") == 3

def test_brapi_germplasm_api_adapter_has_no_persistence_imports_or_db_work():
    source = (
        _backend_root()
        / "app/domains/germplasm/capabilities/accession_passport/adapters/api/brapi_germplasm.py"
    ).read_text()

    assert "from sqlalchemy" not in source
    assert "import sqlalchemy" not in source
    assert "app.models" not in source
    assert "app.modules" not in source
    assert "GermplasmModel" not in source
    assert "Cross" not in source
    assert "GermplasmService" not in source
    assert "build_brapi_germplasm_application_service" in source
    assert "SqlAlchemyBrAPIGermplasmReadAdapter" not in source
    assert "SqlAlchemyBrAPIGermplasmWriteAdapter" not in source
    assert "capabilities.accession_passport.ports import" not in source
    assert "BrAPIGermplasmListQuery" not in source
    assert "BrAPIGermplasmCreateCommand" not in source
    assert "BrAPIGermplasmUpdateCommand" not in source
    assert "BrAPIGermplasmDeleteCommand" not in source
    assert "_mutation_data_from_request" not in source
    for db_operation in (
        "db.execute",
        "db.add",
        "db.commit",
        "db.refresh",
        "db.delete",
    ):
        assert db_operation not in source

def test_brapi_germplasm_dtos_and_response_envelope_are_schema_owned():
    source = (
        _backend_root()
        / "app/domains/germplasm/capabilities/accession_passport/adapters/api/brapi_germplasm.py"
    ).read_text()

    assert "from pydantic" not in source
    assert "class GermplasmBase" not in source
    assert "class GermplasmCreate" not in source
    assert "class Germplasm(" not in source
    assert "def _model_to_brapi" not in source
    assert "def _record_from_model" not in source
    assert "brapi_germplasm_record_to_payload as _model_to_brapi" not in source
    assert "brapi_response as _brapi_response" not in source
    assert "GermplasmBase" not in source
    assert "Germplasm," not in source
    assert "BrAPIGermplasmCreateRequest" in source
    assert "brapi_response" in source
    assert not hasattr(capability_brapi_germplasm, "GermplasmBase")
    assert not hasattr(capability_brapi_germplasm, "GermplasmCreate")
    assert not hasattr(capability_brapi_germplasm, "Germplasm")
    assert not hasattr(capability_brapi_germplasm, "_model_to_brapi")
    assert not hasattr(capability_brapi_germplasm, "_brapi_response")
    assert legacy_brapi_germplasm.GermplasmBase is accession_passport_schemas.GermplasmBase
    assert legacy_brapi_germplasm.GermplasmCreate is accession_passport_schemas.GermplasmCreate
    assert legacy_brapi_germplasm.Germplasm is accession_passport_schemas.Germplasm
    assert (
        legacy_brapi_germplasm._model_to_brapi
        is accession_passport_schemas.brapi_germplasm_record_to_payload
    )
    assert legacy_brapi_germplasm._brapi_response is accession_passport_schemas.brapi_response

    record = BrAPIGermplasmRecord(
        germplasm_db_id="g1",
        germplasm_name="IR64",
        default_display_name=None,
        accession_number="ACC-1",
        genus="Oryza",
        species="sativa",
        synonyms=("IR-64", "IR 64"),
    )
    payload = accession_passport_schemas.brapi_germplasm_record_to_payload(record)

    assert payload["germplasmDbId"] == "g1"
    assert payload["germplasmName"] == "IR64"
    assert payload["defaultDisplayName"] == "IR64"
    assert payload["accessionNumber"] == "ACC-1"
    assert payload["genus"] == "Oryza"
    assert payload["species"] == "sativa"
    assert payload["synonyms"] == ["IR-64", "IR 64"]

    mutation_data = accession_passport_schemas.brapi_germplasm_request_to_mutation_data(
        GermplasmCreate(
            germplasmName="IR64",
            accessionNumber="ACC-1",
            genus="Oryza",
            species="sativa",
            synonyms=["IR-64", "IR 64"],
        )
    )

    assert mutation_data == BrAPIGermplasmMutationData(
        germplasm_name="IR64",
        accession_number="ACC-1",
        genus="Oryza",
        species="sativa",
        synonyms=("IR-64", "IR 64"),
    )

    no_synonym_mutation_data = (
        accession_passport_schemas.brapi_germplasm_request_to_mutation_data(
            GermplasmCreate(
                germplasmName="No Synonyms",
                synonyms=None,
            )
        )
    )

    assert no_synonym_mutation_data.synonyms is None

    response = accession_passport_schemas.brapi_response(
        [{"germplasmDbId": "g1"}],
        page=1,
        pageSize=2,
        total=5,
    )

    assert response["metadata"]["pagination"] == {
        "currentPage": 1,
        "pageSize": 2,
        "totalCount": 5,
        "totalPages": 3,
    }
    assert response["result"]["data"] == [{"germplasmDbId": "g1"}]

    pedigree_payload = accession_passport_schemas.brapi_germplasm_pedigree_to_payload(
        BrAPIGermplasmPedigreeRecord(
            germplasm_db_id="g1",
            germplasm_name="IR64",
            pedigree="P1/P2",
            crossing_project_db_id="crossing-project-1",
            crossing_year=2026,
            breeding_method_db_id="bm1",
            parents=(
                BrAPIGermplasmPedigreeRelation(
                    germplasm_db_id="p1",
                    germplasm_name="Parent 1",
                    parent_type="FEMALE",
                ),
            ),
            siblings=(
                BrAPIGermplasmPedigreeRelation(
                    germplasm_db_id="s1",
                    germplasm_name="Sibling 1",
                ),
            ),
        )
    )

    assert pedigree_payload["germplasmDbId"] == "g1"
    assert pedigree_payload["parents"] == [
        {
            "germplasmDbId": "p1",
            "germplasmName": "Parent 1",
            "parentType": "FEMALE",
        }
    ]
    assert pedigree_payload["siblings"] == [
        {
            "germplasmDbId": "s1",
            "germplasmName": "Sibling 1",
        }
    ]

    progeny_payload = accession_passport_schemas.brapi_germplasm_progeny_to_payload(
        BrAPIGermplasmProgenyResult(
            germplasm_db_id="g1",
            germplasm_name="IR64",
            progeny=(
                BrAPIGermplasmProgenyRecord(
                    germplasm_db_id="c1",
                    germplasm_name="Child 1",
                    parent_type="FEMALE",
                ),
            ),
            total=1,
        )
    )

    assert progeny_payload == {
        "germplasmDbId": "g1",
        "germplasmName": "IR64",
        "progeny": [
            {
                "germplasmDbId": "c1",
                "germplasmName": "Child 1",
                "parentType": "FEMALE",
            }
        ],
    }

    mcpd_payload = accession_passport_schemas.brapi_germplasm_mcpd_to_payload(
        BrAPIGermplasmMCPDRecord(
            germplasm_db_id="g1",
            accession_number="ACC-1",
            accession_names=("IR64",),
            acquisition_date="2026-01-01",
            acquisition_source_code="10",
            ancestral_data="P1/P2",
            biological_status_of_accession_code="500",
            collecting_date="2026-01-02",
            collecting_site="Los Banos",
            common_crop_name="rice",
            country_of_origin="PHL",
            genus="Oryza",
            germplasm_pui="pui:g1",
            institute_code="IRRI",
            species="sativa",
            storage_type_codes=("10",),
            subtaxon="indica",
        )
    )

    assert mcpd_payload["germplasmDbId"] == "g1"
    assert mcpd_payload["accessionNames"] == ["IR64"]
    assert mcpd_payload["acquisitionDate"] == "2026-01-01"
    assert mcpd_payload["collectingInfo"]["collectingSite"] == "Los Banos"
    assert mcpd_payload["storageTypeCodes"] == ["10"]

def test_standard_brapi_germplasm_reads_delegate_to_application_service():
    list_source = inspect.getsource(capability_brapi_germplasm.list_germplasm)
    get_source = inspect.getsource(capability_brapi_germplasm.get_germplasm)
    pedigree_source = inspect.getsource(capability_brapi_germplasm.get_germplasm_pedigree)
    progeny_source = inspect.getsource(capability_brapi_germplasm.get_germplasm_progeny)
    mcpd_source = inspect.getsource(capability_brapi_germplasm.get_germplasm_mcpd)
    specialized_source = "\n".join((pedigree_source, progeny_source, mcpd_source))

    assert "build_brapi_germplasm_application_service" in list_source
    assert "service.list_germplasm_for_request" in list_source
    assert "BrAPIGermplasmListQuery" not in list_source
    assert "select(" not in list_source
    assert "service.get_germplasm_for_request" in get_source
    assert "organization_id=getattr(current_user, \"organization_id\", None)" in get_source
    assert "select(" not in get_source
    assert "service.get_pedigree_for_request" in pedigree_source
    assert "service.get_progeny_for_request" in progeny_source
    assert "service.get_mcpd_for_request" in mcpd_source
    assert "BrAPIGermplasmPedigreeQuery" not in pedigree_source
    assert "BrAPIGermplasmProgenyQuery" not in progeny_source
    assert "BrAPIGermplasmMCPDQuery" not in mcpd_source
    assert "_brapi_operation_response" in list_source
    assert "_brapi_operation_response" in get_source
    assert "_brapi_operation_response" in pedigree_source
    assert "_brapi_operation_response" in progeny_source
    assert "_brapi_operation_response" in mcpd_source
    assert "_model_to_brapi" not in list_source
    assert "_model_to_brapi" not in get_source
    assert "_pedigree_to_brapi" not in pedigree_source
    assert "_progeny_to_brapi" not in progeny_source
    assert "_mcpd_to_brapi" not in mcpd_source
    assert "select(" not in specialized_source
    assert "selectinload" not in specialized_source
    assert "GermplasmModel" not in specialized_source
    assert "Cross" not in specialized_source

def test_standard_brapi_germplasm_writes_delegate_to_application_service():
    create_source = inspect.getsource(capability_brapi_germplasm.create_germplasm)
    update_source = inspect.getsource(capability_brapi_germplasm.update_germplasm)
    delete_source = inspect.getsource(capability_brapi_germplasm.delete_germplasm)
    combined_source = "\n".join((create_source, update_source, delete_source))

    assert "build_brapi_germplasm_application_service" in combined_source
    assert "service.create_germplasm_from_payload" in create_source
    assert "service.update_germplasm_from_payload" in update_source
    assert "service.delete_germplasm_for_request" in delete_source
    assert "BrAPIGermplasmCreateCommand" not in create_source
    assert "BrAPIGermplasmUpdateCommand" not in update_source
    assert "BrAPIGermplasmDeleteCommand" not in delete_source
    assert "_mutation_data_from_request" not in create_source
    assert "_mutation_data_from_request" not in update_source
    assert "_brapi_operation_response" in create_source
    assert "_brapi_operation_response" in update_source
    assert "_brapi_operation_response" in delete_source
    assert "_model_to_brapi" not in combined_source
    assert "organization_id=current_user.organization_id" in update_source
    assert "organization_id=current_user.organization_id" in delete_source
    assert "GermplasmModel(" not in combined_source
    assert "db.add" not in combined_source
    assert "db.commit" not in combined_source
    assert "db.refresh" not in combined_source
    assert "db.delete" not in combined_source
    assert "GermplasmService" not in combined_source
    assert "select(" not in create_source
    assert "select(" not in update_source
    assert "select(" not in delete_source

def test_legacy_brapi_germplasm_module_reexports_capability_adapter_symbols():
    for symbol_name in (
        "router",
        "list_germplasm",
        "create_germplasm",
        "get_germplasm",
        "update_germplasm",
        "delete_germplasm",
        "get_germplasm_pedigree",
        "get_germplasm_progeny",
        "get_germplasm_mcpd",
        "_require_brapi_germplasm_read_access",
        "_require_brapi_germplasm_manage_access",
        "get_tenant_db",
        "get_current_user",
        "get_optional_user",
    ):
        assert getattr(legacy_brapi_germplasm, symbol_name) is getattr(
            capability_brapi_germplasm,
            symbol_name,
        )
    assert legacy_brapi_germplasm.GermplasmBase is accession_passport_schemas.GermplasmBase
    assert legacy_brapi_germplasm.GermplasmCreate is accession_passport_schemas.GermplasmCreate
    assert legacy_brapi_germplasm.Germplasm is accession_passport_schemas.Germplasm
    assert legacy_brapi_germplasm._brapi_response is accession_passport_schemas.brapi_response
    assert (
        legacy_brapi_germplasm._model_to_brapi
        is accession_passport_schemas.brapi_germplasm_record_to_payload
    )

def test_brapi_germplasm_route_inventory_is_preserved():
    route_inventory = {
        (route.path, tuple(sorted(route.methods or ())))
        for route in capability_brapi_germplasm.router.routes
    }

    assert route_inventory == {
        ("/germplasm", ("GET",)),
        ("/germplasm", ("POST",)),
        ("/germplasm/{germplasmDbId}", ("DELETE",)),
        ("/germplasm/{germplasmDbId}", ("GET",)),
        ("/germplasm/{germplasmDbId}", ("PUT",)),
        ("/germplasm/{germplasmDbId}/mcpd", ("GET",)),
        ("/germplasm/{germplasmDbId}/pedigree", ("GET",)),
        ("/germplasm/{germplasmDbId}/progeny", ("GET",)),
    }
