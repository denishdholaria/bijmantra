"""
Germplasm Search Service

Advanced germplasm search and discovery.
"""

from typing import Optional, List


class GermplasmSearchService:
    """Service for advanced germplasm search."""
    
    def __init__(self):
        self._germplasm = self._generate_demo_germplasm()
    
    def _generate_demo_germplasm(self) -> list:
        """Generate demo germplasm data."""
        return [
            {"id": "germ-1", "name": "IR64", "accession": "IRGC-66970", "species": "Oryza sativa", "subspecies": "indica", "origin": "Philippines", "traits": ["High yield", "Good quality", "Semi-dwarf"], "status": "Active", "collection": "IRRI", "year": 1985},
            {"id": "germ-2", "name": "Swarna", "accession": "IRGC-45678", "species": "Oryza sativa", "subspecies": "indica", "origin": "India", "traits": ["High yield", "Wide adaptation", "Long duration"], "status": "Active", "collection": "IRRI", "year": 1979},
            {"id": "germ-3", "name": "Nipponbare", "accession": "IRGC-12345", "species": "Oryza sativa", "subspecies": "japonica", "origin": "Japan", "traits": ["Reference genome", "Temperate adapted"], "status": "Active", "collection": "NIAS", "year": 1963},
            {"id": "germ-4", "name": "Kasalath", "accession": "IRGC-23456", "species": "Oryza sativa", "subspecies": "aus", "origin": "India", "traits": ["Drought tolerance", "Deep roots", "Phosphorus uptake"], "status": "Active", "collection": "IRRI", "year": 1978},
            {"id": "germ-5", "name": "N22", "accession": "IRGC-34567", "species": "Oryza sativa", "subspecies": "aus", "origin": "India", "traits": ["Heat tolerance", "Drought tolerance", "Early maturity"], "status": "Active", "collection": "IRRI", "year": 1975},
            {"id": "germ-6", "name": "FR13A", "accession": "IRGC-56789", "species": "Oryza sativa", "subspecies": "indica", "origin": "India", "traits": ["Submergence tolerance", "SUB1 gene"], "status": "Active", "collection": "IRRI", "year": 1970},
            {"id": "germ-7", "name": "Pokkali", "accession": "IRGC-67890", "species": "Oryza sativa", "subspecies": "indica", "origin": "India", "traits": ["Salt tolerance", "Coastal adapted"], "status": "Active", "collection": "IRRI", "year": 1965},
            {"id": "germ-8", "name": "Moroberekan", "accession": "IRGC-78901", "species": "Oryza sativa", "subspecies": "japonica", "origin": "Guinea", "traits": ["Blast resistance", "Upland adapted"], "status": "Active", "collection": "AfricaRice", "year": 1960},
            {"id": "germ-9", "name": "Azucena", "accession": "IRGC-89012", "species": "Oryza sativa", "subspecies": "japonica", "origin": "Philippines", "traits": ["Drought tolerance", "Deep roots", "Upland"], "status": "Active", "collection": "IRRI", "year": 1955},
            {"id": "germ-10", "name": "Bala", "accession": "IRGC-90123", "species": "Oryza sativa", "subspecies": "indica", "origin": "India", "traits": ["Drought tolerance", "Early maturity"], "status": "Active", "collection": "IRRI", "year": 1968},
        ]

    def search(self, query: Optional[str] = None, species: Optional[str] = None,
               origin: Optional[str] = None, collection: Optional[str] = None,
               trait: Optional[str] = None, limit: int = 50) -> list:
        """Search germplasm with filters."""
        results = self._germplasm.copy()
        
        if query:
            q = query.lower()
            results = [g for g in results if q in g["name"].lower() or q in g["accession"].lower() or any(q in t.lower() for t in g["traits"])]
        
        if species:
            results = [g for g in results if species.lower() in g["species"].lower() or species.lower() in g.get("subspecies", "").lower()]
        
        if origin:
            results = [g for g in results if g["origin"].lower() == origin.lower()]
        
        if collection:
            results = [g for g in results if g["collection"].lower() == collection.lower()]
        
        if trait:
            results = [g for g in results if any(trait.lower() in t.lower() for t in g["traits"])]
        
        return results[:limit]
    
    def get_by_id(self, germplasm_id: str) -> Optional[dict]:
        """Get germplasm by ID."""
        for g in self._germplasm:
            if g["id"] == germplasm_id:
                return g
        return None
    
    def get_filters(self) -> dict:
        """Get available filter options."""
        species = set()
        origins = set()
        collections = set()
        traits = set()
        
        for g in self._germplasm:
            species.add(g["species"])
            if g.get("subspecies"):
                species.add(f"{g['species']} {g['subspecies']}")
            origins.add(g["origin"])
            collections.add(g["collection"])
            for t in g["traits"]:
                traits.add(t)
        
        return {
            "species": sorted(list(species)),
            "origins": sorted(list(origins)),
            "collections": sorted(list(collections)),
            "traits": sorted(list(traits)),
        }
    
    def get_statistics(self) -> dict:
        """Get search statistics."""
        return {
            "total_germplasm": len(self._germplasm),
            "species_count": len(set(g["species"] for g in self._germplasm)),
            "origin_count": len(set(g["origin"] for g in self._germplasm)),
            "collection_count": len(set(g["collection"] for g in self._germplasm)),
        }


# Singleton instance
germplasm_search_service = GermplasmSearchService()
