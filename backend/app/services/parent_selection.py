"""
Parent Selection Service
Manage potential parents for crossing and provide recommendations
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
import random


class ParentSelectionService:
    """Service for managing parent selection for breeding crosses"""

    def __init__(self):
        # In-memory storage (would be database in production)
        self.parents: Dict[str, Dict[str, Any]] = {}
        self.breeding_objectives: List[Dict[str, Any]] = []
        self._init_demo_data()

    def _init_demo_data(self):
        """Initialize with demo parent data"""
        demo_parents = [
            {
                "id": "parent-001",
                "name": "IR64",
                "type": "elite",
                "species": "Oryza sativa",
                "subspecies": "indica",
                "traits": ["High yield", "Good quality", "Medium duration"],
                "gebv": 2.45,
                "heterosis_potential": 15.2,
                "pedigree": "IR5657-33-2-1/IR2061-465-1-5-5",
                "origin": "IRRI, Philippines",
                "year_released": 1985,
                "markers": {"Xa21": True, "xa13": False, "Pi-ta": True, "Sub1A": False},
                "agronomic_data": {
                    "yield_potential": 7.5,
                    "days_to_maturity": 115,
                    "plant_height": 100,
                    "grain_quality": "Premium"
                }
            },
            {
                "id": "parent-002",
                "name": "Swarna",
                "type": "elite",
                "species": "Oryza sativa",
                "subspecies": "indica",
                "traits": ["High yield", "Wide adaptation", "Lodging tolerant"],
                "gebv": 2.38,
                "heterosis_potential": 12.8,
                "pedigree": "Vasistha/Mahsuri",
                "origin": "India",
                "year_released": 1979,
                "markers": {"Xa21": False, "xa13": True, "Pi-ta": False, "Sub1A": False},
                "agronomic_data": {
                    "yield_potential": 7.0,
                    "days_to_maturity": 140,
                    "plant_height": 110,
                    "grain_quality": "Good"
                }
            },
            {
                "id": "parent-003",
                "name": "FR13A",
                "type": "donor",
                "species": "Oryza sativa",
                "subspecies": "indica",
                "traits": ["Submergence tolerance", "Deep water adaptation"],
                "gebv": 1.85,
                "heterosis_potential": 8.5,
                "pedigree": "Landrace selection",
                "origin": "India (Odisha)",
                "year_released": None,
                "markers": {"Xa21": False, "xa13": False, "Pi-ta": False, "Sub1A": True},
                "agronomic_data": {
                    "yield_potential": 4.5,
                    "days_to_maturity": 150,
                    "plant_height": 140,
                    "grain_quality": "Medium"
                }
            },
            {
                "id": "parent-004",
                "name": "Pokkali",
                "type": "donor",
                "species": "Oryza sativa",
                "subspecies": "indica",
                "traits": ["Salt tolerance", "Coastal adaptation"],
                "gebv": 1.72,
                "heterosis_potential": 7.2,
                "pedigree": "Kerala landrace",
                "origin": "India (Kerala)",
                "year_released": None,
                "markers": {"Xa21": False, "xa13": False, "Pi-ta": False, "Sub1A": False, "Saltol": True},
                "agronomic_data": {
                    "yield_potential": 3.5,
                    "days_to_maturity": 160,
                    "plant_height": 150,
                    "grain_quality": "Medium"
                }
            },
            {
                "id": "parent-005",
                "name": "Kasalath",
                "type": "landrace",
                "species": "Oryza sativa",
                "subspecies": "aus",
                "traits": ["Drought tolerance", "Deep roots", "Phosphorus uptake"],
                "gebv": 1.65,
                "heterosis_potential": 6.8,
                "pedigree": "Aus landrace",
                "origin": "India",
                "year_released": None,
                "markers": {"Xa21": False, "xa13": False, "Pi-ta": False, "Sub1A": False, "Pup1": True},
                "agronomic_data": {
                    "yield_potential": 3.0,
                    "days_to_maturity": 100,
                    "plant_height": 90,
                    "grain_quality": "Low"
                }
            },
            {
                "id": "parent-006",
                "name": "N22",
                "type": "donor",
                "species": "Oryza sativa",
                "subspecies": "aus",
                "traits": ["Heat tolerance", "Drought tolerance", "Early maturity"],
                "gebv": 1.58,
                "heterosis_potential": 9.1,
                "pedigree": "Aus variety",
                "origin": "India",
                "year_released": 1978,
                "markers": {"Xa21": False, "xa13": False, "Pi-ta": False, "Sub1A": False},
                "agronomic_data": {
                    "yield_potential": 3.5,
                    "days_to_maturity": 90,
                    "plant_height": 85,
                    "grain_quality": "Medium"
                }
            },
            {
                "id": "parent-007",
                "name": "IRBB60",
                "type": "donor",
                "species": "Oryza sativa",
                "subspecies": "indica",
                "traits": ["Bacterial blight resistance", "Multiple Xa genes"],
                "gebv": 1.92,
                "heterosis_potential": 5.4,
                "pedigree": "IR24 NIL with Xa4+xa5+xa13+Xa21",
                "origin": "IRRI, Philippines",
                "year_released": 2000,
                "markers": {"Xa21": True, "xa13": True, "xa5": True, "Xa4": True},
                "agronomic_data": {
                    "yield_potential": 5.0,
                    "days_to_maturity": 120,
                    "plant_height": 95,
                    "grain_quality": "Good"
                }
            },
            {
                "id": "parent-008",
                "name": "Tetep",
                "type": "donor",
                "species": "Oryza sativa",
                "subspecies": "indica",
                "traits": ["Blast resistance", "Multiple Pi genes"],
                "gebv": 1.78,
                "heterosis_potential": 6.2,
                "pedigree": "Vietnamese variety",
                "origin": "Vietnam",
                "year_released": None,
                "markers": {"Pi-ta": True, "Pi-b": True, "Pi-kh": True},
                "agronomic_data": {
                    "yield_potential": 4.0,
                    "days_to_maturity": 130,
                    "plant_height": 120,
                    "grain_quality": "Medium"
                }
            },
            {
                "id": "parent-009",
                "name": "Sahbhagi Dhan",
                "type": "elite",
                "species": "Oryza sativa",
                "subspecies": "indica",
                "traits": ["Drought tolerance", "Direct seeding", "Rainfed adaptation"],
                "gebv": 2.15,
                "heterosis_potential": 11.5,
                "pedigree": "IR55419-04/Way Rarem",
                "origin": "IRRI/India",
                "year_released": 2009,
                "markers": {"qDTY1.1": True, "qDTY2.1": True, "qDTY3.1": True},
                "agronomic_data": {
                    "yield_potential": 5.5,
                    "days_to_maturity": 105,
                    "plant_height": 95,
                    "grain_quality": "Good"
                }
            },
            {
                "id": "parent-010",
                "name": "Swarna-Sub1",
                "type": "elite",
                "species": "Oryza sativa",
                "subspecies": "indica",
                "traits": ["High yield", "Submergence tolerance", "Wide adaptation"],
                "gebv": 2.32,
                "heterosis_potential": 13.2,
                "pedigree": "Swarna*3/IR49830-7-1-2-2",
                "origin": "IRRI/India",
                "year_released": 2009,
                "markers": {"Sub1A": True, "xa13": True},
                "agronomic_data": {
                    "yield_potential": 6.5,
                    "days_to_maturity": 140,
                    "plant_height": 105,
                    "grain_quality": "Good"
                }
            }
        ]

        for parent in demo_parents:
            self.parents[parent["id"]] = parent

        # Default breeding objectives
        self.breeding_objectives = [
            {"trait": "Yield", "weight": 40, "direction": "maximize"},
            {"trait": "Disease Resistance", "weight": 25, "direction": "maximize"},
            {"trait": "Drought Tolerance", "weight": 20, "direction": "maximize"},
            {"trait": "Grain Quality", "weight": 15, "direction": "maximize"}
        ]

    def list_parents(
        self,
        parent_type: Optional[str] = None,
        trait: Optional[str] = None,
        min_gebv: Optional[float] = None,
        search: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """List available parents with optional filters"""
        results = []

        for parent in self.parents.values():
            # Apply filters
            if parent_type and parent.get("type") != parent_type:
                continue
            if min_gebv and parent.get("gebv", 0) < min_gebv:
                continue
            if trait:
                trait_lower = trait.lower()
                if not any(trait_lower in t.lower() for t in parent.get("traits", [])):
                    continue
            if search:
                search_lower = search.lower()
                if not (
                    search_lower in parent.get("name", "").lower()
                    or search_lower in parent.get("pedigree", "").lower()
                    or any(search_lower in t.lower() for t in parent.get("traits", []))
                ):
                    continue

            results.append(parent)

        # Sort by GEBV descending
        results.sort(key=lambda x: x.get("gebv", 0), reverse=True)
        return results

    def get_parent(self, parent_id: str) -> Optional[Dict[str, Any]]:
        """Get a single parent by ID"""
        return self.parents.get(parent_id)

    def predict_cross(
        self,
        parent1_id: str,
        parent2_id: str,
    ) -> Dict[str, Any]:
        """Predict cross performance between two parents"""
        parent1 = self.parents.get(parent1_id)
        parent2 = self.parents.get(parent2_id)

        if not parent1 or not parent2:
            return {"error": "One or both parents not found"}

        # Calculate expected GEBV (mid-parent value)
        expected_gebv = (parent1["gebv"] + parent2["gebv"]) / 2

        # Calculate heterosis (simplified)
        avg_heterosis = (parent1["heterosis_potential"] + parent2["heterosis_potential"]) / 2

        # Calculate genetic distance (simplified based on type and traits)
        type_distance = 0.2 if parent1["type"] != parent2["type"] else 0
        trait_overlap = len(set(parent1["traits"]) & set(parent2["traits"]))
        trait_distance = 0.1 * (len(parent1["traits"]) + len(parent2["traits"]) - 2 * trait_overlap)
        genetic_distance = min(1.0, type_distance + trait_distance + random.uniform(0.1, 0.3))

        # Calculate success probability
        success_prob = min(95, 50 + expected_gebv * 10 + avg_heterosis * 0.5)

        # Combine traits
        combined_traits = list(set(parent1["traits"]) | set(parent2["traits"]))

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
            "yield_potential": (p1_agro.get("yield_potential", 5) + p2_agro.get("yield_potential", 5)) / 2 * (1 + avg_heterosis / 100),
            "days_to_maturity": (p1_agro.get("days_to_maturity", 120) + p2_agro.get("days_to_maturity", 120)) / 2,
            "plant_height": (p1_agro.get("plant_height", 100) + p2_agro.get("plant_height", 100)) / 2,
        }

        return {
            "parent1": {"id": parent1["id"], "name": parent1["name"], "type": parent1["type"]},
            "parent2": {"id": parent2["id"], "name": parent2["name"], "type": parent2["type"]},
            "expected_gebv": round(expected_gebv, 2),
            "heterosis": round(avg_heterosis, 1),
            "genetic_distance": round(genetic_distance, 2),
            "success_probability": round(success_prob, 0),
            "combined_traits": combined_traits,
            "combined_markers": combined_markers,
            "predicted_agronomic": predicted_agro,
            "recommendation": self._get_cross_recommendation(expected_gebv, avg_heterosis, genetic_distance)
        }

    def _get_cross_recommendation(self, gebv: float, heterosis: float, distance: float) -> str:
        """Generate recommendation for a cross"""
        if gebv > 2.0 and heterosis > 10:
            return "Highly recommended - excellent breeding value and heterosis potential"
        elif gebv > 1.8 and distance > 0.3:
            return "Recommended - good genetic diversity for trait introgression"
        elif gebv > 1.5:
            return "Consider - moderate breeding value, may need backcrossing"
        else:
            return "Low priority - consider other combinations"

    def get_recommendations(
        self,
        target_traits: Optional[List[str]] = None,
        limit: int = 5,
    ) -> List[Dict[str, Any]]:
        """Get AI-powered cross recommendations"""
        recommendations = []
        parents_list = list(self.parents.values())

        # Generate all possible crosses
        for i, p1 in enumerate(parents_list):
            for p2 in parents_list[i + 1:]:
                prediction = self.predict_cross(p1["id"], p2["id"])
                if "error" not in prediction:
                    # Score based on objectives
                    score = prediction["expected_gebv"] * 20 + prediction["heterosis"] * 2 + prediction["genetic_distance"] * 10

                    # Bonus for target traits
                    if target_traits:
                        trait_match = sum(1 for t in target_traits if any(t.lower() in ct.lower() for ct in prediction["combined_traits"]))
                        score += trait_match * 10

                    recommendations.append({
                        "cross": f"{p1['name']} × {p2['name']}",
                        "parent1_id": p1["id"],
                        "parent2_id": p2["id"],
                        "score": round(score, 0),
                        "reason": prediction["recommendation"],
                        "expected_gebv": prediction["expected_gebv"],
                        "heterosis": prediction["heterosis"],
                        "combined_traits": prediction["combined_traits"][:4]  # Top 4 traits
                    })

        # Sort by score and return top recommendations
        recommendations.sort(key=lambda x: x["score"], reverse=True)
        return recommendations[:limit]

    def get_breeding_objectives(self) -> List[Dict[str, Any]]:
        """Get current breeding objectives"""
        return self.breeding_objectives

    def set_breeding_objectives(self, objectives: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Set breeding objectives"""
        self.breeding_objectives = objectives
        return {"status": "success", "objectives": objectives}

    def get_parent_types(self) -> List[Dict[str, str]]:
        """Get available parent types"""
        return [
            {"value": "elite", "label": "Elite Line", "description": "High-performing breeding lines"},
            {"value": "donor", "label": "Donor Line", "description": "Source of specific traits/genes"},
            {"value": "landrace", "label": "Landrace", "description": "Traditional varieties with unique traits"}
        ]

    def get_statistics(self) -> Dict[str, Any]:
        """Get parent selection statistics"""
        parents_list = list(self.parents.values())
        return {
            "total_parents": len(parents_list),
            "by_type": {
                "elite": sum(1 for p in parents_list if p["type"] == "elite"),
                "donor": sum(1 for p in parents_list if p["type"] == "donor"),
                "landrace": sum(1 for p in parents_list if p["type"] == "landrace")
            },
            "avg_gebv": round(sum(p["gebv"] for p in parents_list) / len(parents_list), 2) if parents_list else 0,
            "top_gebv_parent": max(parents_list, key=lambda x: x["gebv"])["name"] if parents_list else None
        }


# Singleton instance
parent_selection_service = ParentSelectionService()
