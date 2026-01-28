"""
Seed Bank Division - API Router
"""

from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, timezone
import uuid
import io

from app.core.database import get_db
from app.api.deps import get_current_user
from .models import Vault, Accession, ViabilityTest, RegenerationTask, GermplasmExchange
from .schemas import (
    VaultCreate, VaultUpdate, VaultResponse,
    AccessionCreate, AccessionUpdate, AccessionResponse, AccessionListResponse,
    ViabilityTestCreate, ViabilityTestUpdate, ViabilityTestResponse,
    RegenerationTaskCreate, RegenerationTaskResponse,
    ExchangeCreate, ExchangeResponse,
)
from .mcpd import (
    export_to_mcpd_csv, export_to_mcpd_json,
    parse_mcpd_csv, mcpd_to_accession_data, validate_mcpd_record,
    get_biological_status_codes, get_acquisition_source_codes,
    get_storage_type_codes, get_country_codes,
    MCPDImportResult, BIOLOGICAL_STATUS_CODES, COUNTRY_CODES,
)

router = APIRouter(prefix="/seed-bank", tags=["Seed Bank"])


# ============ Vaults ============

@router.get("/vaults", response_model=List[VaultResponse])
async def list_vaults(
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """List all storage vaults"""
    result = await db.execute(
        select(Vault).where(Vault.organization_id == current_user.organization_id)
    )
    return result.scalars().all()


@router.post("/vaults", response_model=VaultResponse)
async def create_vault(
    vault: VaultCreate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """Create a new storage vault"""
    db_vault = Vault(
        **vault.model_dump(),
        organization_id=current_user.organization_id,
    )
    db.add(db_vault)
    await db.commit()
    await db.refresh(db_vault)
    return db_vault


@router.get("/vaults/{vault_id}", response_model=VaultResponse)
async def get_vault(
    vault_id: str,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """Get vault details"""
    result = await db.execute(
        select(Vault).where(
            Vault.id == vault_id,
            Vault.organization_id == current_user.organization_id
        )
    )
    vault = result.scalar_one_or_none()
    if not vault:
        raise HTTPException(status_code=404, detail="Vault not found")
    return vault


# ============ Accessions ============

@router.get("/accessions", response_model=AccessionListResponse)
async def list_accessions(
    page: int = Query(0, ge=0),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    status: Optional[str] = None,
    vault_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """List accessions with filtering and pagination"""
    query = select(Accession).where(Accession.organization_id == current_user.organization_id)
    
    if search:
        query = query.where(
            (Accession.accession_number.ilike(f"%{search}%")) |
            (Accession.genus.ilike(f"%{search}%")) |
            (Accession.species.ilike(f"%{search}%")) |
            (Accession.common_name.ilike(f"%{search}%"))
        )
    if status:
        query = query.where(Accession.status == status)
    if vault_id:
        query = query.where(Accession.vault_id == vault_id)
    
    # Count total
    count_result = await db.execute(select(func.count()).select_from(query.subquery()))
    total = count_result.scalar()
    
    # Paginate
    query = query.offset(page * page_size).limit(page_size)
    result = await db.execute(query)
    
    return AccessionListResponse(
        data=result.scalars().all(),
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("/accessions", response_model=AccessionResponse)
async def create_accession(
    accession: AccessionCreate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """Register a new accession"""
    db_accession = Accession(
        **accession.model_dump(),
        organization_id=current_user.organization_id,
    )
    db.add(db_accession)
    await db.commit()
    await db.refresh(db_accession)
    return db_accession


@router.get("/accessions/{accession_id}", response_model=AccessionResponse)
async def get_accession(
    accession_id: str,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """Get accession details"""
    result = await db.execute(
        select(Accession).where(
            Accession.id == accession_id,
            Accession.organization_id == current_user.organization_id
        )
    )
    accession = result.scalar_one_or_none()
    if not accession:
        raise HTTPException(status_code=404, detail="Accession not found")
    return accession


@router.patch("/accessions/{accession_id}", response_model=AccessionResponse)
async def update_accession(
    accession_id: str,
    update: AccessionUpdate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """Update an accession"""
    result = await db.execute(
        select(Accession).where(
            Accession.id == accession_id,
            Accession.organization_id == current_user.organization_id
        )
    )
    accession = result.scalar_one_or_none()
    if not accession:
        raise HTTPException(status_code=404, detail="Accession not found")
    
    for key, value in update.model_dump(exclude_unset=True).items():
        setattr(accession, key, value)
    
    await db.commit()
    await db.refresh(accession)
    return accession


# ============ Viability Tests ============

@router.get("/viability-tests", response_model=List[ViabilityTestResponse])
async def list_viability_tests(
    status: Optional[str] = None,
    accession_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """List viability tests"""
    query = select(ViabilityTest).where(ViabilityTest.organization_id == current_user.organization_id)
    if status:
        query = query.where(ViabilityTest.status == status)
    if accession_id:
        query = query.where(ViabilityTest.accession_id == accession_id)
    
    result = await db.execute(query.order_by(ViabilityTest.test_date.desc()))
    return result.scalars().all()


@router.post("/viability-tests", response_model=ViabilityTestResponse)
async def create_viability_test(
    test: ViabilityTestCreate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """Schedule a new viability test"""
    batch_number = f"VT-{datetime.now().strftime('%Y')}-{str(uuid.uuid4())[:4].upper()}"
    db_test = ViabilityTest(
        **test.model_dump(),
        batch_number=batch_number,
        organization_id=current_user.organization_id,
    )
    db.add(db_test)
    await db.commit()
    await db.refresh(db_test)
    return db_test


# ============ Regeneration Tasks ============

@router.get("/regeneration-tasks", response_model=List[RegenerationTaskResponse])
async def list_regeneration_tasks(
    priority: Optional[str] = None,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """List regeneration tasks"""
    query = select(RegenerationTask).where(RegenerationTask.organization_id == current_user.organization_id)
    if priority:
        query = query.where(RegenerationTask.priority == priority)
    if status:
        query = query.where(RegenerationTask.status == status)
    
    result = await db.execute(query)
    return result.scalars().all()


@router.post("/regeneration-tasks", response_model=RegenerationTaskResponse)
async def create_regeneration_task(
    task: RegenerationTaskCreate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """Plan a new regeneration task"""
    db_task = RegenerationTask(
        **task.model_dump(),
        organization_id=current_user.organization_id,
    )
    db.add(db_task)
    await db.commit()
    await db.refresh(db_task)
    return db_task


# ============ Germplasm Exchange ============

@router.get("/exchanges", response_model=List[ExchangeResponse])
async def list_exchanges(
    type: Optional[str] = None,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """List germplasm exchanges"""
    query = select(GermplasmExchange).where(GermplasmExchange.organization_id == current_user.organization_id)
    if type:
        query = query.where(GermplasmExchange.type == type)
    if status:
        query = query.where(GermplasmExchange.status == status)
    
    result = await db.execute(query.order_by(GermplasmExchange.request_date.desc()))
    return result.scalars().all()


@router.post("/exchanges", response_model=ExchangeResponse)
async def create_exchange(
    exchange: ExchangeCreate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """Create a new germplasm exchange request"""
    request_number = f"EX-{datetime.now().strftime('%Y')}-{str(uuid.uuid4())[:4].upper()}"
    db_exchange = GermplasmExchange(
        **exchange.model_dump(),
        request_number=request_number,
        request_date=datetime.now(timezone.utc),
        organization_id=current_user.organization_id,
    )
    db.add(db_exchange)
    await db.commit()
    await db.refresh(db_exchange)
    return db_exchange


# ============ Dashboard Stats ============

@router.get("/stats")
async def get_seed_bank_stats(
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """Get seed bank dashboard statistics"""
    org_id = current_user.organization_id
    
    # Count accessions
    accession_count = await db.execute(
        select(func.count()).where(Accession.organization_id == org_id)
    )
    
    # Count vaults
    vault_count = await db.execute(
        select(func.count()).where(Vault.organization_id == org_id)
    )
    
    # Pending viability tests
    pending_tests = await db.execute(
        select(func.count()).where(
            ViabilityTest.organization_id == org_id,
            ViabilityTest.status.in_(["scheduled", "in-progress"])
        )
    )
    
    # Scheduled regeneration
    regen_count = await db.execute(
        select(func.count()).where(
            RegenerationTask.organization_id == org_id,
            RegenerationTask.status.in_(["planned", "in-progress"])
        )
    )
    
    return {
        "total_accessions": accession_count.scalar() or 0,
        "active_vaults": vault_count.scalar() or 0,
        "pending_viability": pending_tests.scalar() or 0,
        "scheduled_regeneration": regen_count.scalar() or 0,
    }


# ============ MCPD Import/Export ============

@router.get("/mcpd/export/csv")
async def export_accessions_mcpd_csv(
    inst_code: str = Query("BIJ001", description="FAO WIEWS institute code"),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """
    Export all accessions in MCPD v2.1 CSV format.
    
    This format is compatible with:
    - GENESYS global portal
    - GRIN-Global
    - FAO WIEWS
    - Other genebank systems
    """
    result = await db.execute(
        select(Accession)
        .where(Accession.organization_id == current_user.organization_id)
        .options()  # Add eager loading if needed
    )
    accessions = result.scalars().all()
    
    csv_content = export_to_mcpd_csv(accessions, inst_code)
    
    filename = f"mcpd_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    
    return StreamingResponse(
        io.StringIO(csv_content),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/mcpd/export/json")
async def export_accessions_mcpd_json(
    inst_code: str = Query("BIJ001", description="FAO WIEWS institute code"),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """
    Export all accessions in MCPD v2.1 JSON format.
    
    Useful for API-based data exchange with other systems.
    """
    result = await db.execute(
        select(Accession)
        .where(Accession.organization_id == current_user.organization_id)
    )
    accessions = result.scalars().all()
    
    return {
        "mcpd_version": "2.1",
        "institute_code": inst_code,
        "export_date": datetime.now().isoformat(),
        "total_records": len(accessions),
        "data": export_to_mcpd_json(accessions, inst_code),
    }


@router.post("/mcpd/import", response_model=MCPDImportResult)
async def import_accessions_mcpd(
    file: UploadFile = File(..., description="MCPD CSV file"),
    skip_duplicates: bool = Query(True, description="Skip records with existing accession numbers"),
    validate_only: bool = Query(False, description="Only validate, don't import"),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """
    Import accessions from MCPD v2.1 CSV file.
    
    Supports files exported from:
    - GENESYS
    - GRIN-Global
    - Other MCPD-compliant systems
    
    Set `validate_only=true` to check the file without importing.
    """
    # Read file content
    content = await file.read()
    try:
        csv_content = content.decode("utf-8")
    except UnicodeDecodeError:
        csv_content = content.decode("latin-1")
    
    # Parse CSV
    try:
        records = parse_mcpd_csv(csv_content)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse CSV: {str(e)}")
    
    if not records:
        raise HTTPException(status_code=400, detail="No records found in CSV file")
    
    # Get existing accession numbers
    existing_result = await db.execute(
        select(Accession.accession_number)
        .where(Accession.organization_id == current_user.organization_id)
    )
    existing_numbers = {r[0] for r in existing_result.fetchall()}
    
    imported = 0
    skipped = 0
    errors = []
    
    for i, row in enumerate(records, start=2):  # Start at 2 (header is row 1)
        # Validate record
        validation_errors = validate_mcpd_record(row)
        if validation_errors:
            errors.append({
                "row": i,
                "accession_number": row.get("ACCENUMB"),
                "errors": validation_errors,
            })
            continue
        
        accession_number = row.get("ACCENUMB")
        
        # Check for duplicates
        if accession_number in existing_numbers:
            if skip_duplicates:
                skipped += 1
                continue
            else:
                errors.append({
                    "row": i,
                    "accession_number": accession_number,
                    "errors": ["Accession number already exists"],
                })
                continue
        
        if validate_only:
            imported += 1
            continue
        
        # Convert to accession data
        accession_data = mcpd_to_accession_data(row)
        
        # Remove internal metadata fields
        accession_data = {k: v for k, v in accession_data.items() if not k.startswith("_")}
        
        # Create accession
        try:
            db_accession = Accession(
                **accession_data,
                organization_id=current_user.organization_id,
            )
            db.add(db_accession)
            imported += 1
            existing_numbers.add(accession_number)  # Track for duplicates in same file
        except Exception as e:
            errors.append({
                "row": i,
                "accession_number": accession_number,
                "errors": [str(e)],
            })
    
    if not validate_only and imported > 0:
        await db.commit()
    
    return MCPDImportResult(
        total_records=len(records),
        imported=imported,
        skipped=skipped,
        errors=errors,
    )


@router.get("/mcpd/template")
async def get_mcpd_template():
    """
    Download an empty MCPD v2.1 CSV template with all fields.
    
    Use this template to prepare data for import.
    """
    fieldnames = [
        "PUID", "INSTCODE", "ACCENUMB", "COLLNUMB", "OTHERNUMB",
        "COLLCODE", "COLLNAME", "COLLINSTADDRESS", "COLLMISSID", "COLLDATE",
        "GENUS", "SPECIES", "SPAUTHOR", "SUBTAXA", "SUBTAUTHOR", "CROPNAME",
        "ACCENAME", "ACQDATE", "ORIGCTY",
        "COLLSITE", "LATITUDE", "LONGITUDE", "COORDUNCERT", "COORDDATUM", "GEOREFMETH", "ELEVATION",
        "BREDCODE", "BREDNAME", "ANCEST",
        "DONORCODE", "DONORNAME", "DONORNUMB",
        "SAMPSTAT", "COLLSRC",
        "DUPLSITE", "DUPLINSTNAME",
        "STORAGE", "MLSSTAT",
        "REMARKS", "ACCEURL", "MCPDVERSION",
    ]
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(fieldnames)
    # Add example row
    writer.writerow([
        "", "BIJ001", "ACC-001", "", "",
        "", "", "", "", "20240115",
        "Oryza", "sativa", "L.", "indica", "", "Rice",
        "IR64", "20240101", "IND",
        "Punjab, India", "30.7333", "76.7794", "", "WGS84", "GPS", "250",
        "", "", "IR8/TKM6",
        "", "IRRI", "",
        "500", "40",
        "", "",
        "13", "1",
        "Example accession", "", "2.1",
    ])
    
    return StreamingResponse(
        io.StringIO(output.getvalue()),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=mcpd_template.csv"}
    )


# ============ MCPD Reference Data ============

@router.get("/mcpd/codes/biological-status")
async def get_mcpd_biological_status_codes():
    """Get MCPD biological status codes (SAMPSTAT)"""
    return {
        "field": "SAMPSTAT",
        "description": "Biological status of accession",
        "codes": [
            {"code": code, "description": desc}
            for code, desc in BIOLOGICAL_STATUS_CODES.items()
        ],
    }


@router.get("/mcpd/codes/acquisition-source")
async def get_mcpd_acquisition_source_codes():
    """Get MCPD acquisition source codes (COLLSRC)"""
    return {
        "field": "COLLSRC",
        "description": "Collecting/acquisition source",
        "codes": [
            {"code": code, "description": desc}
            for code, desc in get_acquisition_source_codes().items()
        ],
    }


@router.get("/mcpd/codes/storage-type")
async def get_mcpd_storage_type_codes():
    """Get MCPD storage type codes (STORAGE)"""
    return {
        "field": "STORAGE",
        "description": "Type of germplasm storage",
        "codes": [
            {"code": code, "description": desc}
            for code, desc in get_storage_type_codes().items()
        ],
    }


@router.get("/mcpd/codes/countries")
async def get_mcpd_country_codes():
    """Get ISO 3166-1 alpha-3 country codes for MCPD"""
    return {
        "field": "ORIGCTY",
        "description": "Country of origin (ISO 3166-1 alpha-3)",
        "codes": [
            {"code": code, "name": name}
            for code, name in sorted(COUNTRY_CODES.items(), key=lambda x: x[1])
        ],
    }
