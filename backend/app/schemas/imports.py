from pydantic import BaseModel, Field

from app.services.import_engine.schemas import ValidationReport


class ImportUploadResponse(BaseModel):
    job_id: int
    status: str
    mapping_suggestions: dict[str, str] = Field(default_factory=dict)


class ImportJobResponse(BaseModel):
    id: int
    import_type: str
    file_name: str
    status: str
    dry_run: bool
    total_rows: int
    success_count: int
    error_count: int


class ImportExecuteOptions(BaseModel):
    import_type: str
    mapping: dict[str, str] = Field(default_factory=dict)
    formulas: dict[str, str] = Field(default_factory=dict)
    dry_run: bool = False


class ImportExecutionResult(BaseModel):
    report: ValidationReport
    inserted: int
