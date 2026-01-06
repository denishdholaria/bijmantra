"""
Space Research Service

Provides data and calculations for interplanetary agriculture research.
Includes microgravity effects, radiation exposure, and controlled environment systems.
"""

from datetime import datetime, date, timedelta
from typing import Optional
import math
import random


class SpaceResearchService:
    """Service for space agriculture research data and calculations."""
    
    def __init__(self):
        self._experiments = {}
        self._crops = {}
        self._init_demo_data()
    
    def _init_demo_data(self):
        """Initialize demo data for space crops and experiments."""
        self._space_crops = [
            {
                "id": "SC001",
                "name": "Dwarf Wheat (Apogee)",
                "species": "Triticum aestivum",
                "space_heritage": "ISS Veggie, 2014-present",
                "growth_cycle_days": 62,
                "radiation_tolerance": "Moderate",
                "microgravity_adaptation": "Good",
                "caloric_yield": 3400,
                "notes": "NASA-developed dwarf variety for space",
            },
            {
                "id": "SC002",
                "name": "Red Romaine Lettuce",
                "species": "Lactuca sativa",
                "space_heritage": "ISS Veggie, 2015",
                "growth_cycle_days": 28,
                "radiation_tolerance": "Low",
                "microgravity_adaptation": "Excellent",
                "caloric_yield": 150,
                "notes": "First crop eaten in space (2015)",
            },
            {
                "id": "SC003",
                "name": "Mizuna",
                "species": "Brassica rapa var. nipposinica",
                "space_heritage": "ISS, 2020",
                "growth_cycle_days": 21,
                "radiation_tolerance": "Moderate",
                "microgravity_adaptation": "Excellent",
                "caloric_yield": 230,
                "notes": "Fast-growing Asian green",
            },
            {
                "id": "SC004",
                "name": "Radish",
                "species": "Raphanus sativus",
                "space_heritage": "ISS APH, 2020",
                "growth_cycle_days": 27,
                "radiation_tolerance": "Moderate",
                "microgravity_adaptation": "Good",
                "caloric_yield": 160,
                "notes": "Root crop successfully grown in space",
            },
            {
                "id": "SC005",
                "name": "Chile Pepper",
                "species": "Capsicum annuum",
                "space_heritage": "ISS APH, 2021",
                "growth_cycle_days": 120,
                "radiation_tolerance": "Moderate",
                "microgravity_adaptation": "Good",
                "caloric_yield": 400,
                "notes": "First fruit crop grown and eaten in space",
            },
            {
                "id": "SC006",
                "name": "Tomato (Red Robin)",
                "species": "Solanum lycopersicum",
                "space_heritage": "ISS, 2023",
                "growth_cycle_days": 90,
                "radiation_tolerance": "Moderate",
                "microgravity_adaptation": "Good",
                "caloric_yield": 180,
                "notes": "Dwarf determinate variety",
            },
        ]
        
        self._experiments = {
            "EXP001": {
                "id": "EXP001",
                "name": "Microgravity Wheat Growth Study",
                "status": "Active",
                "start_date": "2024-06-15",
                "crop": "Dwarf Wheat (Apogee)",
                "environment": "ISS Veggie",
                "parameters": {
                    "light_hours": 16,
                    "temperature_c": 22,
                    "co2_ppm": 1000,
                    "humidity_percent": 65,
                },
                "observations": 45,
            },
            "EXP002": {
                "id": "EXP002",
                "name": "Radiation Tolerance Screening",
                "status": "Completed",
                "start_date": "2024-01-10",
                "crop": "Multiple",
                "environment": "Ground Simulation",
                "parameters": {
                    "radiation_type": "Gamma",
                    "dose_gy": 0.5,
                    "duration_days": 30,
                },
                "observations": 120,
            },
        }
    
    def get_space_crops(self) -> list:
        """Get list of crops suitable for space agriculture."""
        return self._space_crops
    
    def get_space_crop(self, crop_id: str) -> Optional[dict]:
        """Get details of a specific space crop."""
        for crop in self._space_crops:
            if crop["id"] == crop_id:
                return crop
        return None

    def get_experiments(self, status: Optional[str] = None) -> list:
        """Get list of space agriculture experiments."""
        experiments = list(self._experiments.values())
        if status:
            experiments = [e for e in experiments if e["status"].lower() == status.lower()]
        return experiments
    
    def get_experiment(self, exp_id: str) -> Optional[dict]:
        """Get details of a specific experiment."""
        return self._experiments.get(exp_id)
    
    def calculate_radiation_exposure(
        self,
        mission_type: str,
        duration_days: int,
        shielding_gcm2: float = 20,
    ) -> dict:
        """
        Calculate estimated radiation exposure for a space mission.
        
        Args:
            mission_type: "LEO" (Low Earth Orbit), "lunar", "mars", "deep_space"
            duration_days: Mission duration in days
            shielding_gcm2: Shielding thickness in g/cm²
        """
        # Base radiation rates (mSv/day)
        base_rates = {
            "LEO": 0.5,  # ISS average
            "lunar": 1.0,  # Outside magnetosphere
            "mars": 0.7,  # Transit average
            "deep_space": 1.5,  # Galactic cosmic rays
        }
        
        base_rate = base_rates.get(mission_type.lower(), 0.5)
        
        # Shielding reduction factor (simplified model)
        shielding_factor = math.exp(-shielding_gcm2 / 30)
        effective_rate = base_rate * (0.3 + 0.7 * shielding_factor)
        
        total_dose = effective_rate * duration_days
        
        # Plant damage thresholds
        plant_effects = []
        if total_dose > 500:
            plant_effects.append("Severe growth inhibition likely")
        elif total_dose > 100:
            plant_effects.append("Moderate growth reduction expected")
        elif total_dose > 50:
            plant_effects.append("Minor effects on sensitive varieties")
        else:
            plant_effects.append("Minimal impact expected")
        
        return {
            "mission_type": mission_type,
            "duration_days": duration_days,
            "shielding_gcm2": shielding_gcm2,
            "daily_dose_msv": round(effective_rate, 3),
            "total_dose_msv": round(total_dose, 1),
            "plant_effects": plant_effects,
            "comparison": {
                "earth_annual": 2.4,
                "iss_annual": 182.5,
                "mars_transit": 300,
            },
        }
    
    def calculate_life_support_requirements(
        self,
        crew_size: int,
        mission_days: int,
        crop_area_m2: float,
    ) -> dict:
        """
        Calculate life support requirements for a space mission with crops.
        
        Args:
            crew_size: Number of crew members
            mission_days: Mission duration
            crop_area_m2: Growing area in square meters
        """
        # Daily requirements per person
        daily_o2_kg = 0.84
        daily_co2_kg = 1.0
        daily_water_kg = 2.5
        daily_food_kg = 1.8
        
        # Crop production estimates (per m² per day)
        crop_o2_production = 0.02  # kg O2/m²/day
        crop_co2_consumption = 0.025  # kg CO2/m²/day
        crop_water_recycling = 0.1  # kg water/m²/day
        crop_food_production = 0.015  # kg edible/m²/day
        
        # Calculate totals
        total_o2_needed = daily_o2_kg * crew_size * mission_days
        total_co2_produced = daily_co2_kg * crew_size * mission_days
        total_water_needed = daily_water_kg * crew_size * mission_days
        total_food_needed = daily_food_kg * crew_size * mission_days
        
        # Crop contributions
        crop_o2 = crop_o2_production * crop_area_m2 * mission_days
        crop_co2_absorbed = crop_co2_consumption * crop_area_m2 * mission_days
        crop_water = crop_water_recycling * crop_area_m2 * mission_days
        crop_food = crop_food_production * crop_area_m2 * mission_days
        
        return {
            "crew_size": crew_size,
            "mission_days": mission_days,
            "crop_area_m2": crop_area_m2,
            "requirements": {
                "oxygen_kg": round(total_o2_needed, 1),
                "water_kg": round(total_water_needed, 1),
                "food_kg": round(total_food_needed, 1),
            },
            "crop_contribution": {
                "oxygen_kg": round(crop_o2, 1),
                "oxygen_percent": round(crop_o2 / total_o2_needed * 100, 1),
                "co2_absorbed_kg": round(crop_co2_absorbed, 1),
                "co2_percent": round(crop_co2_absorbed / total_co2_produced * 100, 1),
                "water_recycled_kg": round(crop_water, 1),
                "water_percent": round(crop_water / total_water_needed * 100, 1),
                "food_kg": round(crop_food, 1),
                "food_percent": round(crop_food / total_food_needed * 100, 1),
            },
            "self_sufficiency_score": round(
                (crop_o2 / total_o2_needed + crop_food / total_food_needed) / 2 * 100, 1
            ),
        }
    
    def get_controlled_environment_params(self, crop_id: str) -> dict:
        """Get optimal controlled environment parameters for a space crop."""
        crop = self.get_space_crop(crop_id)
        if not crop:
            return {"error": "Crop not found"}
        
        # Default optimal parameters (would be crop-specific in production)
        params = {
            "crop": crop["name"],
            "light": {
                "photoperiod_hours": 16,
                "ppfd_umol": 400,
                "spectrum": "Red:Blue 4:1",
            },
            "atmosphere": {
                "co2_ppm": 1000,
                "o2_percent": 21,
                "humidity_percent": 65,
            },
            "temperature": {
                "day_c": 24,
                "night_c": 18,
            },
            "nutrients": {
                "ec_ms_cm": 1.8,
                "ph": 6.0,
                "solution": "Modified Hoagland",
            },
            "growth_medium": "Arcillite/Peat mix",
        }
        
        return params
    
    def get_mission_profiles(self) -> list:
        """Get predefined space mission profiles."""
        return [
            {
                "id": "ISS",
                "name": "International Space Station",
                "type": "LEO",
                "duration_days": 180,
                "distance_km": 400,
                "gravity_g": 0.0,
                "radiation_msv_day": 0.5,
                "current_crops": ["Lettuce", "Mizuna", "Radish"],
            },
            {
                "id": "LUNAR_GATEWAY",
                "name": "Lunar Gateway",
                "type": "lunar",
                "duration_days": 90,
                "distance_km": 384400,
                "gravity_g": 0.0,
                "radiation_msv_day": 1.0,
                "planned_crops": ["Lettuce", "Tomato"],
            },
            {
                "id": "MARS_TRANSIT",
                "name": "Mars Transit",
                "type": "mars",
                "duration_days": 260,
                "distance_km": 225000000,
                "gravity_g": 0.0,
                "radiation_msv_day": 0.7,
                "planned_crops": ["Wheat", "Soybean", "Potato"],
            },
            {
                "id": "MARS_SURFACE",
                "name": "Mars Surface Habitat",
                "type": "mars",
                "duration_days": 500,
                "distance_km": 225000000,
                "gravity_g": 0.38,
                "radiation_msv_day": 0.3,
                "planned_crops": ["Wheat", "Rice", "Potato", "Soybean", "Vegetables"],
            },
        ]


# Singleton instance
_space_service: Optional[SpaceResearchService] = None


def get_space_research_service() -> SpaceResearchService:
    """Get or create the space research service singleton."""
    global _space_service
    if _space_service is None:
        _space_service = SpaceResearchService()
    return _space_service
