"""
Crop Calendar Service for Plant Breeding
Planting schedules, growth stages, and activity planning

Features:
- Crop growth stage tracking
- Planting window recommendations
- Activity scheduling (sowing, transplanting, harvest)
- Growing degree days (GDD) calculation
- Season planning
"""

from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime, date, timedelta
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class GrowthStage(str, Enum):
    GERMINATION = "germination"
    SEEDLING = "seedling"
    VEGETATIVE = "vegetative"
    FLOWERING = "flowering"
    GRAIN_FILLING = "grain_filling"
    MATURITY = "maturity"
    HARVEST = "harvest"


class ActivityType(str, Enum):
    SOWING = "sowing"
    TRANSPLANTING = "transplanting"
    FERTILIZATION = "fertilization"
    IRRIGATION = "irrigation"
    PEST_CONTROL = "pest_control"
    OBSERVATION = "observation"
    HARVEST = "harvest"
    DATA_COLLECTION = "data_collection"


@dataclass
class CropProfile:
    """Crop growth profile"""
    crop_id: str
    name: str
    species: str
    days_to_maturity: int
    base_temperature: float  # °C for GDD
    optimal_temp_min: float
    optimal_temp_max: float
    growth_stages: Dict[str, int]  # stage -> days from sowing
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "crop_id": self.crop_id,
            "name": self.name,
            "species": self.species,
            "days_to_maturity": self.days_to_maturity,
            "base_temperature_c": self.base_temperature,
            "optimal_temp_range_c": [self.optimal_temp_min, self.optimal_temp_max],
            "growth_stages": self.growth_stages,
        }


@dataclass
class PlantingEvent:
    """Planting event record"""
    event_id: str
    crop_id: str
    trial_id: str
    sowing_date: date
    expected_harvest: date
    location: str
    area_hectares: float
    notes: str = ""
    actual_harvest: Optional[date] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "crop_id": self.crop_id,
            "trial_id": self.trial_id,
            "sowing_date": self.sowing_date.isoformat(),
            "expected_harvest": self.expected_harvest.isoformat(),
            "actual_harvest": self.actual_harvest.isoformat() if self.actual_harvest else None,
            "location": self.location,
            "area_hectares": self.area_hectares,
            "notes": self.notes,
            "days_to_harvest": (self.expected_harvest - self.sowing_date).days,
        }


@dataclass
class ScheduledActivity:
    """Scheduled field activity"""
    activity_id: str
    event_id: str
    activity_type: ActivityType
    scheduled_date: date
    description: str
    completed: bool = False
    completed_date: Optional[date] = None
    notes: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "activity_id": self.activity_id,
            "event_id": self.event_id,
            "activity_type": self.activity_type.value,
            "scheduled_date": self.scheduled_date.isoformat(),
            "description": self.description,
            "completed": self.completed,
            "completed_date": self.completed_date.isoformat() if self.completed_date else None,
            "notes": self.notes,
        }


class CropCalendarService:
    """
    Crop calendar and activity planning
    """
    
    def __init__(self):
        self.crop_profiles: Dict[str, CropProfile] = {}
        self.planting_events: Dict[str, PlantingEvent] = {}
        self.activities: Dict[str, ScheduledActivity] = {}
        self._event_counter = 0
        self._activity_counter = 0
        
        # Initialize default crop profiles
        self._init_default_profiles()
    
    def _init_default_profiles(self):
        """Initialize common crop profiles"""
        defaults = [
            CropProfile(
                crop_id="rice_short",
                name="Rice (Short Duration)",
                species="Oryza sativa",
                days_to_maturity=110,
                base_temperature=10.0,
                optimal_temp_min=25.0,
                optimal_temp_max=35.0,
                growth_stages={
                    "germination": 7,
                    "seedling": 21,
                    "vegetative": 45,
                    "flowering": 70,
                    "grain_filling": 90,
                    "maturity": 110,
                },
            ),
            CropProfile(
                crop_id="rice_medium",
                name="Rice (Medium Duration)",
                species="Oryza sativa",
                days_to_maturity=135,
                base_temperature=10.0,
                optimal_temp_min=25.0,
                optimal_temp_max=35.0,
                growth_stages={
                    "germination": 7,
                    "seedling": 25,
                    "vegetative": 55,
                    "flowering": 85,
                    "grain_filling": 115,
                    "maturity": 135,
                },
            ),
            CropProfile(
                crop_id="wheat",
                name="Wheat",
                species="Triticum aestivum",
                days_to_maturity=120,
                base_temperature=0.0,
                optimal_temp_min=15.0,
                optimal_temp_max=25.0,
                growth_stages={
                    "germination": 10,
                    "seedling": 25,
                    "vegetative": 50,
                    "flowering": 75,
                    "grain_filling": 100,
                    "maturity": 120,
                },
            ),
            CropProfile(
                crop_id="maize",
                name="Maize",
                species="Zea mays",
                days_to_maturity=100,
                base_temperature=10.0,
                optimal_temp_min=20.0,
                optimal_temp_max=30.0,
                growth_stages={
                    "germination": 7,
                    "seedling": 20,
                    "vegetative": 45,
                    "flowering": 60,
                    "grain_filling": 85,
                    "maturity": 100,
                },
            ),
            CropProfile(
                crop_id="soybean",
                name="Soybean",
                species="Glycine max",
                days_to_maturity=110,
                base_temperature=10.0,
                optimal_temp_min=20.0,
                optimal_temp_max=30.0,
                growth_stages={
                    "germination": 7,
                    "seedling": 20,
                    "vegetative": 40,
                    "flowering": 55,
                    "grain_filling": 90,
                    "maturity": 110,
                },
            ),
        ]
        
        for profile in defaults:
            self.crop_profiles[profile.crop_id] = profile
    
    def register_crop(
        self,
        crop_id: str,
        name: str,
        species: str,
        days_to_maturity: int,
        base_temperature: float,
        optimal_temp_min: float,
        optimal_temp_max: float,
        growth_stages: Dict[str, int]
    ) -> CropProfile:
        """Register a new crop profile"""
        profile = CropProfile(
            crop_id=crop_id,
            name=name,
            species=species,
            days_to_maturity=days_to_maturity,
            base_temperature=base_temperature,
            optimal_temp_min=optimal_temp_min,
            optimal_temp_max=optimal_temp_max,
            growth_stages=growth_stages,
        )
        self.crop_profiles[crop_id] = profile
        return profile
    
    def create_planting_event(
        self,
        crop_id: str,
        trial_id: str,
        sowing_date: str,
        location: str,
        area_hectares: float,
        notes: str = ""
    ) -> PlantingEvent:
        """
        Create a planting event
        
        Automatically calculates expected harvest date based on crop profile.
        """
        if crop_id not in self.crop_profiles:
            raise ValueError(f"Crop profile {crop_id} not found")
        
        profile = self.crop_profiles[crop_id]
        sowing = date.fromisoformat(sowing_date)
        expected_harvest = sowing + timedelta(days=profile.days_to_maturity)
        
        self._event_counter += 1
        event_id = f"PE-{self._event_counter:06d}"
        
        event = PlantingEvent(
            event_id=event_id,
            crop_id=crop_id,
            trial_id=trial_id,
            sowing_date=sowing,
            expected_harvest=expected_harvest,
            location=location,
            area_hectares=area_hectares,
            notes=notes,
        )
        
        self.planting_events[event_id] = event
        
        # Auto-generate activities
        self._generate_activities(event, profile)
        
        return event
    
    def _generate_activities(self, event: PlantingEvent, profile: CropProfile):
        """Generate scheduled activities for a planting event"""
        activities = [
            (ActivityType.SOWING, 0, "Sowing/Planting"),
            (ActivityType.OBSERVATION, 7, "Germination check"),
            (ActivityType.FERTILIZATION, 21, "First fertilizer application"),
            (ActivityType.OBSERVATION, 30, "Vegetative stage observation"),
            (ActivityType.IRRIGATION, 35, "Irrigation check"),
            (ActivityType.PEST_CONTROL, 45, "Pest/disease scouting"),
            (ActivityType.DATA_COLLECTION, 50, "Mid-season data collection"),
            (ActivityType.OBSERVATION, profile.growth_stages.get("flowering", 70), "Flowering observation"),
            (ActivityType.DATA_COLLECTION, profile.growth_stages.get("maturity", 100) - 10, "Pre-harvest data collection"),
            (ActivityType.HARVEST, profile.days_to_maturity, "Harvest"),
        ]
        
        for activity_type, days_offset, description in activities:
            self._activity_counter += 1
            activity_id = f"ACT-{self._activity_counter:06d}"
            
            activity = ScheduledActivity(
                activity_id=activity_id,
                event_id=event.event_id,
                activity_type=activity_type,
                scheduled_date=event.sowing_date + timedelta(days=days_offset),
                description=description,
            )
            self.activities[activity_id] = activity
    
    def get_growth_stage(
        self,
        event_id: str,
        check_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get current growth stage for a planting event
        """
        if event_id not in self.planting_events:
            raise ValueError(f"Planting event {event_id} not found")
        
        event = self.planting_events[event_id]
        profile = self.crop_profiles[event.crop_id]
        
        check = date.fromisoformat(check_date) if check_date else date.today()
        days_after_sowing = (check - event.sowing_date).days
        
        if days_after_sowing < 0:
            current_stage = "not_planted"
            progress = 0
        else:
            current_stage = "maturity"
            for stage, days in sorted(profile.growth_stages.items(), key=lambda x: x[1]):
                if days_after_sowing < days:
                    current_stage = stage
                    break
            
            progress = min(100, days_after_sowing / profile.days_to_maturity * 100)
        
        return {
            "event_id": event_id,
            "crop": profile.name,
            "sowing_date": event.sowing_date.isoformat(),
            "check_date": check.isoformat(),
            "days_after_sowing": days_after_sowing,
            "current_stage": current_stage,
            "progress_percent": round(progress, 1),
            "days_to_harvest": max(0, (event.expected_harvest - check).days),
            "expected_harvest": event.expected_harvest.isoformat(),
        }
    
    def calculate_gdd(
        self,
        crop_id: str,
        daily_temps: List[Dict[str, float]]
    ) -> Dict[str, Any]:
        """
        Calculate Growing Degree Days (GDD)
        
        GDD = max(0, (Tmax + Tmin)/2 - Tbase)
        
        Args:
            crop_id: Crop profile ID
            daily_temps: List of {date, temp_max, temp_min}
        """
        if crop_id not in self.crop_profiles:
            raise ValueError(f"Crop profile {crop_id} not found")
        
        profile = self.crop_profiles[crop_id]
        base_temp = profile.base_temperature
        
        total_gdd = 0
        daily_gdd = []
        
        for day in daily_temps:
            avg_temp = (day["temp_max"] + day["temp_min"]) / 2
            gdd = max(0, avg_temp - base_temp)
            total_gdd += gdd
            daily_gdd.append({
                "date": day.get("date", ""),
                "temp_max": day["temp_max"],
                "temp_min": day["temp_min"],
                "gdd": round(gdd, 1),
                "cumulative_gdd": round(total_gdd, 1),
            })
        
        return {
            "crop": profile.name,
            "base_temperature_c": base_temp,
            "total_gdd": round(total_gdd, 1),
            "days_counted": len(daily_temps),
            "daily_gdd": daily_gdd,
        }
    
    def get_upcoming_activities(
        self,
        days_ahead: int = 14,
        event_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get upcoming activities within specified days"""
        today = date.today()
        end_date = today + timedelta(days=days_ahead)
        
        upcoming = []
        for activity in self.activities.values():
            if activity.completed:
                continue
            if event_id and activity.event_id != event_id:
                continue
            if today <= activity.scheduled_date <= end_date:
                event = self.planting_events.get(activity.event_id)
                upcoming.append({
                    **activity.to_dict(),
                    "trial_id": event.trial_id if event else None,
                    "location": event.location if event else None,
                    "days_until": (activity.scheduled_date - today).days,
                })
        
        return sorted(upcoming, key=lambda x: x["scheduled_date"])
    
    def complete_activity(
        self,
        activity_id: str,
        notes: str = ""
    ) -> ScheduledActivity:
        """Mark an activity as completed"""
        if activity_id not in self.activities:
            raise ValueError(f"Activity {activity_id} not found")
        
        activity = self.activities[activity_id]
        activity.completed = True
        activity.completed_date = date.today()
        activity.notes = notes
        
        return activity
    
    def get_calendar_view(
        self,
        start_date: str,
        end_date: str
    ) -> Dict[str, Any]:
        """Get calendar view of all events and activities"""
        start = date.fromisoformat(start_date)
        end = date.fromisoformat(end_date)
        
        calendar = {}
        current = start
        while current <= end:
            calendar[current.isoformat()] = {
                "events": [],
                "activities": [],
            }
            current += timedelta(days=1)
        
        # Add planting events
        for event in self.planting_events.values():
            if start <= event.sowing_date <= end:
                date_key = event.sowing_date.isoformat()
                if date_key in calendar:
                    calendar[date_key]["events"].append({
                        "type": "sowing",
                        "event_id": event.event_id,
                        "crop_id": event.crop_id,
                        "trial_id": event.trial_id,
                    })
            
            if start <= event.expected_harvest <= end:
                date_key = event.expected_harvest.isoformat()
                if date_key in calendar:
                    calendar[date_key]["events"].append({
                        "type": "harvest",
                        "event_id": event.event_id,
                        "crop_id": event.crop_id,
                        "trial_id": event.trial_id,
                    })
        
        # Add activities
        for activity in self.activities.values():
            if start <= activity.scheduled_date <= end:
                date_key = activity.scheduled_date.isoformat()
                if date_key in calendar:
                    calendar[date_key]["activities"].append({
                        "activity_id": activity.activity_id,
                        "type": activity.activity_type.value,
                        "description": activity.description,
                        "completed": activity.completed,
                    })
        
        return {
            "start_date": start_date,
            "end_date": end_date,
            "calendar": calendar,
        }
    
    def list_crops(self) -> List[Dict[str, Any]]:
        """List all crop profiles"""
        return [p.to_dict() for p in self.crop_profiles.values()]
    
    def list_events(
        self,
        crop_id: Optional[str] = None,
        location: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """List planting events with optional filters"""
        result = []
        for event in self.planting_events.values():
            if crop_id and event.crop_id != crop_id:
                continue
            if location and event.location != location:
                continue
            result.append(event.to_dict())
        return result


# Singleton
_crop_calendar_service: Optional[CropCalendarService] = None


def get_crop_calendar_service() -> CropCalendarService:
    """Get or create crop calendar service singleton"""
    global _crop_calendar_service
    if _crop_calendar_service is None:
        _crop_calendar_service = CropCalendarService()
    return _crop_calendar_service
