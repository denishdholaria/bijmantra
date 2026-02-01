"""
Molecular Breeding Service

Integrated molecular breeding tools and workflows.
Queries real data from database - no demo/mock data.
"""

from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func


class MolecularBreedingService:
    """Service for molecular breeding workflows.
    
    All methods query the database for real data.
    Returns empty results when no data exists.
    """
    
    async def get_schemes(
        self,
        db: AsyncSession,
        organization_id: int,
        scheme_type: Optional[str] = None,
        status: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Get breeding schemes from database.
        
        Args:
            db: Database session
            organization_id: Organization ID for multi-tenant filtering
            scheme_type: Filter by scheme type (MABC, MARS, GS, Speed)
            status: Filter by status (active, planned, completed)
            
        Returns:
            List of breeding scheme dictionaries, empty if no data
        """
        from app.models.core import Program
        
        # Query programs that have molecular breeding info
        stmt = (
            select(Program)
            .where(Program.organization_id == organization_id)
        )
        
        result = await db.execute(stmt)
        programs = result.scalars().all()
        
        schemes = []
        for p in programs:
            info = p.additional_info or {}
            mb_schemes = info.get("molecular_breeding_schemes", [])
            
            for scheme in mb_schemes:
                # Apply filters
                if scheme_type and scheme.get("type", "").lower() != scheme_type.lower():
                    continue
                if status and scheme.get("status", "").lower() != status.lower():
                    continue
                
                schemes.append({
                    "id": scheme.get("id", f"scheme-{p.id}"),
                    "name": scheme.get("name", "Unnamed Scheme"),
                    "type": scheme.get("type", "Unknown"),
                    "status": scheme.get("status", "planned"),
                    "generation": scheme.get("generation"),
                    "progress": scheme.get("progress", 0),
                    "target_traits": scheme.get("target_traits", []),
                    "start_date": scheme.get("start_date"),
                    "target_date": scheme.get("target_date"),
                    "program_id": str(p.id),
                    "program_name": p.program_name,
                })
        
        return schemes
    
    async def get_scheme(
        self,
        db: AsyncSession,
        organization_id: int,
        scheme_id: str,
    ) -> Optional[Dict[str, Any]]:
        """Get a specific breeding scheme by ID.
        
        Args:
            db: Database session
            organization_id: Organization ID for multi-tenant filtering
            scheme_id: Scheme ID
            
        Returns:
            Scheme dictionary or None if not found
        """
        schemes = await self.get_schemes(db, organization_id)
        
        for s in schemes:
            if s["id"] == scheme_id:
                return s
        
        return None
    
    async def get_introgression_lines(
        self,
        db: AsyncSession,
        organization_id: int,
        scheme_id: Optional[str] = None,
        foreground_status: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Get introgression lines from database.
        
        Args:
            db: Database session
            organization_id: Organization ID for multi-tenant filtering
            scheme_id: Filter by breeding scheme ID
            foreground_status: Filter by foreground marker status (fixed, segregating)
            
        Returns:
            List of introgression line dictionaries, empty if no data
        """
        from app.models.germplasm import Germplasm
        
        # Query germplasm that are introgression lines
        stmt = (
            select(Germplasm)
            .where(Germplasm.organization_id == organization_id)
        )
        
        result = await db.execute(stmt)
        germplasm_list = result.scalars().all()
        
        lines = []
        for g in germplasm_list:
            info = g.additional_info or {}
            
            # Check if this is an introgression line
            if not info.get("is_introgression_line"):
                continue
            
            line_scheme_id = info.get("scheme_id")
            fg_status = info.get("foreground_status")
            
            # Apply filters
            if scheme_id and line_scheme_id != scheme_id:
                continue
            if foreground_status and fg_status and fg_status.lower() != foreground_status.lower():
                continue
            
            lines.append({
                "id": str(g.id),
                "name": g.germplasm_name or f"IL-{g.id}",
                "donor": info.get("donor"),
                "recurrent": info.get("recurrent_parent"),
                "target_gene": info.get("target_gene"),
                "bc_generation": info.get("bc_generation"),
                "rp_recovery": info.get("rp_recovery"),
                "foreground_status": fg_status,
                "scheme_id": line_scheme_id,
            })
        
        return lines
    
    async def get_statistics(
        self,
        db: AsyncSession,
        organization_id: int,
    ) -> Dict[str, Any]:
        """Get molecular breeding statistics from database.
        
        Args:
            db: Database session
            organization_id: Organization ID for multi-tenant filtering
            
        Returns:
            Statistics dictionary
        """
        schemes = await self.get_schemes(db, organization_id)
        lines = await self.get_introgression_lines(db, organization_id)
        
        if not schemes and not lines:
            return {
                "total_schemes": 0,
                "active_schemes": 0,
                "total_lines": 0,
                "fixed_lines": 0,
                "target_genes": 0,
                "avg_progress": 0,
                "by_type": {
                    "MABC": 0,
                    "MARS": 0,
                    "GS": 0,
                    "Speed": 0,
                },
            }
        
        avg_progress = sum(s.get("progress", 0) for s in schemes) / len(schemes) if schemes else 0
        target_genes = set()
        for line in lines:
            gene = line.get("target_gene")
            if gene:
                target_genes.add(gene)
        
        return {
            "total_schemes": len(schemes),
            "active_schemes": len([s for s in schemes if s.get("status") == "active"]),
            "total_lines": len(lines),
            "fixed_lines": len([l for l in lines if l.get("foreground_status") == "fixed"]),
            "target_genes": len(target_genes),
            "avg_progress": round(avg_progress, 1),
            "by_type": {
                "MABC": len([s for s in schemes if s.get("type") == "MABC"]),
                "MARS": len([s for s in schemes if s.get("type") == "MARS"]),
                "GS": len([s for s in schemes if s.get("type") == "GS"]),
                "Speed": len([s for s in schemes if s.get("type") == "Speed"]),
            },
        }
    
    async def get_pyramiding_matrix(
        self,
        db: AsyncSession,
        organization_id: int,
        scheme_id: str,
    ) -> Dict[str, Any]:
        """Get gene pyramiding matrix for a scheme.
        
        Args:
            db: Database session
            organization_id: Organization ID for multi-tenant filtering
            scheme_id: Breeding scheme ID
            
        Returns:
            Pyramiding matrix dictionary
        """
        lines = await self.get_introgression_lines(db, organization_id, scheme_id=scheme_id)
        
        if not lines:
            return {
                "scheme_id": scheme_id,
                "target_genes": [],
                "pyramids": [],
                "triple_stack_count": 0,
            }
        
        # Get unique target genes
        genes = list(set(l.get("target_gene") for l in lines if l.get("target_gene")))
        
        # Build pyramid combinations from lines with multiple genes
        # This would require more complex logic to track gene combinations
        # For now, return basic structure
        return {
            "scheme_id": scheme_id,
            "target_genes": genes,
            "pyramids": [],  # Would need to calculate from genotype data
            "triple_stack_count": 0,
        }


# Singleton instance
molecular_breeding_service = MolecularBreedingService()
