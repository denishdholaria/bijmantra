"""
Field Environment Service
Soil profiles, input logs, irrigation, and field history management

Features:
- Soil profile management (texture, nutrients, pH)
- Input logging (fertilizers, pesticides, amendments)
- Water & irrigation tracking
- Field history and crop rotation
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, date, timezone
from dataclasses import dataclass, field
from enum import Enum
import uuid


class SoilTexture(str, Enum):
    """Soil texture classification"""
    CLAY = "clay"
    CLAY_LOAM = "clay_loam"
    LOAM = "loam"
    SANDY_LOAM = "sandy_loam"
    SANDY = "sandy"
    SILT = "silt"
    SILT_LOAM = "silt_loam"


class InputType(str, Enum):
    """Types of field inputs"""
    FERTILIZER = "fertilizer"
    PESTICIDE = "pesticide"
    HERBICIDE = "herbicide"
    FUNGICIDE = "fungicide"
    AMENDMENT = "amendment"
    SEED = "seed"
    WATER = "water"
    OTHER = "other"


class IrrigationType(str, Enum):
    """Irrigation methods"""
    DRIP = "drip"
    SPRINKLER = "sprinkler"
    FLOOD = "flood"
    FURROW = "furrow"
    CENTER_PIVOT = "center_pivot"
    RAINFED = "rainfed"


@dataclass
class SoilProfile:
    """Soil profile data"""
    id: str
    field_id: str
    sample_date: date
    depth_cm: int
    texture: SoilTexture
    ph: float
    organic_matter: float  # percentage
    nitrogen: float  # kg/ha
    phosphorus: float  # kg/ha
    potassium: float  # kg/ha
    calcium: Optional[float] = None
    magnesium: Optional[float] = None
    sulfur: Optional[float] = None
    cec: Optional[float] = None  # Cation Exchange Capacity
    ec: Optional[float] = None  # Electrical Conductivity
    bulk_density: Optional[float] = None
    water_holding_capacity: Optional[float] = None
    notes: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class InputLog:
    """Field input application record"""
    id: str
    field_id: str
    input_type: InputType
    product_name: str
    application_date: date
    quantity: float
    unit: str
    area_applied: float  # hectares
    method: str
    applicator: Optional[str] = None
    weather_conditions: Optional[str] = None
    cost: Optional[float] = None
    notes: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class IrrigationEvent:
    """Irrigation event record"""
    id: str
    field_id: str
    irrigation_type: IrrigationType
    event_date: date
    duration_hours: float
    water_volume: float  # cubic meters
    source: str  # well, canal, reservoir, etc.
    cost: Optional[float] = None
    notes: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class FieldHistory:
    """Field history entry (crop rotation, events)"""
    id: str
    field_id: str
    season: str  # e.g., "2024-Kharif", "2024-Rabi"
    crop: str
    variety: Optional[str] = None
    planting_date: Optional[date] = None
    harvest_date: Optional[date] = None
    yield_amount: Optional[float] = None
    yield_unit: str = "kg/ha"
    notes: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class FieldEnvironmentService:
    """
    Service for managing field environment data
    """

    def __init__(self):
        # In-memory storage (use database in production)
        self._soil_profiles: Dict[str, SoilProfile] = {}
        self._input_logs: Dict[str, InputLog] = {}
        self._irrigation_events: Dict[str, IrrigationEvent] = {}
        self._field_history: Dict[str, FieldHistory] = {}

        # Add sample data
        self._add_sample_data()

    def _add_sample_data(self):
        """Add sample data for demo"""
        # Sample soil profiles
        profiles = [
            SoilProfile(
                id="sp-001", field_id="field-001", sample_date=date(2024, 11, 15),
                depth_cm=30, texture=SoilTexture.LOAM, ph=6.8, organic_matter=2.4,
                nitrogen=45, phosphorus=32, potassium=180, calcium=1200, magnesium=180
            ),
            SoilProfile(
                id="sp-002", field_id="field-002", sample_date=date(2024, 11, 14),
                depth_cm=30, texture=SoilTexture.CLAY_LOAM, ph=7.2, organic_matter=2.1,
                nitrogen=38, phosphorus=28, potassium=165, calcium=1400, magnesium=200
            ),
        ]
        for p in profiles:
            self._soil_profiles[p.id] = p

        # Sample input logs
        inputs = [
            InputLog(
                id="inp-001", field_id="field-001", input_type=InputType.FERTILIZER,
                product_name="Urea (46-0-0)", application_date=date(2024, 11, 10),
                quantity=50, unit="kg", area_applied=2.5, method="broadcast"
            ),
            InputLog(
                id="inp-002", field_id="field-001", input_type=InputType.PESTICIDE,
                product_name="Chlorpyrifos 20EC", application_date=date(2024, 11, 5),
                quantity=2, unit="L", area_applied=2.5, method="foliar spray"
            ),
        ]
        for i in inputs:
            self._input_logs[i.id] = i

        # Sample irrigation
        irrigation = [
            IrrigationEvent(
                id="irr-001", field_id="field-001", irrigation_type=IrrigationType.DRIP,
                event_date=date(2024, 11, 12), duration_hours=4, water_volume=100,
                source="borewell"
            ),
        ]
        for ir in irrigation:
            self._irrigation_events[ir.id] = ir

        # Sample field history
        history = [
            FieldHistory(
                id="fh-001", field_id="field-001", season="2024-Kharif",
                crop="Rice", variety="IR64", planting_date=date(2024, 6, 15),
                harvest_date=date(2024, 10, 20), yield_amount=4500
            ),
            FieldHistory(
                id="fh-002", field_id="field-001", season="2023-Rabi",
                crop="Wheat", variety="HD2967", planting_date=date(2023, 11, 10),
                harvest_date=date(2024, 4, 5), yield_amount=3800
            ),
        ]
        for h in history:
            self._field_history[h.id] = h

    # Soil Profile Methods
    def get_soil_profiles(self, field_id: Optional[str] = None) -> List[SoilProfile]:
        """Get soil profiles, optionally filtered by field"""
        profiles = list(self._soil_profiles.values())
        if field_id:
            profiles = [p for p in profiles if p.field_id == field_id]
        return sorted(profiles, key=lambda p: p.sample_date, reverse=True)

    def get_soil_profile(self, profile_id: str) -> Optional[SoilProfile]:
        """Get a specific soil profile"""
        return self._soil_profiles.get(profile_id)

    def add_soil_profile(self, data: Dict[str, Any]) -> SoilProfile:
        """Add a new soil profile"""
        profile_id = f"sp-{uuid.uuid4().hex[:8]}"
        profile = SoilProfile(
            id=profile_id,
            field_id=data["field_id"],
            sample_date=data.get("sample_date", date.today()),
            depth_cm=data.get("depth_cm", 30),
            texture=SoilTexture(data.get("texture", "loam")),
            ph=data["ph"],
            organic_matter=data.get("organic_matter", 0),
            nitrogen=data.get("nitrogen", 0),
            phosphorus=data.get("phosphorus", 0),
            potassium=data.get("potassium", 0),
            calcium=data.get("calcium"),
            magnesium=data.get("magnesium"),
            notes=data.get("notes", ""),
        )
        self._soil_profiles[profile_id] = profile
        return profile

    # Input Log Methods
    def get_input_logs(self, field_id: Optional[str] = None, input_type: Optional[InputType] = None) -> List[InputLog]:
        """Get input logs with optional filters"""
        logs = list(self._input_logs.values())
        if field_id:
            logs = [l for l in logs if l.field_id == field_id]
        if input_type:
            logs = [l for l in logs if l.input_type == input_type]
        return sorted(logs, key=lambda l: l.application_date, reverse=True)

    def add_input_log(self, data: Dict[str, Any]) -> InputLog:
        """Add a new input log"""
        log_id = f"inp-{uuid.uuid4().hex[:8]}"
        log = InputLog(
            id=log_id,
            field_id=data["field_id"],
            input_type=InputType(data["input_type"]),
            product_name=data["product_name"],
            application_date=data.get("application_date", date.today()),
            quantity=data["quantity"],
            unit=data["unit"],
            area_applied=data.get("area_applied", 1.0),
            method=data.get("method", ""),
            applicator=data.get("applicator"),
            cost=data.get("cost"),
            notes=data.get("notes", ""),
        )
        self._input_logs[log_id] = log
        return log

    # Irrigation Methods
    def get_irrigation_events(self, field_id: Optional[str] = None) -> List[IrrigationEvent]:
        """Get irrigation events"""
        events = list(self._irrigation_events.values())
        if field_id:
            events = [e for e in events if e.field_id == field_id]
        return sorted(events, key=lambda e: e.event_date, reverse=True)

    def add_irrigation_event(self, data: Dict[str, Any]) -> IrrigationEvent:
        """Add a new irrigation event"""
        event_id = f"irr-{uuid.uuid4().hex[:8]}"
        event = IrrigationEvent(
            id=event_id,
            field_id=data["field_id"],
            irrigation_type=IrrigationType(data.get("irrigation_type", "drip")),
            event_date=data.get("event_date", date.today()),
            duration_hours=data["duration_hours"],
            water_volume=data["water_volume"],
            source=data.get("source", ""),
            cost=data.get("cost"),
            notes=data.get("notes", ""),
        )
        self._irrigation_events[event_id] = event
        return event

    def get_water_usage_summary(self, field_id: str, year: int = None) -> Dict[str, Any]:
        """Get water usage summary for a field"""
        events = self.get_irrigation_events(field_id)
        if year:
            events = [e for e in events if e.event_date.year == year]

        total_volume = sum(e.water_volume for e in events)
        total_hours = sum(e.duration_hours for e in events)
        total_cost = sum(e.cost or 0 for e in events)

        return {
            "field_id": field_id,
            "total_events": len(events),
            "total_volume_m3": total_volume,
            "total_hours": total_hours,
            "total_cost": total_cost,
            "avg_volume_per_event": total_volume / len(events) if events else 0,
        }

    # Field History Methods
    def get_field_history(self, field_id: str) -> List[FieldHistory]:
        """Get field history (crop rotation)"""
        history = [h for h in self._field_history.values() if h.field_id == field_id]
        return sorted(history, key=lambda h: h.season, reverse=True)

    def add_field_history(self, data: Dict[str, Any]) -> FieldHistory:
        """Add a field history entry"""
        history_id = f"fh-{uuid.uuid4().hex[:8]}"
        history = FieldHistory(
            id=history_id,
            field_id=data["field_id"],
            season=data["season"],
            crop=data["crop"],
            variety=data.get("variety"),
            planting_date=data.get("planting_date"),
            harvest_date=data.get("harvest_date"),
            yield_amount=data.get("yield_amount"),
            yield_unit=data.get("yield_unit", "kg/ha"),
            notes=data.get("notes", ""),
        )
        self._field_history[history_id] = history
        return history

    # Fertilizer Recommendations
    def get_fertilizer_recommendations(self, profile_id: str) -> List[Dict[str, Any]]:
        """Generate fertilizer recommendations based on soil profile"""
        profile = self._soil_profiles.get(profile_id)
        if not profile:
            return []

        recommendations = []

        # Nitrogen recommendation
        n_target = 55  # kg/ha target
        if profile.nitrogen < n_target:
            deficit = n_target - profile.nitrogen
            urea_needed = deficit / 0.46  # Urea is 46% N
            recommendations.append({
                "nutrient": "Nitrogen",
                "current": profile.nitrogen,
                "target": n_target,
                "deficit": deficit,
                "product": "Urea (46-0-0)",
                "quantity": round(urea_needed, 1),
                "unit": "kg/ha",
                "timing": "Split application: 50% at sowing, 50% at tillering",
            })

        # Phosphorus recommendation
        p_target = 35
        if profile.phosphorus < p_target:
            deficit = p_target - profile.phosphorus
            dap_needed = deficit / 0.46  # DAP is 46% P2O5
            recommendations.append({
                "nutrient": "Phosphorus",
                "current": profile.phosphorus,
                "target": p_target,
                "deficit": deficit,
                "product": "DAP (18-46-0)",
                "quantity": round(dap_needed, 1),
                "unit": "kg/ha",
                "timing": "Apply at sowing",
            })

        # Potassium recommendation
        k_target = 175
        if profile.potassium < k_target:
            deficit = k_target - profile.potassium
            mop_needed = deficit / 0.60  # MOP is 60% K2O
            recommendations.append({
                "nutrient": "Potassium",
                "current": profile.potassium,
                "target": k_target,
                "deficit": deficit,
                "product": "MOP (0-0-60)",
                "quantity": round(mop_needed, 1),
                "unit": "kg/ha",
                "timing": "Apply at sowing or first irrigation",
            })

        # pH adjustment
        if profile.ph < 6.0:
            recommendations.append({
                "nutrient": "pH Correction",
                "current": profile.ph,
                "target": 6.5,
                "product": "Agricultural Lime",
                "quantity": round((6.5 - profile.ph) * 500, 0),
                "unit": "kg/ha",
                "timing": "Apply 2-3 weeks before sowing",
            })
        elif profile.ph > 8.0:
            recommendations.append({
                "nutrient": "pH Correction",
                "current": profile.ph,
                "target": 7.5,
                "product": "Gypsum",
                "quantity": round((profile.ph - 7.5) * 1000, 0),
                "unit": "kg/ha",
                "timing": "Apply before land preparation",
            })

        return recommendations


# Global service instance
field_environment = FieldEnvironmentService()
