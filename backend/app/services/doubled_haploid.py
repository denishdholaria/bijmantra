"""
Doubled Haploid Service
DH production and management.
Converted to use real database queries per Zero Mock Data Policy.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, date, UTC

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.doubled_haploid import DHProtocol, DHBatch


class DoubledHaploidService:
    """
    Service for doubled haploid production management.
    
    All methods are async and require AsyncSession and organization_id
    for multi-tenant isolation per GOVERNANCE.md §4.3.1.
    """

    async def _generate_protocol_code(
        self, db: AsyncSession, organization_id: int
    ) -> str:
        """Generate unique protocol code."""
        stmt = select(func.count(DHProtocol.id)).where(
            DHProtocol.organization_id == organization_id
        )
        result = await db.execute(stmt)
        count = result.scalar() or 0
        return f"DH-{count + 1:03d}"

    async def _generate_batch_code(
        self, db: AsyncSession, organization_id: int
    ) -> str:
        """Generate unique batch code."""
        stmt = select(func.count(DHBatch.id)).where(
            DHBatch.organization_id == organization_id
        )
        result = await db.execute(stmt)
        count = result.scalar() or 0
        return f"DHB-{count + 1:03d}"


    # ============ Protocol Management ============

    async def create_protocol(
        self,
        db: AsyncSession,
        organization_id: int,
        name: str,
        crop: str,
        method: str,
        inducer: Optional[str] = None,
        induction_rate: float = 0.1,
        doubling_agent: Optional[str] = None,
        doubling_rate: float = 0.25,
        days_to_complete: Optional[int] = None,
        notes: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create a new DH protocol."""
        protocol_code = await self._generate_protocol_code(db, organization_id)
        overall_efficiency = induction_rate * doubling_rate
        
        protocol = DHProtocol(
            protocol_code=protocol_code,
            name=name,
            crop=crop,
            method=method,
            inducer=inducer,
            induction_rate=induction_rate,
            doubling_agent=doubling_agent,
            doubling_rate=doubling_rate,
            overall_efficiency=overall_efficiency,
            days_to_complete=days_to_complete,
            status="active",
            notes=notes,
            organization_id=organization_id,
        )
        db.add(protocol)
        await db.commit()
        await db.refresh(protocol)
        
        return self._protocol_to_dict(protocol)

    async def get_protocols(
        self,
        db: AsyncSession,
        organization_id: int,
        crop: Optional[str] = None,
        method: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Get DH protocols with filters."""
        stmt = select(DHProtocol).where(
            DHProtocol.organization_id == organization_id
        )
        
        if crop:
            stmt = stmt.where(func.lower(DHProtocol.crop) == crop.lower())
        if method:
            stmt = stmt.where(DHProtocol.method.ilike(f"%{method}%"))
        if status:
            stmt = stmt.where(DHProtocol.status == status)
        
        stmt = stmt.order_by(DHProtocol.created_at.desc()).limit(limit)
        
        result = await db.execute(stmt)
        protocols = result.scalars().all()
        
        return [self._protocol_to_dict(p) for p in protocols]

    async def get_protocol(
        self,
        db: AsyncSession,
        organization_id: int,
        protocol_id: int,
    ) -> Optional[Dict[str, Any]]:
        """Get single protocol by ID."""
        stmt = select(DHProtocol).where(
            and_(
                DHProtocol.organization_id == organization_id,
                DHProtocol.id == protocol_id
            )
        )
        result = await db.execute(stmt)
        protocol = result.scalar_one_or_none()
        
        return self._protocol_to_dict(protocol) if protocol else None


    # ============ Batch Management ============

    async def create_batch(
        self,
        db: AsyncSession,
        organization_id: int,
        protocol_id: int,
        name: str,
        donor_cross: Optional[str] = None,
        donor_plants: int = 0,
        start_date: Optional[date] = None,
        notes: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """Create a new DH batch."""
        # Verify protocol exists and belongs to org
        protocol_stmt = select(DHProtocol).where(
            and_(
                DHProtocol.organization_id == organization_id,
                DHProtocol.id == protocol_id
            )
        )
        protocol_result = await db.execute(protocol_stmt)
        if not protocol_result.scalar_one_or_none():
            return None
        
        batch_code = await self._generate_batch_code(db, organization_id)
        
        batch = DHBatch(
            batch_code=batch_code,
            name=name,
            protocol_id=protocol_id,
            donor_cross=donor_cross,
            donor_plants=donor_plants,
            start_date=start_date or date.today(),
            stage="Initiated",
            status="active",
            notes=notes,
            organization_id=organization_id,
        )
        db.add(batch)
        await db.commit()
        await db.refresh(batch)
        
        return self._batch_to_dict(batch)

    async def get_batches(
        self,
        db: AsyncSession,
        organization_id: int,
        protocol_id: Optional[int] = None,
        status: Optional[str] = None,
        stage: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Get DH batches with filters."""
        stmt = select(DHBatch).options(
            selectinload(DHBatch.protocol)
        ).where(
            DHBatch.organization_id == organization_id
        )
        
        if protocol_id:
            stmt = stmt.where(DHBatch.protocol_id == protocol_id)
        if status:
            stmt = stmt.where(DHBatch.status == status)
        if stage:
            stmt = stmt.where(DHBatch.stage.ilike(f"%{stage}%"))
        
        stmt = stmt.order_by(DHBatch.created_at.desc()).limit(limit)
        
        result = await db.execute(stmt)
        batches = result.scalars().all()
        
        return [self._batch_to_dict(b) for b in batches]

    async def get_batch(
        self,
        db: AsyncSession,
        organization_id: int,
        batch_id: int,
    ) -> Optional[Dict[str, Any]]:
        """Get single batch by ID."""
        stmt = select(DHBatch).options(
            selectinload(DHBatch.protocol)
        ).where(
            and_(
                DHBatch.organization_id == organization_id,
                DHBatch.id == batch_id
            )
        )
        result = await db.execute(stmt)
        batch = result.scalar_one_or_none()
        
        return self._batch_to_dict(batch) if batch else None

    async def update_batch_progress(
        self,
        db: AsyncSession,
        organization_id: int,
        batch_id: int,
        **updates,
    ) -> Optional[Dict[str, Any]]:
        """Update batch progress."""
        stmt = select(DHBatch).where(
            and_(
                DHBatch.organization_id == organization_id,
                DHBatch.id == batch_id
            )
        )
        result = await db.execute(stmt)
        batch = result.scalar_one_or_none()
        
        if not batch:
            return None
        
        allowed_fields = {
            'anthers_cultured', 'embryos_formed', 'plants_regenerated',
            'haploids_induced', 'haploids_identified', 'doubled_plants',
            'fertile_dh_lines', 'stage', 'status', 'end_date', 'notes'
        }
        
        for key, value in updates.items():
            if key in allowed_fields and value is not None:
                setattr(batch, key, value)
        
        await db.commit()
        await db.refresh(batch)
        
        return self._batch_to_dict(batch)


    # ============ Calculations ============

    async def calculate_efficiency(
        self,
        db: AsyncSession,
        organization_id: int,
        protocol_id: int,
        donor_plants: int,
    ) -> Dict[str, Any]:
        """Calculate expected DH production efficiency."""
        protocol = await self.get_protocol(db, organization_id, protocol_id)
        if not protocol:
            return {"error": "Protocol not found"}
        
        method = protocol["method"].lower()
        
        if "anther" in method or "microspore" in method:
            anthers_per_plant = 100
            total_anthers = donor_plants * anthers_per_plant
            embryos = int(total_anthers * protocol["induction_rate"])
            regenerated = int(embryos * 0.70)
            doubled = int(regenerated * protocol["doubling_rate"])
        else:
            # In vivo method
            seeds_per_plant = 200
            total_seeds = donor_plants * seeds_per_plant
            haploids = int(total_seeds * protocol["induction_rate"])
            doubled = int(haploids * protocol["doubling_rate"])
            regenerated = haploids
            embryos = haploids
        
        return {
            "protocol": protocol["name"],
            "crop": protocol["crop"],
            "method": protocol["method"],
            "donor_plants": donor_plants,
            "expected_embryos": embryos,
            "expected_regenerated": regenerated,
            "expected_dh_lines": doubled,
            "overall_efficiency": protocol["overall_efficiency"],
            "days_to_complete": protocol["days_to_complete"],
            "cost_estimate": f"${donor_plants * 50}-{donor_plants * 100}",
        }

    def get_stage_workflow(self, method: str) -> List[Dict[str, Any]]:
        """Get workflow stages for a method type."""
        if "anther" in method.lower() or "microspore" in method.lower():
            return [
                {"stage": 1, "name": "Donor plant growth", "days": 60},
                {"stage": 2, "name": "Anther collection", "days": 7},
                {"stage": 3, "name": "Culture initiation", "days": 14},
                {"stage": 4, "name": "Embryo induction", "days": 30},
                {"stage": 5, "name": "Plant regeneration", "days": 45},
                {"stage": 6, "name": "Chromosome doubling", "days": 14},
                {"stage": 7, "name": "Hardening", "days": 21},
                {"stage": 8, "name": "Field transfer", "days": 7},
                {"stage": 9, "name": "Seed multiplication", "days": 90},
            ]
        else:
            return [
                {"stage": 1, "name": "Donor plant growth", "days": 60},
                {"stage": 2, "name": "Pollination with inducer", "days": 7},
                {"stage": 3, "name": "Seed harvest", "days": 45},
                {"stage": 4, "name": "Haploid identification", "days": 14},
                {"stage": 5, "name": "Chromosome doubling", "days": 14},
                {"stage": 6, "name": "D0 plant growth", "days": 60},
                {"stage": 7, "name": "Seed multiplication", "days": 90},
            ]

    async def get_statistics(
        self,
        db: AsyncSession,
        organization_id: int,
    ) -> Dict[str, Any]:
        """Get DH production statistics."""
        # Protocol counts
        protocol_stmt = select(func.count(DHProtocol.id)).where(
            DHProtocol.organization_id == organization_id
        )
        protocol_result = await db.execute(protocol_stmt)
        total_protocols = protocol_result.scalar() or 0
        
        # Batch counts by status
        active_stmt = select(func.count(DHBatch.id)).where(
            and_(
                DHBatch.organization_id == organization_id,
                DHBatch.status == "active"
            )
        )
        active_result = await db.execute(active_stmt)
        active_batches = active_result.scalar() or 0
        
        completed_stmt = select(func.count(DHBatch.id)).where(
            and_(
                DHBatch.organization_id == organization_id,
                DHBatch.status == "completed"
            )
        )
        completed_result = await db.execute(completed_stmt)
        completed_batches = completed_result.scalar() or 0
        
        # Total DH lines
        lines_stmt = select(func.sum(DHBatch.fertile_dh_lines)).where(
            DHBatch.organization_id == organization_id
        )
        lines_result = await db.execute(lines_stmt)
        total_dh_lines = lines_result.scalar() or 0
        
        # Distinct crops and methods
        crops_stmt = select(DHProtocol.crop).where(
            DHProtocol.organization_id == organization_id
        ).distinct()
        crops_result = await db.execute(crops_stmt)
        crops = [row[0] for row in crops_result.all()]
        
        methods_stmt = select(DHProtocol.method).where(
            DHProtocol.organization_id == organization_id
        ).distinct()
        methods_result = await db.execute(methods_stmt)
        methods = [row[0] for row in methods_result.all()]
        
        # Average efficiency
        eff_stmt = select(func.avg(DHProtocol.overall_efficiency)).where(
            DHProtocol.organization_id == organization_id
        )
        eff_result = await db.execute(eff_stmt)
        avg_efficiency = eff_result.scalar() or 0
        
        return {
            "total_protocols": total_protocols,
            "active_batches": active_batches,
            "completed_batches": completed_batches,
            "total_dh_lines_produced": total_dh_lines,
            "crops": crops,
            "methods": methods,
            "avg_efficiency": round(avg_efficiency, 3) if avg_efficiency else 0,
        }


    # ============ Helper Methods ============

    def _protocol_to_dict(self, protocol: DHProtocol) -> Dict[str, Any]:
        """Convert DHProtocol model to dictionary."""
        return {
            "id": str(protocol.id),
            "protocol_code": protocol.protocol_code,
            "name": protocol.name,
            "crop": protocol.crop,
            "method": protocol.method,
            "inducer": protocol.inducer,
            "induction_rate": protocol.induction_rate,
            "doubling_agent": protocol.doubling_agent,
            "doubling_rate": protocol.doubling_rate,
            "overall_efficiency": protocol.overall_efficiency,
            "days_to_complete": protocol.days_to_complete,
            "status": protocol.status,
            "notes": protocol.notes,
            "created_at": protocol.created_at.isoformat() if protocol.created_at else None,
        }

    def _batch_to_dict(self, batch: DHBatch) -> Dict[str, Any]:
        """Convert DHBatch model to dictionary."""
        return {
            "id": str(batch.id),
            "batch_code": batch.batch_code,
            "name": batch.name,
            "protocol_id": str(batch.protocol_id),
            "protocol_name": batch.protocol.name if batch.protocol else None,
            "donor_cross": batch.donor_cross,
            "donor_plants": batch.donor_plants,
            "anthers_cultured": batch.anthers_cultured,
            "embryos_formed": batch.embryos_formed,
            "plants_regenerated": batch.plants_regenerated,
            "haploids_induced": batch.haploids_induced,
            "haploids_identified": batch.haploids_identified,
            "doubled_plants": batch.doubled_plants,
            "fertile_dh_lines": batch.fertile_dh_lines,
            "stage": batch.stage,
            "start_date": batch.start_date.isoformat() if batch.start_date else None,
            "end_date": batch.end_date.isoformat() if batch.end_date else None,
            "status": batch.status,
            "notes": batch.notes,
            "created_at": batch.created_at.isoformat() if batch.created_at else None,
        }


# Singleton instance
doubled_haploid_service = DoubledHaploidService()


def get_doubled_haploid_service() -> DoubledHaploidService:
    return doubled_haploid_service
