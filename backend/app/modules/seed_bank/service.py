"""
Seed Bank Conservation Service
"""

from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, timezone
import uuid

from app.models.germplasm import Seedlot
from .models import Vault, Accession, ViabilityTest, RegenerationTask, GermplasmExchange
from .schemas import (
    VaultCreate, AccessionCreate, AccessionUpdate,
    ViabilityTestCreate, RegenerationTaskCreate, ExchangeCreate
)

class ConservationService:
    """
    Service for managing Seed Bank conservation data.
    Handles Accessions, Vaults, Viability Tests, and Regeneration.
    """

    # ============ Vaults ============

    async def list_vaults(self, db: AsyncSession, organization_id: int) -> List[Vault]:
        """List all storage vaults"""
        result = await db.execute(
            select(Vault).where(Vault.organization_id == organization_id)
        )
        return result.scalars().all()

    async def create_vault(self, db: AsyncSession, vault_data: VaultCreate, organization_id: int) -> Vault:
        """Create a new storage vault"""
        db_vault = Vault(
            **vault_data.model_dump(),
            organization_id=organization_id,
        )
        db.add(db_vault)
        await db.commit()
        await db.refresh(db_vault)
        return db_vault

    async def get_vault(self, db: AsyncSession, vault_id: str, organization_id: int) -> Optional[Vault]:
        """Get vault details"""
        result = await db.execute(
            select(Vault).where(
                Vault.id == vault_id,
                Vault.organization_id == organization_id
            )
        )
        return result.scalar_one_or_none()

    # ============ Accessions ============

    async def list_accessions(
        self,
        db: AsyncSession,
        organization_id: int,
        page: int = 0,
        page_size: int = 20,
        search: Optional[str] = None,
        status: Optional[str] = None,
        vault_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """List accessions with filtering and pagination"""
        query = select(Accession).where(Accession.organization_id == organization_id)

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

        return {
            "data": result.scalars().all(),
            "total": total,
            "page": page,
            "page_size": page_size
        }

    async def create_accession(self, db: AsyncSession, accession: AccessionCreate, organization_id: int) -> Accession:
        """Register a new accession"""
        db_accession = Accession(
            **accession.model_dump(),
            organization_id=organization_id,
        )
        db.add(db_accession)
        await db.commit()
        await db.refresh(db_accession)
        return db_accession

    async def get_accession(self, db: AsyncSession, accession_id: str, organization_id: int) -> Optional[Accession]:
        """Get accession details"""
        result = await db.execute(
            select(Accession).where(
                Accession.id == accession_id,
                Accession.organization_id == organization_id
            )
        )
        return result.scalar_one_or_none()

    async def update_accession(
        self,
        db: AsyncSession,
        accession_id: str,
        update: AccessionUpdate,
        organization_id: int
    ) -> Optional[Accession]:
        """Update an accession"""
        accession = await self.get_accession(db, accession_id, organization_id)
        if not accession:
            return None

        for key, value in update.model_dump(exclude_unset=True).items():
            setattr(accession, key, value)

        await db.commit()
        await db.refresh(accession)
        return accession

    # ============ Viability Tests ============

    async def create_viability_test(
        self,
        db: AsyncSession,
        test: ViabilityTestCreate,
        organization_id: int
    ) -> ViabilityTest:
        """Schedule a new viability test"""
        batch_number = f"VT-{datetime.now().strftime('%Y')}-{str(uuid.uuid4())[:4].upper()}"
        db_test = ViabilityTest(
            **test.model_dump(),
            batch_number=batch_number,
            organization_id=organization_id,
        )
        db.add(db_test)
        await db.commit()
        await db.refresh(db_test)

        # Optionally update Accession viability stats if completed
        if db_test.status == "completed" and db_test.germination_rate is not None:
             accession = await self.get_accession(db, str(db_test.accession_id), organization_id)
             if accession:
                 accession.viability = db_test.germination_rate
                 db.add(accession)
                 await db.commit()

        return db_test

    # ============ Dashboard Stats ============

    async def get_stats(self, db: AsyncSession, organization_id: int) -> Dict[str, int]:
        """Get seed bank dashboard statistics"""

        # Count accessions
        accession_count = await db.execute(
            select(func.count()).where(Accession.organization_id == organization_id)
        )

        # Count vaults
        vault_count = await db.execute(
            select(func.count()).where(Vault.organization_id == organization_id)
        )

        # Pending viability tests
        pending_tests = await db.execute(
            select(func.count()).where(
                ViabilityTest.organization_id == organization_id,
                ViabilityTest.status.in_(["scheduled", "in-progress"])
            )
        )

        # Scheduled regeneration
        regen_count = await db.execute(
            select(func.count()).where(
                RegenerationTask.organization_id == organization_id,
                RegenerationTask.status.in_(["planned", "in-progress"])
            )
        )

        return {
            "total_accessions": accession_count.scalar() or 0,
            "active_vaults": vault_count.scalar() or 0,
            "pending_viability": pending_tests.scalar() or 0,
            "scheduled_regeneration": regen_count.scalar() or 0,
        }

# Singleton
_conservation_service: Optional[ConservationService] = None

def get_conservation_service() -> ConservationService:
    global _conservation_service
    if _conservation_service is None:
        _conservation_service = ConservationService()
    return _conservation_service
