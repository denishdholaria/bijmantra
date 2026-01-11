"""
Germplasm Comparison Service

Compare multiple germplasm entries side-by-side for selection decisions.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime


# Demo germplasm data with traits and markers
DEMO_GERMPLASM = [
    {
        "id": "G001",
        "name": "IR64",
        "accession": "IRRI-001",
        "species": "Oryza sativa",
        "origin": "Philippines",
        "pedigree": "IR5657-33-2-1/IR2061-465-1-5-5",
        "status": "active",
        "traits": {
            "yield": 6.5,
            "plant_height": 105,
            "days_to_maturity": 115,
            "grain_length": 7.2,
            "amylose": 23,
            "blast_resistance": "MR",
            "drought_tolerance": "S",
        },
        "markers": {
            "Xa21": "Present",
            "xa13": "Absent",
            "Pi-ta": "Present",
            "Sub1A": "Absent",
        },
    },
    {
        "id": "G002",
        "name": "Swarna",
        "accession": "CRRI-002",
        "species": "Oryza sativa",
        "origin": "India",
        "pedigree": "Vasistha/Mahsuri",
        "status": "active",
        "traits": {
            "yield": 5.8,
            "plant_height": 115,
            "days_to_maturity": 140,
            "grain_length": 5.5,
            "amylose": 25,
            "blast_resistance": "S",
            "drought_tolerance": "MT",
        },
        "markers": {
            "Xa21": "Absent",
            "xa13": "Present",
            "Pi-ta": "Absent",
            "Sub1A": "Present",
        },
    },
    {
        "id": "G003",
        "name": "Sahbhagi Dhan",
        "accession": "IRRI-003",
        "species": "Oryza sativa",
        "origin": "India",
        "pedigree": "IR74371-70-1-1",
        "status": "active",
        "traits": {
            "yield": 4.5,
            "plant_height": 100,
            "days_to_maturity": 105,
            "grain_length": 6.8,
            "amylose": 22,
            "blast_resistance": "MR",
            "drought_tolerance": "T",
        },
        "markers": {
            "Xa21": "Present",
            "xa13": "Absent",
            "Pi-ta": "Present",
            "Sub1A": "Absent",
        },
    },
    {
        "id": "G004",
        "name": "Swarna-Sub1",
        "accession": "IRRI-004",
        "species": "Oryza sativa",
        "origin": "India",
        "pedigree": "Swarna*3/IR49830-7-1-2-2",
        "status": "candidate",
        "traits": {
            "yield": 5.5,
            "plant_height": 112,
            "days_to_maturity": 138,
            "grain_length": 5.6,
            "amylose": 24,
            "blast_resistance": "S",
            "drought_tolerance": "MT",
        },
        "markers": {
            "Xa21": "Absent",
            "xa13": "Present",
            "Pi-ta": "Absent",
            "Sub1A": "Present",
        },
    },
    {
        "id": "G005",
        "name": "DRR Dhan 44",
        "accession": "IIRR-005",
        "species": "Oryza sativa",
        "origin": "India",
        "pedigree": "MTU1010/Swarna",
        "status": "active",
        "traits": {
            "yield": 6.2,
            "plant_height": 95,
            "days_to_maturity": 120,
            "grain_length": 6.5,
            "amylose": 21,
            "blast_resistance": "R",
            "drought_tolerance": "MT",
        },
        "markers": {
            "Xa21": "Present",
            "xa13": "Present",
            "Pi-ta": "Present",
            "Sub1A": "Absent",
        },
    },
    {
        "id": "G006",
        "name": "HD2967",
        "accession": "IARI-001",
        "species": "Triticum aestivum",
        "origin": "India",
        "pedigree": "ALD/COC//URES/HD2160M/HD2278",
        "status": "active",
        "traits": {
            "yield": 5.2,
            "plant_height": 98,
            "days_to_maturity": 145,
            "grain_length": 6.8,
            "amylose": 26,
            "blast_resistance": "MR",
            "drought_tolerance": "MT",
        },
        "markers": {
            "Lr24": "Present",
            "Yr15": "Present",
            "Sr31": "Absent",
            "Glu-D1": "Present",
        },
    },
    {
        "id": "G007",
        "name": "PBW343",
        "accession": "PAU-001",
        "species": "Triticum aestivum",
        "origin": "India",
        "pedigree": "ND/VG9144//KAL/BB/3/YACO/4/VEE#5",
        "status": "archived",
        "traits": {
            "yield": 4.8,
            "plant_height": 95,
            "days_to_maturity": 140,
            "grain_length": 6.5,
            "amylose": 25,
            "blast_resistance": "S",
            "drought_tolerance": "S",
        },
        "markers": {
            "Lr24": "Absent",
            "Yr15": "Absent",
            "Sr31": "Present",
            "Glu-D1": "Present",
        },
    },
    {
        "id": "G008",
        "name": "Pusa Basmati 1121",
        "accession": "IARI-002",
        "species": "Oryza sativa",
        "origin": "India",
        "pedigree": "Pusa Basmati 1/Type 3",
        "status": "active",
        "traits": {
            "yield": 4.2,
            "plant_height": 125,
            "days_to_maturity": 135,
            "grain_length": 8.4,
            "amylose": 20,
            "blast_resistance": "MS",
            "drought_tolerance": "S",
        },
        "markers": {
            "Xa21": "Absent",
            "xa13": "Absent",
            "Pi-ta": "Absent",
            "Sub1A": "Absent",
            "BADH2": "Present",
        },
    },
]


# Trait definitions
COMPARISON_TRAITS = [
    {"id": "yield", "name": "Yield", "unit": "t/ha", "type": "numeric", "higher_is_better": True},
    {"id": "plant_height", "name": "Plant Height", "unit": "cm", "type": "numeric", "higher_is_better": False},
    {"id": "days_to_maturity", "name": "Days to Maturity", "unit": "days", "type": "numeric", "higher_is_better": False},
    {"id": "grain_length", "name": "Grain Length", "unit": "mm", "type": "numeric", "higher_is_better": True},
    {"id": "amylose", "name": "Amylose Content", "unit": "%", "type": "numeric", "higher_is_better": False},
    {"id": "blast_resistance", "name": "Blast Resistance", "unit": "", "type": "categorical", "higher_is_better": True},
    {"id": "drought_tolerance", "name": "Drought Tolerance", "unit": "", "type": "categorical", "higher_is_better": True},
]

# Marker definitions
MARKER_DEFINITIONS = [
    {"id": "Xa21", "name": "Xa21", "gene": "Xa21", "trait": "Bacterial Blight Resistance", "crop": "Rice"},
    {"id": "xa13", "name": "xa13", "gene": "xa13", "trait": "Bacterial Blight Resistance", "crop": "Rice"},
    {"id": "Pi-ta", "name": "Pi-ta", "gene": "Pi-ta", "trait": "Blast Resistance", "crop": "Rice"},
    {"id": "Sub1A", "name": "Sub1A", "gene": "Sub1A", "trait": "Submergence Tolerance", "crop": "Rice"},
    {"id": "BADH2", "name": "BADH2", "gene": "BADH2", "trait": "Aroma", "crop": "Rice"},
    {"id": "Lr24", "name": "Lr24", "gene": "Lr24", "trait": "Leaf Rust Resistance", "crop": "Wheat"},
    {"id": "Yr15", "name": "Yr15", "gene": "Yr15", "trait": "Yellow Rust Resistance", "crop": "Wheat"},
    {"id": "Sr31", "name": "Sr31", "gene": "Sr31", "trait": "Stem Rust Resistance", "crop": "Wheat"},
    {"id": "Glu-D1", "name": "Glu-D1", "gene": "Glu-D1", "trait": "Bread-making Quality", "crop": "Wheat"},
]


class GermplasmComparisonService:
    """Service for germplasm comparison operations."""
    
    def __init__(self):
        self.germplasm_db = {g["id"]: g for g in DEMO_GERMPLASM}
    
    def list_germplasm(
        self,
        search: Optional[str] = None,
        species: Optional[str] = None,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 50
    ) -> Dict[str, Any]:
        """List germplasm with optional filters."""
        results = list(self.germplasm_db.values())
        
        if search:
            search_lower = search.lower()
            results = [
                g for g in results
                if search_lower in g["name"].lower()
                or search_lower in g["accession"].lower()
                or search_lower in g.get("pedigree", "").lower()
            ]
        
        if species:
            results = [g for g in results if species.lower() in g["species"].lower()]
        
        if status:
            results = [g for g in results if g["status"] == status]
        
        total = len(results)
        paginated = results[skip:skip + limit]
        
        return {
            "data": paginated,
            "total": total,
            "skip": skip,
            "limit": limit,
        }
    
    def get_germplasm(self, germplasm_id: str) -> Optional[Dict[str, Any]]:
        """Get a single germplasm entry by ID."""
        return self.germplasm_db.get(germplasm_id)
    
    def get_multiple(self, ids: List[str]) -> List[Dict[str, Any]]:
        """Get multiple germplasm entries by IDs."""
        return [self.germplasm_db[id] for id in ids if id in self.germplasm_db]
    
    def compare(self, ids: List[str]) -> Dict[str, Any]:
        """Compare multiple germplasm entries."""
        entries = self.get_multiple(ids)
        if not entries:
            return {"entries": [], "traits": [], "markers": [], "summary": {}}
        
        # Get all unique markers across entries
        all_markers = set()
        for entry in entries:
            all_markers.update(entry.get("markers", {}).keys())
        
        # Calculate best values for each trait
        trait_analysis = []
        for trait in COMPARISON_TRAITS:
            trait_id = trait["id"]
            values = []
            for entry in entries:
                val = entry.get("traits", {}).get(trait_id)
                if val is not None:
                    values.append({"id": entry["id"], "name": entry["name"], "value": val})
            
            if values:
                if trait["type"] == "numeric":
                    if trait["higher_is_better"]:
                        best = max(values, key=lambda x: x["value"])
                    else:
                        best = min(values, key=lambda x: x["value"])
                else:
                    # Categorical ordering
                    order = ["R", "T", "MR", "MT", "MS", "S", "HS"]
                    if trait["higher_is_better"]:
                        best = min(values, key=lambda x: order.index(str(x["value"])) if str(x["value"]) in order else 99)
                    else:
                        best = max(values, key=lambda x: order.index(str(x["value"])) if str(x["value"]) in order else -1)
                
                trait_analysis.append({
                    **trait,
                    "values": values,
                    "best": best,
                })
        
        # Marker analysis
        marker_analysis = []
        for marker_id in sorted(all_markers):
            marker_def = next((m for m in MARKER_DEFINITIONS if m["id"] == marker_id), None)
            values = []
            for entry in entries:
                val = entry.get("markers", {}).get(marker_id, "Unknown")
                values.append({"id": entry["id"], "name": entry["name"], "value": val})
            
            marker_analysis.append({
                "id": marker_id,
                "name": marker_def["name"] if marker_def else marker_id,
                "trait": marker_def["trait"] if marker_def else "Unknown",
                "values": values,
                "present_count": sum(1 for v in values if v["value"] == "Present"),
            })
        
        # Generate recommendations
        recommendations = self._generate_recommendations(entries, trait_analysis, marker_analysis)
        
        return {
            "entries": entries,
            "traits": trait_analysis,
            "markers": marker_analysis,
            "summary": {
                "total_entries": len(entries),
                "species": list(set(e["species"] for e in entries)),
                "recommendations": recommendations,
            },
        }
    
    def _generate_recommendations(
        self,
        entries: List[Dict],
        traits: List[Dict],
        markers: List[Dict]
    ) -> List[Dict[str, Any]]:
        """Generate selection recommendations based on comparison."""
        recommendations = []
        
        # Best for yield
        yield_trait = next((t for t in traits if t["id"] == "yield"), None)
        if yield_trait and yield_trait.get("best"):
            recommendations.append({
                "type": "yield",
                "title": "Best for Yield",
                "entry": yield_trait["best"]["name"],
                "value": f"{yield_trait['best']['value']} t/ha",
                "color": "green",
            })
        
        # Best disease resistance
        blast_trait = next((t for t in traits if t["id"] == "blast_resistance"), None)
        if blast_trait and blast_trait.get("best"):
            recommendations.append({
                "type": "disease",
                "title": "Best Disease Resistance",
                "entry": blast_trait["best"]["name"],
                "value": f"Blast: {blast_trait['best']['value']}",
                "color": "blue",
            })
        
        # Best stress tolerance
        drought_trait = next((t for t in traits if t["id"] == "drought_tolerance"), None)
        if drought_trait and drought_trait.get("best"):
            recommendations.append({
                "type": "stress",
                "title": "Best Stress Tolerance",
                "entry": drought_trait["best"]["name"],
                "value": f"Drought: {drought_trait['best']['value']}",
                "color": "purple",
            })
        
        # Marker-based recommendations
        marker_notes = []
        
        # Check for gene pyramiding opportunities
        xa21_marker = next((m for m in markers if m["id"] == "Xa21"), None)
        xa13_marker = next((m for m in markers if m["id"] == "xa13"), None)
        if xa21_marker and xa13_marker:
            xa21_entries = set(v["id"] for v in xa21_marker["values"] if v["value"] == "Present")
            xa13_entries = set(v["id"] for v in xa13_marker["values"] if v["value"] == "Present")
            if xa21_entries and xa13_entries:
                if xa21_entries & xa13_entries:
                    marker_notes.append({
                        "type": "success",
                        "message": "Gene pyramiding possible: Xa21 + xa13 for bacterial blight resistance",
                    })
                else:
                    marker_notes.append({
                        "type": "info",
                        "message": "Xa21 and xa13 available in different parents - crossing recommended",
                    })
        
        # Check for Sub1A
        sub1a_marker = next((m for m in markers if m["id"] == "Sub1A"), None)
        if sub1a_marker and sub1a_marker["present_count"] > 0:
            marker_notes.append({
                "type": "success",
                "message": "Sub1A available for submergence tolerance introgression",
            })
        
        # Check for missing important markers
        pita_marker = next((m for m in markers if m["id"] == "Pi-ta"), None)
        if pita_marker and pita_marker["present_count"] == 0:
            marker_notes.append({
                "type": "warning",
                "message": "Consider adding Pi-ta donor for blast resistance",
            })
        
        recommendations.append({
            "type": "markers",
            "title": "Marker-Assisted Selection Notes",
            "notes": marker_notes,
        })
        
        return recommendations
    
    def get_traits(self) -> List[Dict[str, Any]]:
        """Get all trait definitions."""
        return COMPARISON_TRAITS
    
    def get_markers(self, crop: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get marker definitions, optionally filtered by crop."""
        if crop:
            return [m for m in MARKER_DEFINITIONS if m["crop"].lower() == crop.lower()]
        return MARKER_DEFINITIONS
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get overall statistics."""
        entries = list(self.germplasm_db.values())
        species_counts = {}
        status_counts = {}
        
        for entry in entries:
            species = entry["species"]
            status = entry["status"]
            species_counts[species] = species_counts.get(species, 0) + 1
            status_counts[status] = status_counts.get(status, 0) + 1
        
        return {
            "total_entries": len(entries),
            "by_species": species_counts,
            "by_status": status_counts,
            "total_traits": len(COMPARISON_TRAITS),
            "total_markers": len(MARKER_DEFINITIONS),
        }


# Singleton instance
_service: Optional[GermplasmComparisonService] = None


def get_germplasm_comparison_service() -> GermplasmComparisonService:
    """Get or create the germplasm comparison service instance."""
    global _service
    if _service is None:
        _service = GermplasmComparisonService()
    return _service
