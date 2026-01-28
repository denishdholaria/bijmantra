"""
Parent Selection Service

Manage potential parents for crossing and provide recommendations.
Queries real Germplasm data from database.

Per Zero Mock Data Policy: All data from database, never in-memory arrays.
"""

from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_, and_
from sqlalchemy.orm import selectinload
import logging

from app.models.germplasm import Germplasm, GermplasmAttribute

logger = logging.getLogger(__name__)


class ParentSelectionService:
    """
    Service for managing parent selection for breeding crosses.
    
    Queries Germplasm table for parent candidates. Parent-specific data
    (GEBV, markers, heterosis potential) stored in additional_info JSON.
    """

    async def list_parents(
        self,
        db: AsyncSession,
        organization_id: int,
        parent_type: Optional[str] = None,
        trait: Optional[str] = None,
        min_gebv: Optional[float] = None,
        search: Optional[str] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """
        List available parents with optional filters.
        
        Parents are germplasm entries with breeding-relevant metadata
        stored in additional_info.
        """
        stmt = (
            select(Germplasm)
            .where(Germplasm.organization_id == organization_id)
        )
        
        # Search filter
        if search:
            search_pattern = f"%{search}%"
            stmt = stmt.where(
                or_(
                    Germplasm.germplasm_name.ilike(search_pattern),
                    Germplasm.pedigree.ilike(search_pattern),
                    Germplasm.accession_number.ilike(search_pattern),
                )
            )
        
        stmt = stmt.limit(limit)
        
        result = await db.execute(stmt)
        germplasm_list = result.scalars().all()
        
        parents = []
        for g in germplasm_list:
            info = g.additional_info or {}
            
            # Extract parent-specific data from additional_info
            gebv = info.get("gebv", 0)
            p_type = info.get("parent_type", "elite")
            traits = info.get("traits", [])
            
            # Apply filters that require additional_info data
            if parent_type and p_type != parent_type:
                continue
            if min_gebv and gebv < min_gebv:
                continue
            if trait:
                trait_lower = trait.lower()
                if not any(trait_lower in t.lower() for t in traits):
                    continue
            
            parents.append(self._germplasm_to_parent(g))
        
        # Sort by GEBV descending
        parents.sort(key=lambda x: x.get("gebv", 0), reverse=True)
        return parents

    async def get_parent(
        self,
        db: AsyncSession,
        organization_id: int,
        parent_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get a single parent by ID (germplasm_db_id or internal id)."""
        stmt = (
            select(Germplasm)
            .where(Germplasm.organization_id == organization_id)
        )
        
        # Try to match by germplasm_db_id or internal id
        try:
            int_id = int(parent_id.replace("parent-", ""))
            stmt = stmt.where(Germplasm.id == int_id)
        except ValueError:
            stmt = stmt.where(Germplasm.germplasm_db_id == parent_id)
        
        result = await db.execute(stmt)
        germplasm = result.scalar_one_or_none()
        
        if not germplasm:
            return None
        
        return self._germplasm_to_parent(germplasm)

    def _germplasm_to_parent(self, g: Germplasm) -> Dict[str, Any]:
        """Convert Germplasm model to parent dict format."""
        info = g.additional_info or {}
        
        return {
            "id": f"parent-{g.id}",
            "germplasm_id": g.id,
            "name": g.germplasm_name,
            "type": info.get("parent_type", "elite"),
            "species": f"{g.genus or ''} {g.species or ''}".strip() or "Unknown",
            "subspecies": g.subtaxa or info.get("subspecies"),
            "traits": info.get("traits", []),
            "gebv": info.get("gebv", 0),
            "heterosis_potential": info.get("heterosis_potential", 0),
            "pedigree": g.pedigree,
            "origin": g.institute_name or g.country_of_origin_code,
            "year_released": info.get("year_released"),
            "markers": info.get("markers", {}),
            "agronomic_data": info.get("agronomic_data", {}),
        }

    async def predict_cross(
        self,
        db: AsyncSession,
        organization_id: int,
        parent1_id: str,
        parent2_id: str,
    ) -> Dict[str, Any]:
        """Predict cross performance between two parents."""
        parent1 = await self.get_parent(db, organization_id, parent1_id)
        parent2 = await self.get_parent(db, organization_id, parent2_id)

        if not parent1 or not parent2:
            return {"error": "One or both parents not found"}

        # Calculate expected GEBV (mid-parent value)
        expected_gebv = (parent1.get("gebv", 0) + parent2.get("gebv", 0)) / 2

        # Calculate heterosis (simplified)
        avg_heterosis = (
            parent1.get("heterosis_potential", 0) + 
            parent2.get("heterosis_potential", 0)
        ) / 2

        # Calculate genetic distance (simplified based on type and traits)
        type_distance = 0.2 if parent1.get("type") != parent2.get("type") else 0
        p1_traits = set(parent1.get("traits", []))
        p2_traits = set(parent2.get("traits", []))
        trait_overlap = len(p1_traits & p2_traits)
        trait_distance = 0.1 * (len(p1_traits) + len(p2_traits) - 2 * trait_overlap)
        genetic_distance = min(1.0, type_distance + trait_distance + 0.2)

        # Calculate success probability
        success_prob = min(95, 50 + expected_gebv * 10 + avg_heterosis * 0.5)

        # Combine traits
        combined_traits = list(p1_traits | p2_traits)

        # Combine markers
        combined_markers = {}
        for marker, present in parent1.get("markers", {}).items():
            combined_markers[marker] = present
        for marker, present in parent2.get("markers", {}).items():
            if marker not in combined_markers:
                combined_markers[marker] = present
            elif present:
                combined_markers[marker] = True

        # Predict agronomic data
        p1_agro = parent1.get("agronomic_data", {})
        p2_agro = parent2.get("agronomic_data", {})
        predicted_agro = {
            "yield_potential": (
                p1_agro.get("yield_potential", 5) + 
                p2_agro.get("yield_potential", 5)
            ) / 2 * (1 + avg_heterosis / 100),
            "days_to_maturity": (
                p1_agro.get("days_to_maturity", 120) + 
                p2_agro.get("days_to_maturity", 120)
            ) / 2,
            "plant_height": (
                p1_agro.get("plant_height", 100) + 
                p2_agro.get("plant_height", 100)
            ) / 2,
        }

        return {
            "parent1": {
                "id": parent1["id"], 
                "name": parent1["name"], 
                "type": parent1.get("type")
            },
            "parent2": {
                "id": parent2["id"], 
                "name": parent2["name"], 
                "type": parent2.get("type")
            },
            "expected_gebv": round(expected_gebv, 2),
            "heterosis": round(avg_heterosis, 1),
            "genetic_distance": round(genetic_distance, 2),
            "success_probability": round(success_prob, 0),
            "combined_traits": combined_traits,
            "combined_markers": combined_markers,
            "predicted_agronomic": predicted_agro,
            "recommendation": self._get_cross_recommendation(
                expected_gebv, avg_heterosis, genetic_distance
            )
        }

    def _get_cross_recommendation(
        self, 
        gebv: float, 
        heterosis: float, 
        distance: float
    ) -> str:
        """Generate recommendation for a cross."""
        if gebv > 2.0 and heterosis > 10:
            return "Highly recommended - excellent breeding value and heterosis potential"
        elif gebv > 1.8 and distance > 0.3:
            return "Recommended - good genetic diversity for trait introgression"
        elif gebv > 1.5:
            return "Consider - moderate breeding value, may need backcrossing"
        else:
            return "Low priority - consider other combinations"

    async def get_recommendations(
        self,
        db: AsyncSession,
        organization_id: int,
        target_traits: Optional[List[str]] = None,
        limit: int = 5,
    ) -> List[Dict[str, Any]]:
        """Get cross recommendations based on available parents."""
        # Get all parents
        parents_list = await self.list_parents(
            db=db,
            organization_id=organization_id,
            limit=100
        )
        
        if len(parents_list) < 2:
            return []
        
        recommendations = []

        # Generate crosses for top parents (limit combinations)
        top_parents = parents_list[:20]  # Limit to avoid O(n²) explosion
        
        for i, p1 in enumerate(top_parents):
            for p2 in top_parents[i + 1:]:
                prediction = await self.predict_cross(
                    db, organization_id, p1["id"], p2["id"]
                )
                if "error" not in prediction:
                    # Score based on objectives
                    score = (
                        prediction["expected_gebv"] * 20 + 
                        prediction["heterosis"] * 2 + 
                        prediction["genetic_distance"] * 10
                    )

                    # Bonus for target traits
                    if target_traits:
                        trait_match = sum(
                            1 for t in target_traits 
                            if any(t.lower() in ct.lower() for ct in prediction["combined_traits"])
                        )
                        score += trait_match * 10

                    recommendations.append({
                        "cross": f"{p1['name']} × {p2['name']}",
                        "parent1_id": p1["id"],
                        "parent2_id": p2["id"],
                        "score": round(score, 0),
                        "reason": prediction["recommendation"],
                        "expected_gebv": prediction["expected_gebv"],
                        "heterosis": prediction["heterosis"],
                        "combined_traits": prediction["combined_traits"][:4]
                    })

        # Sort by score and return top recommendations
        recommendations.sort(key=lambda x: x["score"], reverse=True)
        return recommendations[:limit]

    def get_breeding_objectives(self) -> List[Dict[str, Any]]:
        """Get default breeding objectives."""
        return [
            {"trait": "Yield", "weight": 40, "direction": "maximize"},
            {"trait": "Disease Resistance", "weight": 25, "direction": "maximize"},
            {"trait": "Drought Tolerance", "weight": 20, "direction": "maximize"},
            {"trait": "Grain Quality", "weight": 15, "direction": "maximize"}
        ]

    def get_parent_types(self) -> List[Dict[str, str]]:
        """Get available parent types."""
        return [
            {"value": "elite", "label": "Elite Line", "description": "High-performing breeding lines"},
            {"value": "donor", "label": "Donor Line", "description": "Source of specific traits/genes"},
            {"value": "landrace", "label": "Landrace", "description": "Traditional varieties with unique traits"}
        ]

    async def get_statistics(
        self,
        db: AsyncSession,
        organization_id: int
    ) -> Dict[str, Any]:
        """Get parent selection statistics from database."""
        # Count total germplasm
        count_stmt = (
            select(func.count(Germplasm.id))
            .where(Germplasm.organization_id == organization_id)
        )
        result = await db.execute(count_stmt)
        total_count = result.scalar() or 0
        
        if total_count == 0:
            return {
                "total_parents": 0,
                "by_type": {"elite": 0, "donor": 0, "landrace": 0},
                "avg_gebv": 0,
                "top_gebv_parent": None,
                "message": "No germplasm data available. Add germplasm to enable parent selection."
            }
        
        # Get all germplasm for statistics
        parents = await self.list_parents(db, organization_id, limit=1000)
        
        # Calculate statistics
        by_type = {"elite": 0, "donor": 0, "landrace": 0}
        gebv_sum = 0
        top_parent = None
        top_gebv = -999
        
        for p in parents:
            p_type = p.get("type", "elite")
            if p_type in by_type:
                by_type[p_type] += 1
            
            gebv = p.get("gebv", 0)
            gebv_sum += gebv
            
            if gebv > top_gebv:
                top_gebv = gebv
                top_parent = p.get("name")
        
        return {
            "total_parents": len(parents),
            "by_type": by_type,
            "avg_gebv": round(gebv_sum / len(parents), 2) if parents else 0,
            "top_gebv_parent": top_parent
        }


# Singleton instance
parent_selection_service = ParentSelectionService()
