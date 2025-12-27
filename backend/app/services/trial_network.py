"""
Trial Network Service

Multi-environment trial coordination and analysis.
"""

from typing import Optional
from datetime import datetime


class TrialNetworkService:
    """Service for managing trial networks across multiple sites."""
    
    def __init__(self):
        self._sites = self._generate_demo_sites()
        self._germplasm = self._generate_demo_germplasm()
        self._performance = self._generate_demo_performance()
    
    def _generate_demo_sites(self) -> list:
        """Generate demo trial sites."""
        return [
            {"id": "site-1", "name": "IRRI Los Baños", "location": "Laguna", "country": "Philippines", 
             "coordinates": {"lat": 14.17, "lng": 121.25}, "trials": 8, "germplasm": 450, 
             "status": "active", "season": "2024-25", "lead": "Dr. Maria Santos", "region": "Asia"},
            {"id": "site-2", "name": "CIMMYT El Batán", "location": "Texcoco", "country": "Mexico",
             "coordinates": {"lat": 19.52, "lng": -98.84}, "trials": 6, "germplasm": 380,
             "status": "active", "season": "2024-25", "lead": "Dr. Carlos Rodriguez", "region": "Americas"},
            {"id": "site-3", "name": "ICRISAT Patancheru", "location": "Hyderabad", "country": "India",
             "coordinates": {"lat": 17.51, "lng": 78.27}, "trials": 5, "germplasm": 290,
             "status": "active", "season": "2024-25", "lead": "Dr. Priya Sharma", "region": "Asia"},
            {"id": "site-4", "name": "AfricaRice Ibadan", "location": "Oyo State", "country": "Nigeria",
             "coordinates": {"lat": 7.38, "lng": 3.94}, "trials": 4, "germplasm": 210,
             "status": "active", "season": "2024-25", "lead": "Dr. Adebayo Okonkwo", "region": "Africa"},
            {"id": "site-5", "name": "CIAT Palmira", "location": "Valle del Cauca", "country": "Colombia",
             "coordinates": {"lat": 3.51, "lng": -76.35}, "trials": 3, "germplasm": 180,
             "status": "completed", "season": "2024-25", "lead": "Dr. Ana Martinez", "region": "Americas"},
            {"id": "site-6", "name": "EMBRAPA Goiânia", "location": "Goiás", "country": "Brazil",
             "coordinates": {"lat": -16.68, "lng": -49.26}, "trials": 4, "germplasm": 220,
             "status": "active", "season": "2024-25", "lead": "Dr. Paulo Silva", "region": "Americas"},
        ]

    def _generate_demo_germplasm(self) -> list:
        """Generate demo shared germplasm."""
        return [
            {"id": "germ-1", "name": "IR64-Sub1", "sites": 18, "performance": "High yield, submergence tolerant", "crop": "Rice", "type": "Improved"},
            {"id": "germ-2", "name": "NERICA-L19", "sites": 15, "performance": "Drought tolerant, early maturity", "crop": "Rice", "type": "Improved"},
            {"id": "germ-3", "name": "Swarna-Sub1", "sites": 14, "performance": "Popular variety, flood tolerant", "crop": "Rice", "type": "Improved"},
            {"id": "germ-4", "name": "BRRI dhan52", "sites": 12, "performance": "Salt tolerant, good grain quality", "crop": "Rice", "type": "Improved"},
            {"id": "germ-5", "name": "Sahbhagi Dhan", "sites": 11, "performance": "Drought tolerant, upland adapted", "crop": "Rice", "type": "Improved"},
            {"id": "germ-6", "name": "HD-2967", "sites": 10, "performance": "High yield, rust resistant", "crop": "Wheat", "type": "Improved"},
            {"id": "germ-7", "name": "DKC 9144", "sites": 9, "performance": "Drought tolerant, high yield", "crop": "Maize", "type": "Hybrid"},
            {"id": "germ-8", "name": "ICGV 91114", "sites": 8, "performance": "Aflatoxin resistant, drought tolerant", "crop": "Groundnut", "type": "Improved"},
        ]
    
    def _generate_demo_performance(self) -> list:
        """Generate demo network performance data."""
        return [
            {"trait": "Yield (t/ha)", "mean": 5.8, "best": 7.2, "worst": 3.9, "cv": 12.4, "n_sites": 24},
            {"trait": "Days to Maturity", "mean": 125, "best": 118, "worst": 138, "cv": 8.2, "n_sites": 24},
            {"trait": "Plant Height (cm)", "mean": 98, "best": 85, "worst": 115, "cv": 15.1, "n_sites": 24},
            {"trait": "Disease Score (1-9)", "mean": 3.2, "best": 1.5, "worst": 5.8, "cv": 28.6, "n_sites": 20},
            {"trait": "Grain Quality Score", "mean": 7.5, "best": 9.0, "worst": 5.5, "cv": 10.2, "n_sites": 18},
            {"trait": "Drought Tolerance", "mean": 6.8, "best": 8.5, "worst": 4.2, "cv": 18.5, "n_sites": 15},
        ]
    
    def get_sites(self, season: Optional[str] = None, status: Optional[str] = None, 
                  country: Optional[str] = None, region: Optional[str] = None) -> list:
        """Get trial sites with optional filters."""
        sites = self._sites.copy()
        if season:
            sites = [s for s in sites if s["season"] == season]
        if status:
            sites = [s for s in sites if s["status"] == status]
        if country:
            sites = [s for s in sites if s["country"].lower() == country.lower()]
        if region:
            sites = [s for s in sites if s["region"].lower() == region.lower()]
        return sites
    
    def get_site(self, site_id: str) -> Optional[dict]:
        """Get a specific site by ID."""
        for site in self._sites:
            if site["id"] == site_id:
                return site
        return None
    
    def get_statistics(self, season: Optional[str] = None) -> dict:
        """Get network statistics."""
        sites = self.get_sites(season=season)
        countries = set(s["country"] for s in sites)
        return {
            "total_sites": len(sites),
            "active_trials": sum(s["trials"] for s in sites if s["status"] == "active"),
            "countries": len(countries),
            "germplasm_entries": sum(s["germplasm"] for s in sites),
            "collaborators": len(sites) * 4,  # Estimate
            "by_status": {
                "active": len([s for s in sites if s["status"] == "active"]),
                "completed": len([s for s in sites if s["status"] == "completed"]),
                "planned": len([s for s in sites if s["status"] == "planned"]),
            },
            "by_region": {
                "Asia": len([s for s in sites if s["region"] == "Asia"]),
                "Africa": len([s for s in sites if s["region"] == "Africa"]),
                "Americas": len([s for s in sites if s["region"] == "Americas"]),
            }
        }

    def get_shared_germplasm(self, min_sites: int = 1, crop: Optional[str] = None) -> list:
        """Get germplasm shared across multiple sites."""
        germplasm = self._germplasm.copy()
        if min_sites > 1:
            germplasm = [g for g in germplasm if g["sites"] >= min_sites]
        if crop:
            germplasm = [g for g in germplasm if g["crop"].lower() == crop.lower()]
        return sorted(germplasm, key=lambda x: x["sites"], reverse=True)
    
    def get_network_performance(self, trait: Optional[str] = None) -> list:
        """Get network-wide performance metrics."""
        performance = self._performance.copy()
        if trait:
            performance = [p for p in performance if trait.lower() in p["trait"].lower()]
        return performance
    
    def get_site_comparison(self, site_ids: list) -> dict:
        """Compare performance across selected sites."""
        sites = [s for s in self._sites if s["id"] in site_ids]
        if not sites:
            return {"sites": [], "comparison": []}
        
        return {
            "sites": sites,
            "comparison": [
                {"metric": "Total Trials", "values": {s["id"]: s["trials"] for s in sites}},
                {"metric": "Germplasm Entries", "values": {s["id"]: s["germplasm"] for s in sites}},
                {"metric": "Status", "values": {s["id"]: s["status"] for s in sites}},
            ]
        }
    
    def get_countries(self) -> list:
        """Get list of countries with trial sites."""
        countries = {}
        for site in self._sites:
            country = site["country"]
            if country not in countries:
                countries[country] = {"name": country, "sites": 0, "trials": 0, "region": site["region"]}
            countries[country]["sites"] += 1
            countries[country]["trials"] += site["trials"]
        return list(countries.values())
    
    def get_seasons(self) -> list:
        """Get available seasons."""
        return [
            {"id": "2024-25", "name": "2024-25", "status": "active"},
            {"id": "2023-24", "name": "2023-24", "status": "completed"},
            {"id": "2022-23", "name": "2022-23", "status": "completed"},
            {"id": "2021-22", "name": "2021-22", "status": "archived"},
        ]


# Singleton instance
trial_network_service = TrialNetworkService()
