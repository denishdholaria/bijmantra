import csv
from datetime import datetime
from io import StringIO
from pathlib import Path

from app.domains.germplasm.capabilities.accession_passport.adapters import (
    SqlAlchemyMCPDExportAdapter,
    SqlAlchemyMCPDImportAdapter,
    mcpd_export_record_from_accession,
)
from app.domains.germplasm.capabilities.accession_passport.adapters.api.audit import (
    write_mcpd_audit_event,
)
from app.domains.germplasm.capabilities.accession_passport.application import (
    MCPDImportPlan,
    PlannedMCPDAccession,
    accession_to_mcpd,
    export_to_mcpd_csv,
    export_to_mcpd_json,
    get_mcpd_reference_service,
    import_mcpd_accessions,
    plan_mcpd_accession_import,
)
from app.domains.germplasm.capabilities.accession_passport.domain import (
    BIOLOGICAL_STATUS_CODES,
    MCPD_AUDIT_ACTIONS,
    MCPD_AUDIT_TARGET_TYPE,
    MCPD_EXPORTED,
    MCPD_IMPORTED,
    MCPD_TEMPLATE_EXAMPLE_ROW,
    MCPD_TEMPLATE_FIELDNAMES,
    country_name_to_iso,
    map_storage_to_vault_type,
    map_vault_type_to_storage,
    mcpd_to_accession_data,
    parse_mcpd_csv,
    parse_mcpd_date,
    validate_mcpd_record,
)
from app.domains.germplasm.capabilities.accession_passport.ports import (
    MCPDAccessionExportRecord,
    MCPDImportPersistenceError,
    MCPDImportPersistenceResult,
    MCPDImportRepository,
)
from app.domains.germplasm.capabilities.accession_passport.schemas import (
    MCPDImportResult,
    MCPDRecord,
)
from tests.utils.capability_boundary import assert_no_forbidden_imports, python_files


def _backend_root() -> Path:
    return Path(__file__).resolve().parents[5]


def _capability_root() -> Path:
    return _backend_root() / "app/domains/germplasm/capabilities/accession_passport"


class _EnumLike:
    def __init__(self, value: str) -> None:
        self.value = value


class _Vault:
    type = _EnumLike("base")


class _FakeAccession:
    accession_number = "ACC-001"
    genus = "Oryza"
    species = "sativa"
    subspecies = "indica"
    common_name = "Rice"
    origin = "India"
    collection_date = datetime(2024, 1, 15)
    collection_site = "Punjab"
    latitude = 30.7333
    longitude = 76.7794
    altitude = 250.0
    status = _EnumLike("active")
    vault = _Vault()
    mls = True
    donor_institution = "IRRI"
    pedigree = "IR8/TKM6"
    notes = "reference accession"


def test_mcpd_reference_service_builds_standard_template_csv() -> None:
    template_csv = get_mcpd_reference_service().template_csv()
    rows = list(csv.reader(StringIO(template_csv)))

    assert rows[0] == list(MCPD_TEMPLATE_FIELDNAMES)
    assert rows[1] == list(MCPD_TEMPLATE_EXAMPLE_ROW)
    assert rows[0].index("ACCENUMB") == 2
    assert rows[1][2] == "ACC-001"
    assert rows[1][-1] == "2.1"


def test_mcpd_reference_service_returns_standard_code_payloads() -> None:
    service = get_mcpd_reference_service()

    biological_status = service.biological_status_codes()
    acquisition_source = service.acquisition_source_codes()
    storage_type = service.storage_type_codes()
    countries = service.country_codes()

    assert biological_status["field"] == "SAMPSTAT"
    assert {"code": 500, "description": BIOLOGICAL_STATUS_CODES[500]} in biological_status["codes"]
    assert acquisition_source["field"] == "COLLSRC"
    assert {"code": 40, "description": "Institute, Experimental station, Research organization, Genebank"} in (
        acquisition_source["codes"]
    )
    assert storage_type["field"] == "STORAGE"
    assert {"code": 13, "description": "Long term (base collection)"} in storage_type["codes"]
    assert countries["field"] == "ORIGCTY"
    assert countries["codes"][0] == {"code": "AFG", "name": "Afghanistan"}


def test_mcpd_audit_event_vocabulary_is_specific_to_mcpd_operations() -> None:
    assert MCPD_AUDIT_ACTIONS == (
        "germplasm.mcpd_exported",
        "germplasm.mcpd_imported",
    )
    assert MCPD_EXPORTED in MCPD_AUDIT_ACTIONS
    assert MCPD_IMPORTED in MCPD_AUDIT_ACTIONS
    assert MCPD_AUDIT_TARGET_TYPE == "mcpd_accession_passport"


async def test_mcpd_audit_helper_writes_count_only_immutable_audit_log() -> None:
    class FakeDb:
        def __init__(self) -> None:
            self.added = []
            self.flushed = False

        def add(self, record) -> None:
            self.added.append(record)

        async def flush(self) -> None:
            self.flushed = True

    fake_db = FakeDb()

    await write_mcpd_audit_event(
        fake_db,
        organization_id=7,
        actor_user_id=42,
        action=MCPD_IMPORTED,
        method="POST",
        changes={
            "mcpdVersion": "2.1",
            "validateOnly": False,
            "skipDuplicates": True,
            "totalRecords": 3,
            "imported": 2,
            "skipped": 1,
            "errorCount": 0,
        },
    )

    audit_log = fake_db.added[0]

    assert fake_db.flushed is True
    assert audit_log.organization_id == 7
    assert audit_log.user_id == 42
    assert audit_log.action == "germplasm.mcpd_imported"
    assert audit_log.target_type == "mcpd_accession_passport"
    assert audit_log.target_id is None
    assert audit_log.method == "POST"
    assert audit_log.changes == {
        "mcpdVersion": "2.1",
        "validateOnly": False,
        "skipDuplicates": True,
        "totalRecords": 3,
        "imported": 2,
        "skipped": 1,
        "errorCount": 0,
    }


def test_mcpd_domain_parses_validates_and_maps_accession_rows() -> None:
    records = parse_mcpd_csv(
        "ACCENUMB,GENUS,ORIGCTY,LATITUDE,LONGITUDE,ELEVATION,MLSSTAT,COLLDATE,STORAGE\n"
        "ACC-001,Oryza,IND,30.7333,76.7794,250,1,20240115,13\n"
    )
    accession_data = mcpd_to_accession_data(records[0])

    assert validate_mcpd_record(records[0]) == []
    assert accession_data["accession_number"] == "ACC-001"
    assert accession_data["origin"] == "India"
    assert accession_data["collection_date"] == parse_mcpd_date("20240115")
    assert accession_data["latitude"] == 30.7333
    assert accession_data["mls"] is True
    assert country_name_to_iso("India") == "IND"
    assert map_vault_type_to_storage("base") == "13"
    assert map_storage_to_vault_type("13") == "base"


def test_mcpd_export_service_shapes_accessions_as_standard_csv_and_json() -> None:
    accession = MCPDAccessionExportRecord(
        accession_number="ACC-001",
        genus="Oryza",
        species="sativa",
        subspecies="indica",
        common_name="Rice",
        origin="India",
        collection_date=datetime(2024, 1, 15),
        collection_site="Punjab",
        latitude=30.7333,
        longitude=76.7794,
        altitude=250.0,
        status="active",
        vault_type="base",
        mls=True,
        donor_institution="IRRI",
        pedigree="IR8/TKM6",
        notes="reference accession",
    )

    record = accession_to_mcpd(accession, inst_code="BIJ999")
    payload = record.model_dump(by_alias=True)
    csv_rows = list(csv.DictReader(StringIO(export_to_mcpd_csv([accession], "BIJ999"))))
    json_payload = export_to_mcpd_json([accession], "BIJ999")

    assert isinstance(record, MCPDRecord)
    assert payload["INSTCODE"] == "BIJ999"
    assert payload["ACCENUMB"] == "ACC-001"
    assert payload["ORIGCTY"] == "IND"
    assert payload["COLLDATE"] == "20240115"
    assert payload["SAMPSTAT"] == 400
    assert payload["STORAGE"] == "13"
    assert payload["MLSSTAT"] == 1
    assert csv_rows[0]["ACCENUMB"] == "ACC-001"
    assert csv_rows[0]["INSTCODE"] == "BIJ999"
    assert csv_rows[0]["STORAGE"] == "13"
    assert json_payload[0]["ACCENUMB"] == "ACC-001"
    assert json_payload[0]["DONORNAME"] == "IRRI"


def test_mcpd_export_adapter_maps_legacy_accession_objects_to_capability_records() -> None:
    record = mcpd_export_record_from_accession(_FakeAccession())

    assert record == MCPDAccessionExportRecord(
        accession_number="ACC-001",
        genus="Oryza",
        species="sativa",
        subspecies="indica",
        common_name="Rice",
        origin="India",
        collection_date=datetime(2024, 1, 15),
        collection_site="Punjab",
        latitude=30.7333,
        longitude=76.7794,
        altitude=250.0,
        status="active",
        vault_type="base",
        mls=True,
        donor_institution="IRRI",
        pedigree="IR8/TKM6",
        notes="reference accession",
    )


async def test_mcpd_export_sqlalchemy_adapter_returns_capability_records() -> None:
    class FakeScalarResult:
        def all(self) -> list[_FakeAccession]:
            return [_FakeAccession()]

    class FakeExecuteResult:
        def scalars(self) -> FakeScalarResult:
            return FakeScalarResult()

    class FakeDb:
        async def execute(self, query) -> FakeExecuteResult:
            self.query = query
            return FakeExecuteResult()

    fake_db = FakeDb()
    adapter = SqlAlchemyMCPDExportAdapter(fake_db)

    records = await adapter.list_export_records(organization_id=77)

    assert records == [mcpd_export_record_from_accession(_FakeAccession())]
    assert "seed_bank_accessions" in str(fake_db.query)


def test_mcpd_import_result_schema_is_owned_by_accession_passport() -> None:
    result = MCPDImportResult(total_records=1, imported=1, skipped=0, errors=[])

    assert result.model_dump() == {
        "total_records": 1,
        "imported": 1,
        "skipped": 0,
        "errors": [],
    }


def test_mcpd_domain_reports_validation_errors() -> None:
    errors = validate_mcpd_record(
        {
            "ACCENUMB": "",
            "GENUS": "",
            "ORIGCTY": "ZZZ",
            "LATITUDE": "100",
            "LONGITUDE": "not-a-number",
            "SAMPSTAT": "12345",
            "COLLDATE": "20XX0101",
        }
    )

    assert "ACCENUMB (Accession Number) is required" in errors
    assert "GENUS is required" in errors
    assert "Invalid country code: ZZZ" in errors
    assert "LATITUDE must be between -90 and 90: 100" in errors
    assert "Invalid LONGITUDE value: not-a-number" in errors
    assert "Invalid SAMPSTAT code: 12345" in errors
    assert "Invalid COLLDATE format: 20XX0101" in errors


def test_mcpd_import_planner_preserves_duplicate_and_validation_policy() -> None:
    plan = plan_mcpd_accession_import(
        "ACCENUMB,GENUS,ORIGCTY,LATITUDE\n"
        "ACC-EXIST,Oryza,IND,30\n"
        "ACC-001,Oryza,IND,30\n"
        "ACC-001,Oryza,IND,30\n"
        ",,ZZZ,100\n",
        existing_accession_numbers={"ACC-EXIST"},
        skip_duplicates=True,
        validate_only=False,
    )

    assert plan.total_records == 4
    assert plan.accepted_count == 1
    assert plan.skipped == 2
    assert len(plan.accessions_to_create) == 1
    assert plan.accessions_to_create[0].row == 3
    assert plan.accessions_to_create[0].accession_number == "ACC-001"
    assert plan.accessions_to_create[0].accession_data["origin"] == "India"
    assert not any(key.startswith("_") for key in plan.accessions_to_create[0].accession_data)
    assert plan.errors[0].row == 5
    assert "ACCENUMB (Accession Number) is required" in plan.errors[0].errors


def test_mcpd_import_planner_preserves_validate_only_same_file_duplicate_behavior() -> None:
    plan = plan_mcpd_accession_import(
        "ACCENUMB,GENUS,ORIGCTY\n"
        "ACC-001,Oryza,IND\n"
        "ACC-001,Oryza,IND\n",
        existing_accession_numbers=set(),
        skip_duplicates=True,
        validate_only=True,
    )

    assert plan.total_records == 2
    assert plan.accepted_count == 2
    assert plan.skipped == 0
    assert plan.errors == ()
    assert plan.accessions_to_create == ()


async def test_mcpd_import_use_case_executes_validate_only_without_persistence() -> None:
    class FakeImportRepository:
        persisted = False

        async def list_existing_accession_numbers(self, organization_id: int) -> set[str]:
            self.organization_id = organization_id
            return {"ACC-EXIST"}

        async def persist_import_plan(
            self,
            *,
            organization_id: int,
            import_plan,
        ) -> MCPDImportPersistenceResult:
            self.persisted = True
            return MCPDImportPersistenceResult(imported=0, errors=())

    repository = FakeImportRepository()

    result = await import_mcpd_accessions(
        "ACCENUMB,GENUS,ORIGCTY\n"
        "ACC-EXIST,Oryza,IND\n"
        "ACC-NEW,Oryza,IND\n",
        repository=repository,
        organization_id=77,
        skip_duplicates=True,
        validate_only=True,
    )

    assert repository.organization_id == 77
    assert repository.persisted is False
    assert result.total_records == 2
    assert result.imported == 1
    assert result.skipped == 1
    assert result.errors == ()


async def test_mcpd_import_use_case_merges_persistence_errors() -> None:
    class FakeImportRepository:
        async def list_existing_accession_numbers(self, organization_id: int) -> set[str]:
            return set()

        async def persist_import_plan(
            self,
            *,
            organization_id: int,
            import_plan,
        ) -> MCPDImportPersistenceResult:
            self.organization_id = organization_id
            self.import_plan = import_plan
            return MCPDImportPersistenceResult(
                imported=0,
                errors=(
                    MCPDImportPersistenceError(
                        row=2,
                        accession_number="ACC-BAD",
                        errors=("cannot create accession",),
                    ),
                ),
            )

    repository = FakeImportRepository()

    result = await import_mcpd_accessions(
        "ACCENUMB,GENUS,ORIGCTY\n"
        "ACC-BAD,Oryza,IND\n",
        repository=repository,
        organization_id=77,
        skip_duplicates=True,
        validate_only=False,
    )

    assert repository.organization_id == 77
    assert repository.import_plan.accessions_to_create[0].accession_number == "ACC-BAD"
    assert result.total_records == 1
    assert result.imported == 0
    assert result.skipped == 0
    assert result.errors == (
        {
            "row": 2,
            "accession_number": "ACC-BAD",
            "errors": ["cannot create accession"],
        },
    )


async def test_mcpd_import_adapter_persists_planned_accessions_and_reports_errors() -> None:
    class FakeAccession:
        def __init__(self, **kwargs):
            if kwargs["accession_number"] == "ACC-BAD":
                raise ValueError("cannot create accession")
            self.kwargs = kwargs

    class FakeDb:
        def __init__(self) -> None:
            self.added = []
            self.committed = False

        def add(self, record) -> None:
            self.added.append(record)

        async def commit(self) -> None:
            self.committed = True

    fake_db = FakeDb()
    adapter = SqlAlchemyMCPDImportAdapter(fake_db, accession_model=FakeAccession)
    plan = MCPDImportPlan(
        total_records=2,
        accepted_count=2,
        skipped=0,
        errors=(),
        accessions_to_create=(
            PlannedMCPDAccession(
                row=2,
                accession_number="ACC-OK",
                accession_data={"accession_number": "ACC-OK", "genus": "Oryza"},
            ),
            PlannedMCPDAccession(
                row=3,
                accession_number="ACC-BAD",
                accession_data={"accession_number": "ACC-BAD", "genus": "Oryza"},
            ),
        ),
    )

    result = await adapter.persist_import_plan(
        organization_id=77,
        import_plan=plan,
    )

    assert result.imported == 1
    assert fake_db.committed is True
    assert fake_db.added[0].kwargs == {
        "accession_number": "ACC-OK",
        "genus": "Oryza",
        "organization_id": 77,
    }
    assert result.error_dicts() == [
        {
            "row": 3,
            "accession_number": "ACC-BAD",
            "errors": ["cannot create accession"],
        }
    ]


def test_mcpd_import_adapter_satisfies_repository_port() -> None:
    class FakeDb:
        async def execute(self, query):
            raise AssertionError("not called")

    adapter = SqlAlchemyMCPDImportAdapter(FakeDb())

    assert isinstance(adapter, MCPDImportRepository)


def test_mcpd_persistence_adapters_do_not_import_seed_bank_modules_directly() -> None:
    adapter_sources = [
        _capability_root() / "adapters/mcpd_export.py",
        _capability_root() / "adapters/mcpd_import.py",
    ]

    for adapter_source in adapter_sources:
        source = adapter_source.read_text()
        assert "app.modules.seed_bank" not in source
        assert "get_seed_bank_accession_model" in source


def test_germplasm_legacy_seed_bank_adapter_is_the_only_mcpd_orm_bridge() -> None:
    source = (_backend_root() / "app/domains/germplasm/adapters/legacy_seed_bank.py").read_text()

    assert "app.modules.seed_bank.models" in source
    assert "get_seed_bank_accession_model" in source


def test_accession_passport_inward_layers_do_not_import_legacy_or_infrastructure() -> None:
    inward_paths = (
        python_files(_capability_root() / "domain")
        + python_files(_capability_root() / "application")
        + python_files(_capability_root() / "ports")
        + python_files(_capability_root() / "schemas")
    )

    assert_no_forbidden_imports(
        inward_paths,
        (
            "app.api",
            "app.middleware",
            "app.models",
            "app.modules",
            "app.services",
            "fastapi",
            "sqlalchemy",
        ),
        repo_root=_backend_root(),
        boundary_name="AccessionPassport",
    )


def test_seed_bank_router_no_longer_mounts_capability_mcpd_router() -> None:
    from app.modules.seed_bank.router import router as seed_bank_router

    source = (_backend_root() / "app/modules/seed_bank/router.py").read_text()

    assert "accession_passport.adapters.api" not in source
    assert "mcpd_router" not in source
    assert "router.include_router" not in source
    assert '@router.get("/mcpd' not in source
    assert '@router.post("/mcpd' not in source
    assert "get_mcpd_reference_service" not in source
    assert "plan_mcpd_accession_import" not in source
    assert "SqlAlchemyMCPDImportAdapter" not in source
    assert "BIOLOGICAL_STATUS_CODES" not in source
    assert "COUNTRY_CODES" not in source
    assert "csv.writer" not in source
    assert "MCPD_TEMPLATE_FIELDNAMES" not in source
    assert "validate_mcpd_record" not in source
    assert "parse_mcpd_csv" not in source
    assert "mcpd_to_accession_data" not in source
    assert "MCPDImportResult" not in source
    assert not any("/mcpd" in route.path for route in seed_bank_router.routes)


def test_seed_bank_mcpd_route_inventory_is_owned_by_apex_mounted_capability_adapter() -> None:
    from app.api.bijmantra.apex_router import apex_router
    from app.domains.germplasm.capabilities.accession_passport.adapters.api import (
        router as capability_mcpd_router,
    )

    expected_seed_bank_routes = {
        ("/seed-bank/mcpd/export/csv", ("GET",)),
        ("/seed-bank/mcpd/export/json", ("GET",)),
        ("/seed-bank/mcpd/import", ("POST",)),
        ("/seed-bank/mcpd/template", ("GET",)),
        ("/seed-bank/mcpd/codes/biological-status", ("GET",)),
        ("/seed-bank/mcpd/codes/acquisition-source", ("GET",)),
        ("/seed-bank/mcpd/codes/storage-type", ("GET",)),
        ("/seed-bank/mcpd/codes/countries", ("GET",)),
    }
    expected_capability_routes = {
        (path.replace("/seed-bank", "", 1), methods)
        for path, methods in expected_seed_bank_routes
    }

    capability_routes = {
        (route.path, tuple(sorted(route.methods or [])))
        for route in capability_mcpd_router.routes
    }
    apex_mcpd_route_list = [
        (route.path, tuple(sorted(route.methods or [])))
        for route in apex_router.routes
        if "/seed-bank/mcpd" in route.path
    ]

    assert capability_routes == expected_capability_routes
    assert set(apex_mcpd_route_list) == expected_seed_bank_routes
    assert len(apex_mcpd_route_list) == len(expected_seed_bank_routes)


def test_accession_passport_mcpd_api_adapter_owns_route_logic() -> None:
    source = (
        _backend_root()
        / "app/domains/germplasm/capabilities/accession_passport/adapters/api/mcpd.py"
    ).read_text()

    assert '@router.post("/import"' in source
    assert '@router.get("/template"' in source
    assert '@router.get("/codes/biological-status"' in source
    assert "require_accession_passport_api_access" in source
    assert "write_mcpd_audit_event" in source
    assert "MCPD_EXPORTED" in source
    assert "MCPD_IMPORTED" in source
    assert "SqlAlchemyMCPDImportAdapter" in source
    assert "SqlAlchemyMCPDExportAdapter" in source
    assert "import_mcpd_accessions" in source
    assert "plan_mcpd_accession_import" not in source
    assert "list_existing_accession_numbers" not in source
    assert "persist_import_plan" not in source
    assert "get_mcpd_reference_service" in source
    assert "from sqlalchemy import select" not in source
    assert "app.modules.seed_bank.models" not in source
    assert "app.modules.seed_bank.router" not in source
    assert "app.modules.seed_bank.mcpd" not in source


def test_legacy_seed_bank_mcpd_module_imports_canonical_reference_tables() -> None:
    source = (_backend_root() / "app/modules/seed_bank/mcpd.py").read_text()

    assert "app.domains.germplasm.capabilities.accession_passport.adapters.mcpd_export" in source
    assert "app.domains.germplasm.capabilities.accession_passport.schemas" in source
    assert "app.domains.germplasm.capabilities.accession_passport.domain.mcpd_reference" in source
    assert "class MCPDRecord" not in source
    assert "class MCPDImportResult" not in source
    assert "def accession_to_mcpd(" not in source
    assert "def export_to_mcpd_csv(" not in source
    assert "def export_to_mcpd_json(" not in source
    assert "BIOLOGICAL_STATUS_CODES = {" not in source
    assert "ACQUISITION_SOURCE_CODES = {" not in source
    assert "STORAGE_TYPE_CODES = {" not in source
    assert "COUNTRY_CODES = {" not in source
    assert "def parse_mcpd_csv(" not in source
    assert "def validate_mcpd_record(" not in source
    assert "fieldnames = [" not in source
