"""
Seed Bank Division - API Router
"""

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.middleware.tenant_context import get_tenant_db

from .models import GermplasmExchange, RegenerationTask, ViabilityTest
from .schemas import (
    AccessionCreate,
    AccessionListResponse,
    AccessionResponse,
    AccessionUpdate,
    ExchangeCreate,
    ExchangeResponse,
    RegenerationTaskCreate,
    RegenerationTaskResponse,
    VaultCreate,
    VaultResponse,
    ViabilityTestCreate,
    ViabilityTestResponse,
)
from .service import get_conservation_service


router = APIRouter(prefix="/seed-bank", tags=["Seed Bank"])


# ============ Vaults ============

@router.get("/vaults", response_model=list[VaultResponse])
async def list_vaults(
    db: AsyncSession = Depends(get_tenant_db),
    current_user = Depends(get_current_user),
):
    """List all storage vaults"""
    service = get_conservation_service()
    return await service.list_vaults(db, current_user.organization_id)


@router.post("/vaults", response_model=VaultResponse)
async def create_vault(
    vault: VaultCreate,
    db: AsyncSession = Depends(get_tenant_db),
    current_user = Depends(get_current_user),
):
    """Create a new storage vault"""
    service = get_conservation_service()
    return await service.create_vault(db, vault, current_user.organization_id)


@router.get("/vaults/{vault_id}", response_model=VaultResponse)
async def get_vault(
    vault_id: str,
    db: AsyncSession = Depends(get_tenant_db),
    current_user = Depends(get_current_user),
):
    """Get vault details"""
    service = get_conservation_service()
    vault = await service.get_vault(db, vault_id, current_user.organization_id)
    if not vault:
        raise HTTPException(status_code=404, detail="Vault not found")
    return vault


# ============ Accessions ============

@router.get("/accessions", response_model=AccessionListResponse)
async def list_accessions(
    page: int = Query(0, ge=0),
    page_size: int = Query(20, ge=1, le=100),
    search: str | None = None,
    status: str | None = None,
    vault_id: str | None = None,
    db: AsyncSession = Depends(get_tenant_db),
    current_user = Depends(get_current_user),
):
    """List accessions with filtering and pagination"""
    service = get_conservation_service()
    result = await service.list_accessions(
        db=db,
        organization_id=current_user.organization_id,
        page=page,
        page_size=page_size,
        search=search,
        status=status,
        vault_id=vault_id
    )

    return AccessionListResponse(
        data=result["data"],
        total=result["total"],
        page=result["page"],
        page_size=result["page_size"],
    )


@router.post("/accessions", response_model=AccessionResponse)
async def create_accession(
    accession: AccessionCreate,
    db: AsyncSession = Depends(get_tenant_db),
    current_user = Depends(get_current_user),
):
    """Register a new accession"""
    service = get_conservation_service()
    return await service.create_accession(db, accession, current_user.organization_id)


@router.get("/accessions/{accession_id}", response_model=AccessionResponse)
async def get_accession(
    accession_id: str,
    db: AsyncSession = Depends(get_tenant_db),
    current_user = Depends(get_current_user),
):
    """Get accession details"""
    service = get_conservation_service()
    accession = await service.get_accession(db, accession_id, current_user.organization_id)
    if not accession:
        raise HTTPException(status_code=404, detail="Accession not found")
    return accession


@router.patch("/accessions/{accession_id}", response_model=AccessionResponse)
async def update_accession(
    accession_id: str,
    update: AccessionUpdate,
    db: AsyncSession = Depends(get_tenant_db),
    current_user = Depends(get_current_user),
):
    """Update an accession"""
    service = get_conservation_service()
    accession = await service.update_accession(db, accession_id, update, current_user.organization_id)
    if not accession:
        raise HTTPException(status_code=404, detail="Accession not found")
    return accession


# ============ Viability Tests ============

@router.get("/viability-tests", response_model=list[ViabilityTestResponse])
async def list_viability_tests(
    status: str | None = None,
    accession_id: str | None = None,
    db: AsyncSession = Depends(get_tenant_db),
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
    db: AsyncSession = Depends(get_tenant_db),
    current_user = Depends(get_current_user),
):
    """Schedule a new viability test"""
    batch_number = f"VT-{datetime.now().strftime('%Y')}-{str(uuid.uuid4())[:4].upper()}"
    test_date = test.test_date
    if test_date.tzinfo is not None:
        test_date = test_date.replace(tzinfo=None)

    db_test = ViabilityTest(
        **test.model_dump(exclude={"test_date"}),
        test_date=test_date,
        batch_number=batch_number,
        organization_id=current_user.organization_id,
    )
    db.add(db_test)
    await db.commit()
    await db.refresh(db_test)
    return db_test


# ============ Regeneration Tasks ============

@router.get("/regeneration-tasks", response_model=list[RegenerationTaskResponse])
async def list_regeneration_tasks(
    priority: str | None = None,
    status: str | None = None,
    db: AsyncSession = Depends(get_tenant_db),
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
    db: AsyncSession = Depends(get_tenant_db),
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

@router.get("/exchanges", response_model=list[ExchangeResponse])
async def list_exchanges(
    type: str | None = None,
    status: str | None = None,
    db: AsyncSession = Depends(get_tenant_db),
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
    db: AsyncSession = Depends(get_tenant_db),
    current_user = Depends(get_current_user),
):
    """Create a new germplasm exchange request"""
    request_number = f"EX-{datetime.now().strftime('%Y')}-{str(uuid.uuid4())[:4].upper()}"
    db_exchange = GermplasmExchange(
        **exchange.model_dump(),
        request_number=request_number,
        request_date=datetime.utcnow(),
        organization_id=current_user.organization_id,
    )
    db.add(db_exchange)
    await db.commit()
    await db.refresh(db_exchange)
    return db_exchange


# ============ Dashboard Stats ============

@router.get("/stats")
async def get_seed_bank_stats(
    db: AsyncSession = Depends(get_tenant_db),
    current_user = Depends(get_current_user),
):
    """Get seed bank dashboard statistics"""
    service = get_conservation_service()
    return await service.get_stats(db, current_user.organization_id)
