"""FastAPI adapter for MCPD accession passport routes."""

from __future__ import annotations

import io
from datetime import datetime

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.domains.germplasm.capabilities.accession_passport.adapters import (
    SqlAlchemyMCPDExportAdapter,
    SqlAlchemyMCPDImportAdapter,
)
from app.domains.germplasm.capabilities.accession_passport.adapters.api.access import (
    require_accession_passport_api_access,
)
from app.domains.germplasm.capabilities.accession_passport.adapters.api.audit import (
    write_mcpd_audit_event,
)
from app.domains.germplasm.capabilities.accession_passport.application import (
    EmptyMCPDImportError,
    MCPDImportParseError,
    export_to_mcpd_csv,
    export_to_mcpd_json,
    get_mcpd_reference_service,
    import_mcpd_accessions,
)
from app.domains.germplasm.capabilities.accession_passport.domain import (
    MCPD_EXPORTED,
    MCPD_IMPORTED,
)
from app.domains.germplasm.capabilities.accession_passport.schemas import MCPDImportResult
from app.middleware.tenant_context import get_tenant_db


router = APIRouter(prefix="/mcpd", tags=["Seed Bank MCPD"])


@router.get("/export/csv")
async def export_accessions_mcpd_csv(
    inst_code: str = Query("BIJ001", description="FAO WIEWS institute code"),
    db: AsyncSession = Depends(get_tenant_db),
    current_user=Depends(get_current_user),
):
    """
    Export all accessions in MCPD v2.1 CSV format.

    This format is compatible with:
    - GENESYS global portal
    - GRIN-Global
    - FAO WIEWS
    - Other genebank systems
    """
    await require_accession_passport_api_access(
        current_user,
        db=db,
        required_permission="germplasm.read",
    )
    export_adapter = SqlAlchemyMCPDExportAdapter(db)
    accessions = await export_adapter.list_export_records(
        current_user.organization_id
    )

    csv_content = export_to_mcpd_csv(accessions, inst_code)
    filename = f"mcpd_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    await write_mcpd_audit_event(
        db,
        organization_id=current_user.organization_id,
        actor_user_id=getattr(current_user, "id", None),
        action=MCPD_EXPORTED,
        method="GET",
        changes={
            "mcpdVersion": "2.1",
            "format": "csv",
            "instituteCode": inst_code,
            "totalRecords": len(accessions),
        },
    )

    return StreamingResponse(
        io.StringIO(csv_content),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/export/json")
async def export_accessions_mcpd_json(
    inst_code: str = Query("BIJ001", description="FAO WIEWS institute code"),
    db: AsyncSession = Depends(get_tenant_db),
    current_user=Depends(get_current_user),
):
    """
    Export all accessions in MCPD v2.1 JSON format.

    Useful for API-based data exchange with other systems.
    """
    await require_accession_passport_api_access(
        current_user,
        db=db,
        required_permission="germplasm.read",
    )
    export_adapter = SqlAlchemyMCPDExportAdapter(db)
    accessions = await export_adapter.list_export_records(
        current_user.organization_id
    )

    response = {
        "mcpd_version": "2.1",
        "institute_code": inst_code,
        "export_date": datetime.now().isoformat(),
        "total_records": len(accessions),
        "data": export_to_mcpd_json(accessions, inst_code),
    }

    await write_mcpd_audit_event(
        db,
        organization_id=current_user.organization_id,
        actor_user_id=getattr(current_user, "id", None),
        action=MCPD_EXPORTED,
        method="GET",
        changes={
            "mcpdVersion": "2.1",
            "format": "json",
            "instituteCode": inst_code,
            "totalRecords": len(accessions),
        },
    )

    return response


@router.post("/import", response_model=MCPDImportResult)
async def import_accessions_mcpd(
    file: UploadFile = File(..., description="MCPD CSV file"),
    skip_duplicates: bool = Query(True, description="Skip records with existing accession numbers"),
    validate_only: bool = Query(False, description="Only validate, don't import"),
    db: AsyncSession = Depends(get_tenant_db),
    current_user=Depends(get_current_user),
):
    """
    Import accessions from MCPD v2.1 CSV file.

    Supports files exported from:
    - GENESYS
    - GRIN-Global
    - Other MCPD-compliant systems

    Set `validate_only=true` to check the file without importing.
    """
    await require_accession_passport_api_access(
        current_user,
        db=db,
        required_permission="germplasm.passport.manage",
    )

    content = await file.read()
    try:
        csv_content = content.decode("utf-8")
    except UnicodeDecodeError:
        csv_content = content.decode("latin-1")

    import_adapter = SqlAlchemyMCPDImportAdapter(db)

    try:
        import_result = await import_mcpd_accessions(
            csv_content,
            repository=import_adapter,
            organization_id=current_user.organization_id,
            skip_duplicates=skip_duplicates,
            validate_only=validate_only,
        )
    except MCPDImportParseError as exc:
        raise HTTPException(status_code=400, detail=f"Failed to parse CSV: {str(exc)}") from exc
    except EmptyMCPDImportError as exc:
        raise HTTPException(status_code=400, detail="No records found in CSV file") from exc

    response = MCPDImportResult(
        total_records=import_result.total_records,
        imported=import_result.imported,
        skipped=import_result.skipped,
        errors=list(import_result.errors),
    )
    await write_mcpd_audit_event(
        db,
        organization_id=current_user.organization_id,
        actor_user_id=getattr(current_user, "id", None),
        action=MCPD_IMPORTED,
        method="POST",
        changes={
            "mcpdVersion": "2.1",
            "validateOnly": validate_only,
            "skipDuplicates": skip_duplicates,
            "totalRecords": import_result.total_records,
            "imported": import_result.imported,
            "skipped": import_result.skipped,
            "errorCount": len(import_result.errors),
        },
    )

    return response


@router.get("/template")
async def get_mcpd_template(
    db: AsyncSession = Depends(get_tenant_db),
    current_user=Depends(get_current_user),
):
    """
    Download an empty MCPD v2.1 CSV template with all fields.

    Use this template to prepare data for import.
    """
    await require_accession_passport_api_access(
        current_user,
        db=db,
        required_permission="germplasm.read",
    )
    template_csv = get_mcpd_reference_service().template_csv()

    return StreamingResponse(
        io.StringIO(template_csv),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=mcpd_template.csv"},
    )


@router.get("/codes/biological-status")
async def get_mcpd_biological_status_codes(
    db: AsyncSession = Depends(get_tenant_db),
    current_user=Depends(get_current_user),
):
    """Get MCPD biological status codes (SAMPSTAT)."""
    await require_accession_passport_api_access(
        current_user,
        db=db,
        required_permission="germplasm.read",
    )
    return get_mcpd_reference_service().biological_status_codes()


@router.get("/codes/acquisition-source")
async def get_mcpd_acquisition_source_codes(
    db: AsyncSession = Depends(get_tenant_db),
    current_user=Depends(get_current_user),
):
    """Get MCPD acquisition source codes (COLLSRC)."""
    await require_accession_passport_api_access(
        current_user,
        db=db,
        required_permission="germplasm.read",
    )
    return get_mcpd_reference_service().acquisition_source_codes()


@router.get("/codes/storage-type")
async def get_mcpd_storage_type_codes(
    db: AsyncSession = Depends(get_tenant_db),
    current_user=Depends(get_current_user),
):
    """Get MCPD storage type codes (STORAGE)."""
    await require_accession_passport_api_access(
        current_user,
        db=db,
        required_permission="germplasm.read",
    )
    return get_mcpd_reference_service().storage_type_codes()


@router.get("/codes/countries")
async def get_mcpd_country_codes(
    db: AsyncSession = Depends(get_tenant_db),
    current_user=Depends(get_current_user),
):
    """Get ISO 3166-1 alpha-3 country codes for MCPD."""
    await require_accession_passport_api_access(
        current_user,
        db=db,
        required_permission="germplasm.read",
    )
    return get_mcpd_reference_service().country_codes()
