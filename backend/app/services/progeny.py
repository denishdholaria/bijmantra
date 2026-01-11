"""
Progeny Service
Manage offspring and descendants of germplasm entries
"""

from typing import List, Dict, Any, Optional


class ProgenyService:
    """Service for managing progeny data"""

    def __init__(self):
        # In-memory storage (would be database in production)
        self.parents: Dict[str, Dict[str, Any]] = {}
        self._init_demo_data()

    def _init_demo_data(self):
        """Initialize with demo progeny data"""
        demo_data = [
            {
                "id": "parent-001",
                "germplasm_id": "g001",
                "germplasm_name": "IR64",
                "parent_type": "FEMALE",
                "species": "Oryza sativa",
                "generation": "Elite",
                "progeny": [
                    {"germplasm_id": "g010", "germplasm_name": "IR64-NIL-1", "parent_type": "FEMALE", "generation": "F1", "cross_year": 2022},
                    {"germplasm_id": "g011", "germplasm_name": "IR64-NIL-2", "parent_type": "FEMALE", "generation": "F1", "cross_year": 2022},
                    {"germplasm_id": "g012", "germplasm_name": "IR64 × Azucena F1", "parent_type": "FEMALE", "generation": "F1", "cross_year": 2023},
                    {"germplasm_id": "g019", "germplasm_name": "IR64-Sub1", "parent_type": "FEMALE", "generation": "BC3F4", "cross_year": 2020},
                    {"germplasm_id": "g020", "germplasm_name": "IR64-Xa21", "parent_type": "FEMALE", "generation": "BC2F5", "cross_year": 2019},
                ],
            },
            {
                "id": "parent-002",
                "germplasm_id": "g002",
                "germplasm_name": "Nipponbare",
                "parent_type": "MALE",
                "species": "Oryza sativa",
                "generation": "Reference",
                "progeny": [
                    {"germplasm_id": "g013", "germplasm_name": "Nip × Kas RIL-1", "parent_type": "MALE", "generation": "RIL", "cross_year": 2018},
                    {"germplasm_id": "g014", "germplasm_name": "Nip × Kas RIL-2", "parent_type": "MALE", "generation": "RIL", "cross_year": 2018},
                    {"germplasm_id": "g021", "germplasm_name": "Nip × 93-11 F2", "parent_type": "MALE", "generation": "F2", "cross_year": 2021},
                ],
            },
            {
                "id": "parent-003",
                "germplasm_id": "g003",
                "germplasm_name": "Kasalath",
                "parent_type": "FEMALE",
                "species": "Oryza sativa",
                "generation": "Landrace",
                "progeny": [
                    {"germplasm_id": "g015", "germplasm_name": "Kas-Derived-1", "parent_type": "FEMALE", "generation": "F6", "cross_year": 2019},
                    {"germplasm_id": "g016", "germplasm_name": "Kas-Derived-2", "parent_type": "FEMALE", "generation": "F6", "cross_year": 2019},
                    {"germplasm_id": "g017", "germplasm_name": "Kas-Derived-3", "parent_type": "FEMALE", "generation": "F5", "cross_year": 2020},
                    {"germplasm_id": "g018", "germplasm_name": "Kas-Derived-4", "parent_type": "FEMALE", "generation": "F5", "cross_year": 2020},
                ],
            },
            {
                "id": "parent-004",
                "germplasm_id": "g004",
                "germplasm_name": "Swarna",
                "parent_type": "FEMALE",
                "species": "Oryza sativa",
                "generation": "Elite",
                "progeny": [
                    {"germplasm_id": "g022", "germplasm_name": "Swarna-Sub1", "parent_type": "FEMALE", "generation": "BC3F4", "cross_year": 2008},
                    {"germplasm_id": "g023", "germplasm_name": "Swarna × IR64 F1", "parent_type": "FEMALE", "generation": "F1", "cross_year": 2022},
                    {"germplasm_id": "g024", "germplasm_name": "Swarna-Saltol", "parent_type": "FEMALE", "generation": "BC2F5", "cross_year": 2015},
                ],
            },
            {
                "id": "parent-005",
                "germplasm_id": "g005",
                "germplasm_name": "FR13A",
                "parent_type": "MALE",
                "species": "Oryza sativa",
                "generation": "Donor",
                "progeny": [
                    {"germplasm_id": "g025", "germplasm_name": "FR13A × IR64 BC1", "parent_type": "MALE", "generation": "BC1F1", "cross_year": 2005},
                    {"germplasm_id": "g026", "germplasm_name": "FR13A × Swarna BC1", "parent_type": "MALE", "generation": "BC1F1", "cross_year": 2006},
                ],
            },
            {
                "id": "parent-006",
                "germplasm_id": "g006",
                "germplasm_name": "HD2967",
                "parent_type": "FEMALE",
                "species": "Triticum aestivum",
                "generation": "Elite",
                "progeny": [
                    {"germplasm_id": "g027", "germplasm_name": "HD2967 × PBW343 F1", "parent_type": "FEMALE", "generation": "F1", "cross_year": 2021},
                    {"germplasm_id": "g028", "germplasm_name": "HD2967-Lr24", "parent_type": "FEMALE", "generation": "BC2F4", "cross_year": 2018},
                    {"germplasm_id": "g029", "germplasm_name": "HD2967-Heat", "parent_type": "FEMALE", "generation": "F5", "cross_year": 2020},
                ],
            },
        ]

        for parent in demo_data:
            self.parents[parent["id"]] = parent

    def list_parents(
        self,
        parent_type: Optional[str] = None,
        species: Optional[str] = None,
        search: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """List parents with their progeny"""
        results = list(self.parents.values())

        # Apply filters
        if parent_type:
            results = [p for p in results if p.get("parent_type") == parent_type]
        if species:
            results = [p for p in results if species.lower() in p.get("species", "").lower()]
        if search:
            search_lower = search.lower()
            results = [p for p in results if 
                search_lower in p.get("germplasm_name", "").lower() or
                any(search_lower in pr.get("germplasm_name", "").lower() for pr in p.get("progeny", []))
            ]

        return results

    def get_parent(self, parent_id: str) -> Optional[Dict[str, Any]]:
        """Get a single parent with progeny"""
        return self.parents.get(parent_id)

    def get_progeny_by_germplasm(self, germplasm_id: str) -> Optional[Dict[str, Any]]:
        """Get progeny for a specific germplasm"""
        for parent in self.parents.values():
            if parent.get("germplasm_id") == germplasm_id:
                return parent
        return None

    def get_statistics(self) -> Dict[str, Any]:
        """Get progeny statistics"""
        parents_list = list(self.parents.values())
        total_progeny = sum(len(p.get("progeny", [])) for p in parents_list)

        # Count by parent type
        by_type = {}
        for p in parents_list:
            ptype = p.get("parent_type", "UNKNOWN")
            by_type[ptype] = by_type.get(ptype, 0) + 1

        # Count by species
        by_species = {}
        for p in parents_list:
            species = p.get("species", "Unknown")
            by_species[species] = by_species.get(species, 0) + 1

        # Find parent with most progeny
        max_progeny_parent = max(parents_list, key=lambda x: len(x.get("progeny", []))) if parents_list else None

        return {
            "total_parents": len(parents_list),
            "total_progeny": total_progeny,
            "avg_offspring": round(total_progeny / len(parents_list), 1) if parents_list else 0,
            "max_offspring": len(max_progeny_parent.get("progeny", [])) if max_progeny_parent else 0,
            "max_offspring_parent": max_progeny_parent.get("germplasm_name") if max_progeny_parent else None,
            "by_parent_type": by_type,
            "by_species": by_species,
        }

    def get_parent_types(self) -> List[Dict[str, str]]:
        """Get available parent types"""
        return [
            {"value": "FEMALE", "label": "Female (♀)", "description": "Seed parent"},
            {"value": "MALE", "label": "Male (♂)", "description": "Pollen parent"},
            {"value": "SELF", "label": "Self (⟳)", "description": "Self-pollinated"},
            {"value": "POPULATION", "label": "Population (👥)", "description": "Population cross"},
        ]

    def get_lineage_tree(self, germplasm_id: str, depth: int = 3) -> Dict[str, Any]:
        """Get lineage tree for a germplasm"""
        parent = self.get_progeny_by_germplasm(germplasm_id)
        if not parent:
            return {"error": f"Germplasm {germplasm_id} not found"}

        tree = {
            "id": parent["germplasm_id"],
            "name": parent["germplasm_name"],
            "type": "parent",
            "children": []
        }

        for progeny in parent.get("progeny", []):
            child = {
                "id": progeny["germplasm_id"],
                "name": progeny["germplasm_name"],
                "type": "progeny",
                "generation": progeny.get("generation"),
                "cross_year": progeny.get("cross_year"),
                "children": []
            }
            # Could recursively get children if depth > 1
            tree["children"].append(child)

        return tree


# Singleton instance
progeny_service = ProgenyService()
