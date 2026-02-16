from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterable
from sqlalchemy import insert, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user_management import ActivityLog
from app.services.import_engine.schemas import ValidationMessage, ValidationReport
from app.services.import_engine.validator import SchemaValidator


class BaseImporter(ABC):
    model = None
    required_fields: set[str] = set()
    allowed_fields: set[str] = set()
    defaults: dict[str, object] = {}

    def __init__(self, db: AsyncSession, organization_id: int, user_id: int):
        self.db = db
        self.organization_id = organization_id
        self.user_id = user_id
        self.validator = SchemaValidator(self.required_fields)

    @property
    @abstractmethod
    def domain(self) -> str:
        raise NotImplementedError

    @abstractmethod
    async def resolve_foreign_keys(self, row: dict[str, object]) -> dict[str, object]:
        return row

    def apply_mapping(self, row: dict[str, object], mapping: dict[str, str] | None = None) -> dict[str, object]:
        mapping = mapping or {}
        converted: dict[str, object] = {}
        for source_key, value in row.items():
            key = mapping.get(source_key, source_key)
            converted[key] = value
        return converted

    def apply_formulas(self, row: dict[str, object], formulas: dict[str, str] | None = None) -> dict[str, object]:
        formulas = formulas or {}
        for field, template in formulas.items():
            try:
                row[field] = template.format(**row)
            except Exception:
                continue
        return row

    def apply_defaults(self, row: dict[str, object]) -> dict[str, object]:
        for field, val in self.defaults.items():
            if row.get(field) in (None, ""):
                row[field] = val
        return row

    async def suggest_mappings(self, headers: list[str]) -> dict[str, str]:
        from app.models.import_job import ImportJob

        query = select(ImportJob.mapping_config).where(
            ImportJob.organization_id == self.organization_id,
            ImportJob.import_type == self.domain,
            ImportJob.status == "completed",
        ).order_by(ImportJob.id.desc()).limit(5)
        result = await self.db.execute(query)
        candidates = result.scalars().all()

        suggestions = self.validator.map_headers(headers)
        for cfg in candidates:
            if isinstance(cfg, dict):
                for key, val in cfg.items():
                    if key in headers and val in self.allowed_fields:
                        suggestions[key] = val
        return suggestions

    async def validate_rows(
        self,
        rows: Iterable[dict[str, object]],
        mapping: dict[str, str] | None = None,
        formulas: dict[str, str] | None = None,
    ) -> tuple[list[dict[str, object]], ValidationReport]:
        report = ValidationReport()
        valid_rows: list[dict[str, object]] = []
        mapping = mapping or {}

        for idx, raw in enumerate(rows, start=1):
            row = self.apply_mapping(raw, mapping)
            row = self.apply_formulas(row, formulas)
            row = self.apply_defaults(row)

            missing = [field for field in self.required_fields if not row.get(field)]
            if missing:
                for field in missing:
                    report.errors.append(ValidationMessage(row=idx, field=field, message="Missing required field"))
                continue

            row = await self.resolve_foreign_keys(row)
            valid_rows.append(row)

        report.success_count = len(valid_rows)
        return valid_rows, report

    async def bulk_insert(self, rows: list[dict[str, object]]) -> int:
        if not rows:
            return 0
        stmt = insert(self.model).values(rows)
        await self.db.execute(stmt)
        return len(rows)

    async def log_activity(self, details: str) -> None:
        self.db.add(ActivityLog(
            organization_id=self.organization_id,
            user_id=self.user_id,
            action="import",
            entity_type=self.domain,
            details=details,
        ))

    async def import_data(
        self,
        rows: Iterable[dict[str, object]],
        mapping: dict[str, str] | None = None,
        formulas: dict[str, str] | None = None,
        dry_run: bool = False,
    ) -> ValidationReport:
        valid_rows, report = await self.validate_rows(rows, mapping=mapping, formulas=formulas)

        if report.errors:
            await self.db.rollback()
            await self.log_activity(f"{self.domain} import failed validation")
            await self.db.commit()
            return report

        if dry_run:
            await self.log_activity(f"{self.domain} import dry-run success: {len(valid_rows)} rows")
            await self.db.commit()
            return report

        async with self.db.begin():
            await self.bulk_insert(valid_rows)

        await self.log_activity(f"{self.domain} import committed: {len(valid_rows)} rows")
        await self.db.commit()
        return report
