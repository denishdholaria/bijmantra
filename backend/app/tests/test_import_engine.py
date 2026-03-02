import pytest

from app.services.import_engine.base import BaseImporter
from app.services.import_engine.validator import SchemaValidator


class DummyImporter(BaseImporter):
    model = object
    required_fields = {"name", "organization_id"}
    allowed_fields = {"name", "organization_id", "value", "computed"}
    defaults = {"organization_id": 77}

    @property
    def domain(self) -> str:
        return "dummy"

    async def resolve_foreign_keys(self, row: dict[str, object]) -> dict[str, object]:
        row["resolved"] = True
        return row


@pytest.mark.asyncio
async def test_base_importer_validate_rows_mapping_formula_defaults():
    importer = DummyImporter(db=None, organization_id=77, user_id=2)
    rows = [
        {"Name": "A", "value": "3"},
        {"Name": "", "value": "9"},
    ]

    valid_rows, report = await importer.validate_rows(
        rows,
        mapping={"Name": "name"},
        formulas={"computed": "N-{name}-{value}"},
    )

    assert len(valid_rows) == 1
    assert valid_rows[0]["name"] == "A"
    assert valid_rows[0]["organization_id"] == 77
    assert valid_rows[0]["computed"] == "N-A-3"
    assert valid_rows[0]["resolved"] is True
    assert report.success_count == 1
    assert len(report.errors) == 1


def test_schema_validator_fuzzy_and_alias_mapping():
    validator = SchemaValidator(expected_fields={"germplasm_id", "germplasm_name"})

    ok, missing, mapped = validator.validate_headers(["G_ID", "GermplasmName"])

    assert ok is True
    assert missing == []
    assert mapped["G_ID"] == "germplasm_id"
    assert mapped["GermplasmName"] == "germplasm_name"
