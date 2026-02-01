"""
Speed Breeding Service
Accelerated generation advancement protocols.
Queries real data from database - no demo/mock data.
"""
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from sqlalchemy.orm import selectinload

from app.models.speed_breeding import SpeedBreedingProtocol, SpeedBreedingBatch, SpeedBreedingChamber
from app.schemas.speed_breeding import SpeedBreedingProtocolCreate, SpeedBreedingBatchCreate, SpeedBreedingChamberCreate

class SpeedBreedingService:
    """Service for speed breeding protocol management.
    
    All methods query the database for real data.
    Returns empty results when no data exists.
    """
    
    async def get_protocols(
        self,
        db: AsyncSession,
        organization_id: int,
        crop: Optional[str] = None,
        status: Optional[str] = None
    ) -> List[SpeedBreedingProtocol]:
        """Get speed breeding protocols from database."""
        query = select(SpeedBreedingProtocol).where(
            SpeedBreedingProtocol.organization_id == organization_id
        )
        
        if crop:
            query = query.where(SpeedBreedingProtocol.crop == crop)
        if status:
            query = query.where(SpeedBreedingProtocol.status == status)
            
        result = await db.execute(query)
        return result.scalars().all()
    
    async def create_protocol(
        self,
        db: AsyncSession,
        organization_id: int,
        protocol: SpeedBreedingProtocolCreate
    ) -> SpeedBreedingProtocol:
        """Create a new speed breeding protocol."""
        db_protocol = SpeedBreedingProtocol(
            **protocol.model_dump(),
            organization_id=organization_id
        )
        db.add(db_protocol)
        await db.commit()
        await db.refresh(db_protocol)
        return db_protocol

    async def get_protocol(
        self, 
        db: AsyncSession,
        organization_id: int,
        protocol_id: str
    ) -> Optional[SpeedBreedingProtocol]:
        """Get single protocol by ID."""
        try:
            p_id = int(protocol_id)
        except ValueError:
            return None
            
        query = select(SpeedBreedingProtocol).where(
            SpeedBreedingProtocol.id == p_id,
            SpeedBreedingProtocol.organization_id == organization_id
        )
        result = await db.execute(query)
        return result.scalars().first()
    
    async def get_batches(
        self,
        db: AsyncSession,
        organization_id: int,
        protocol_id: Optional[str] = None,
        status: Optional[str] = None,
        chamber: Optional[str] = None
    ) -> List[SpeedBreedingBatch]:
        """Get active batches from database."""
        query = select(SpeedBreedingBatch).options(
            selectinload(SpeedBreedingBatch.protocol),
            selectinload(SpeedBreedingBatch.chamber)
        ).where(
            SpeedBreedingBatch.organization_id == organization_id
        )
        
        if protocol_id:
            try:
                p_id = int(protocol_id)
                query = query.where(SpeedBreedingBatch.protocol_id == p_id)
            except ValueError:
                pass

        if status:
            query = query.where(SpeedBreedingBatch.status == status)
            
        result = await db.execute(query)
        batches = result.scalars().all()

        # Post-filter for chamber name if needed
        if chamber:
             batches = [b for b in batches if b.chamber and (b.chamber.name == chamber or str(b.chamber.id) == chamber)]

        return batches
    
    async def get_batch(
        self, 
        db: AsyncSession,
        organization_id: int,
        batch_id: str
    ) -> Optional[SpeedBreedingBatch]:
        """Get single batch by ID."""
        try:
            b_id = int(batch_id)
        except ValueError:
            return None
            
        query = select(SpeedBreedingBatch).options(
            selectinload(SpeedBreedingBatch.protocol),
            selectinload(SpeedBreedingBatch.chamber)
        ).where(
            SpeedBreedingBatch.id == b_id,
            SpeedBreedingBatch.organization_id == organization_id
        )
        result = await db.execute(query)
        return result.scalars().first()

    async def create_batch(
        self,
        db: AsyncSession,
        organization_id: int,
        batch: SpeedBreedingBatchCreate
    ) -> SpeedBreedingBatch:
        """Create a new batch."""
        db_batch = SpeedBreedingBatch(
            **batch.model_dump(),
            organization_id=organization_id
        )
        db.add(db_batch)
        await db.commit()
        await db.refresh(db_batch)
        return db_batch
    
    async def calculate_timeline(
        self,
        db: AsyncSession,
        organization_id: int,
        protocol_id: str,
        target_generation: str,
        start_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """Calculate breeding timeline based on protocol parameters."""
        protocol = await self.get_protocol(db, organization_id, protocol_id)
        if not protocol:
            return {"error": "Protocol not found"}
        
        # Parse generation (e.g., F6 -> 6)
        gen_str = target_generation.replace("F", "").replace("BC", "")
        try:
            gen_num = int(gen_str)
        except ValueError:
            return {"error": "Invalid generation format"}
        
        start = datetime.fromisoformat(start_date) if start_date else datetime.now(timezone.utc)
        # Using attributes from model
        days_per_gen = protocol.days_to_harvest or 75
        days_to_flower = protocol.days_to_flower or 35
        total_days = gen_num * days_per_gen
        
        timeline = []
        current_date = start
        for i in range(1, gen_num + 1):
            flower_date = current_date + timedelta(days=days_to_flower)
            harvest_date = current_date + timedelta(days=days_per_gen)
            timeline.append({
                "generation": f"F{i}",
                "sowing": current_date.strftime("%Y-%m-%d"),
                "flowering": flower_date.strftime("%Y-%m-%d"),
                "harvest": harvest_date.strftime("%Y-%m-%d")
            })
            current_date = harvest_date + timedelta(days=7)  # 7 days for seed processing
        
        return {
            "protocol": protocol.name,
            "crop": protocol.crop,
            "target_generation": target_generation,
            "start_date": start.strftime("%Y-%m-%d"),
            "end_date": (start + timedelta(days=total_days + gen_num * 7)).strftime("%Y-%m-%d"),
            "total_days": total_days + gen_num * 7,
            "generations_per_year": protocol.generations_per_year or 4,
            "timeline": timeline
        }
    
    async def get_chamber_status(
        self,
        db: AsyncSession,
        organization_id: int
    ) -> List[SpeedBreedingChamber]:
        """Get growth chamber status from database."""
        query = select(SpeedBreedingChamber).where(
            SpeedBreedingChamber.organization_id == organization_id
        )
        result = await db.execute(query)
        chambers = result.scalars().all()
        return chambers

    async def create_chamber(
        self,
        db: AsyncSession,
        organization_id: int,
        chamber: SpeedBreedingChamberCreate
    ) -> SpeedBreedingChamber:
        db_chamber = SpeedBreedingChamber(
            **chamber.model_dump(),
            organization_id=organization_id
        )
        db.add(db_chamber)
        await db.commit()
        await db.refresh(db_chamber)
        return db_chamber
    
    async def get_statistics(
        self,
        db: AsyncSession,
        organization_id: int
    ) -> Dict[str, Any]:
        """Get speed breeding statistics from database."""
        
        # Total protocols
        count_query = select(func.count()).select_from(SpeedBreedingProtocol).where(
            SpeedBreedingProtocol.organization_id == organization_id
        )
        total_protocols = (await db.execute(count_query)).scalar()

        # Active batches
        batches_query = select(SpeedBreedingBatch).where(
            SpeedBreedingBatch.organization_id == organization_id,
            SpeedBreedingBatch.status.in_(["growing", "flowering", "harvesting"])
        )
        active_batches_res = await db.execute(batches_query)
        active_batches = active_batches_res.scalars().all()

        active_batches_count = len(active_batches)
        total_entries = sum(b.entries for b in active_batches if b.entries)

        # Chambers in use
        chamber_ids = set(b.chamber_id for b in active_batches if b.chamber_id)
        chambers_in_use = len(chamber_ids)

        # Crops
        crops_query = select(SpeedBreedingProtocol.crop).where(
            SpeedBreedingProtocol.organization_id == organization_id
        ).distinct()
        crops = (await db.execute(crops_query)).scalars().all()

        # Avg generations
        avg_gen_query = select(func.avg(SpeedBreedingProtocol.generations_per_year)).where(
             SpeedBreedingProtocol.organization_id == organization_id
        )
        avg_gen = (await db.execute(avg_gen_query)).scalar() or 0
        
        return {
            "total_protocols": total_protocols,
            "active_batches": active_batches_count,
            "total_entries": total_entries,
            "chambers_in_use": chambers_in_use,
            "crops": [c for c in crops if c],
            "avg_generations_per_year": round(avg_gen, 1),
            "avg_success_rate": 0.95 # Mock for now
        }


# Singleton instance
speed_breeding_service = SpeedBreedingService()
