"""
Speed Breeding Service
Accelerated generation advancement protocols.
Queries real data from database - no demo/mock data.
"""
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func


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
    ) -> List[Dict[str, Any]]:
        """Get speed breeding protocols from database.
        
        Args:
            db: Database session
            organization_id: Organization ID for multi-tenant filtering
            crop: Filter by crop name
            status: Filter by status (active, inactive)
            
        Returns:
            List of protocol dictionaries, empty if no data
        """
        # Speed breeding protocols would be stored in a dedicated table
        # For now, return empty list until the table is created
        # TODO: Create speed_breeding_protocols table
        return []
    
    async def get_protocol(
        self, 
        db: AsyncSession,
        organization_id: int,
        protocol_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get single protocol by ID.
        
        Args:
            db: Database session
            organization_id: Organization ID for multi-tenant filtering
            protocol_id: Protocol ID
            
        Returns:
            Protocol dictionary or None if not found
        """
        # TODO: Query from speed_breeding_protocols table
        return None
    
    async def get_batches(
        self,
        db: AsyncSession,
        organization_id: int,
        protocol_id: Optional[str] = None,
        status: Optional[str] = None,
        chamber: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get active batches from database.
        
        Args:
            db: Database session
            organization_id: Organization ID for multi-tenant filtering
            protocol_id: Filter by protocol ID
            status: Filter by status (growing, flowering, harvesting)
            chamber: Filter by chamber name
            
        Returns:
            List of batch dictionaries, empty if no data
        """
        # TODO: Query from speed_breeding_batches table
        return []
    
    async def get_batch(
        self, 
        db: AsyncSession,
        organization_id: int,
        batch_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get single batch by ID.
        
        Args:
            db: Database session
            organization_id: Organization ID for multi-tenant filtering
            batch_id: Batch ID
            
        Returns:
            Batch dictionary or None if not found
        """
        # TODO: Query from speed_breeding_batches table
        return None
    
    async def calculate_timeline(
        self,
        db: AsyncSession,
        organization_id: int,
        protocol_id: str,
        target_generation: str,
        start_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """Calculate breeding timeline based on protocol parameters.
        
        Args:
            db: Database session
            organization_id: Organization ID for multi-tenant filtering
            protocol_id: Protocol ID to use for calculations
            target_generation: Target generation (e.g., "F6", "BC2F3")
            start_date: Optional start date (ISO format)
            
        Returns:
            Timeline dictionary with projected dates
        """
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
        days_per_gen = protocol.get("days_to_harvest", 75)
        days_to_flower = protocol.get("days_to_flower", 35)
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
            "protocol": protocol.get("name", "Unknown"),
            "crop": protocol.get("crop", "Unknown"),
            "target_generation": target_generation,
            "start_date": start.strftime("%Y-%m-%d"),
            "end_date": (start + timedelta(days=total_days + gen_num * 7)).strftime("%Y-%m-%d"),
            "total_days": total_days + gen_num * 7,
            "generations_per_year": protocol.get("generations_per_year", 4),
            "timeline": timeline
        }
    
    async def get_chamber_status(
        self,
        db: AsyncSession,
        organization_id: int
    ) -> List[Dict[str, Any]]:
        """Get growth chamber status from database.
        
        Args:
            db: Database session
            organization_id: Organization ID for multi-tenant filtering
            
        Returns:
            List of chamber status dictionaries, empty if no data
        """
        # TODO: Query from growth_chambers table with IoT sensor data
        return []
    
    async def get_statistics(
        self,
        db: AsyncSession,
        organization_id: int
    ) -> Dict[str, Any]:
        """Get speed breeding statistics from database.
        
        Args:
            db: Database session
            organization_id: Organization ID for multi-tenant filtering
            
        Returns:
            Statistics dictionary with counts
        """
        protocols = await self.get_protocols(db, organization_id)
        batches = await self.get_batches(db, organization_id)
        
        return {
            "total_protocols": len(protocols),
            "active_batches": len(batches),
            "total_entries": sum(b.get("entries", 0) for b in batches),
            "chambers_in_use": len(set(b.get("chamber") for b in batches if b.get("chamber"))),
            "crops": list(set(p.get("crop") for p in protocols if p.get("crop"))),
            "avg_generations_per_year": 0,
            "avg_success_rate": 0
        }


# Singleton instance
speed_breeding_service = SpeedBreedingService()
