from pydantic import BaseModel, Field


class ValidationMessage(BaseModel):
    row: int | None = None
    field: str | None = None
    message: str


class ValidationReport(BaseModel):
    errors: list[ValidationMessage] = Field(default_factory=list)
    warnings: list[ValidationMessage] = Field(default_factory=list)
    success_count: int = 0

    @property
    def ok(self) -> bool:
        return len(self.errors) == 0
