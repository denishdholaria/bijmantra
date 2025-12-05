"""
Seed Bank Division - API Router
"""

from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime
import uuid

from app.core.database import get_db
from app.core.auth import get_current_user
from .models import Vault, Accession, ViabilityTest, RegenerationTask, GermplasmExchange
from .schemas import (
    VaultCreate, VaultUpdate, VaultResponse,
    AccessionCreate, AccessionUpdate, AccessionResponse, AccessionListResponse,
    ViabilityTestCreate, ViabilityTestUpdate, ViabilityTestResponse,
    RegenerationTaskCreate, RegenerationTaskResponse,
    ExchangeCreate, ExchangeResponse,
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
