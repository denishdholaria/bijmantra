"""
Climate Analysis API
Long-term climate trends and historical data analysis for agricultural planning.
"""

from datetime import datetime, date, timezone
from typing import Optional, List
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import get_current_user

router = APIRouter(prefix="/climate", tags=["Climate Analysis"])


class ClimateIndicator(BaseModel):
    """Climate indicator with historical comparison"""
    name: str
    current_value: float
    historical_avg: float
    change: float
    change_percent: float
    unit: str
    trend: str  # increasing, decreasing, stable


class ClimateData(BaseModel):
    """Climate analysis response"""
    location_id: str
    location_name: str
    analysis_period: str
    indicators: List[ClimateIndicator]
    recommendations: List[dict]
    generated_at: str


class DroughtIndicator(BaseModel):
    """Drought monitoring indicator"""
    name: str
    value: float
    unit: str
    status: str  # Good, Moderate, Watch, Warning, Critical
    trend: str  # increasing, declining, stable


class DroughtRegion(BaseModel):
    """Regional drought status"""
    name: str
    status: str  # None, D0, D1, D2, D3, D4
    description: str
    soil_moisture: float
    days_since_rain: int


class DroughtData(BaseModel):
    """Drought monitoring response"""
    location_id: str
    alert_active: bool
    alert_message: Optional[str]
    indicators: List[DroughtIndicator]
    regions: List[DroughtRegion]
    recommendations: List[dict]
    generated_at: str


@router.get("/analysis/{location_id}", response_model=ClimateData)
async def get_climate_analysis(
    location_id: str,
    location_name: str = Query("Location", description="Location display name"),
    years: int = Query(30, ge=5, le=50, description="Historical comparison period"),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Get long-term climate analysis with historical comparisons.
    
    Analyzes:
    - Average temperature trends
    - Rainfall patterns
    - Growing season length
    - Extreme weather frequency
    """
    # In production, this would query historical weather data
    # For now, generate realistic climate analysis data

    indicators = [
        ClimateIndicator(
            name="Average Temperature",
            current_value=26.5,
            historical_avg=25.2,
            change=1.3,
            change_percent=5.2,
            unit="°C",
            trend="increasing"
        ),
        ClimateIndicator(
            name="Annual Rainfall",
            current_value=850,
            historical_avg=920,
            change=-70,
            change_percent=-7.6,
            unit="mm",
            trend="decreasing"
        ),
        ClimateIndicator(
            name="Growing Season",
            current_value=245,
            historical_avg=230,
            change=15,
            change_percent=6.5,
            unit="days",
            trend="increasing"
        ),
        ClimateIndicator(
            name="Frost-Free Days",
            current_value=280,
            historical_avg=265,
            change=15,
            change_percent=5.7,
            unit="days",
            trend="increasing"
        ),
        ClimateIndicator(
            name="Heat Stress Days (>35°C)",
            current_value=28,
            historical_avg=18,
            change=10,
            change_percent=55.6,
            unit="days",
            trend="increasing"
        ),
        ClimateIndicator(
            name="Heavy Rain Events",
            current_value=12,
            historical_avg=8,
            change=4,
            change_percent=50.0,
            unit="events/year",
            trend="increasing"
        ),
    ]

    recommendations = [
        {
            "icon": "💧",
            "title": "Water Management",
            "description": "Consider drought-tolerant varieties and improved irrigation efficiency due to declining rainfall trends.",
            "priority": "high"
        },
        {
            "icon": "📅",
            "title": "Planting Dates",
            "description": "Shift sowing dates 1-2 weeks earlier to optimize the extended growing season.",
            "priority": "medium"
        },
        {
            "icon": "🌾",
            "title": "Crop Selection",
            "description": "Evaluate heat-tolerant cultivars for changing temperature patterns. Consider short-duration varieties.",
            "priority": "high"
        },
        {
            "icon": "🛡️",
            "title": "Risk Management",
            "description": "Increase crop insurance coverage due to higher frequency of extreme weather events.",
            "priority": "medium"
        },
    ]

    return ClimateData(
        location_id=location_id,
        location_name=location_name,
        analysis_period=f"{years}-year comparison",
        indicators=indicators,
        recommendations=recommendations,
        generated_at=datetime.now(timezone.utc).isoformat()
    )


@router.get("/drought/{location_id}", response_model=DroughtData)
async def get_drought_monitor(
    location_id: str,
    location_name: str = Query("Location", description="Location display name"),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Get drought monitoring data and water stress indicators.
    
    Uses US Drought Monitor scale:
    - None: No drought
    - D0: Abnormally Dry
    - D1: Moderate Drought
    - D2: Severe Drought
    - D3: Extreme Drought
    - D4: Exceptional Drought
    """
    indicators = [
        DroughtIndicator(
            name="Soil Moisture Index",
            value=0.65,
            unit="",
            status="Moderate",
            trend="declining"
        ),
        DroughtIndicator(
            name="Vegetation Health (NDVI)",
            value=0.72,
            unit="",
            status="Good",
            trend="stable"
        ),
        DroughtIndicator(
            name="Evapotranspiration",
            value=5.2,
            unit="mm/day",
            status="High",
            trend="increasing"
        ),
        DroughtIndicator(
            name="Days Since Rain",
            value=12,
            unit="days",
            status="Watch",
            trend="increasing"
        ),
        DroughtIndicator(
            name="Groundwater Level",
            value=-2.3,
            unit="m below normal",
            status="Warning",
            trend="declining"
        ),
        DroughtIndicator(
            name="Reservoir Storage",
            value=68,
            unit="%",
            status="Moderate",
            trend="declining"
        ),
    ]

    regions = [
        DroughtRegion(
            name="North Block",
            status="D0",
            description="Abnormally Dry",
            soil_moisture=0.58,
            days_since_rain=14
        ),
        DroughtRegion(
            name="South Block",
            status="D1",
            description="Moderate Drought",
            soil_moisture=0.42,
            days_since_rain=18
        ),
        DroughtRegion(
            name="East Field",
            status="None",
            description="No Drought",
            soil_moisture=0.75,
            days_since_rain=5
        ),
        DroughtRegion(
            name="Trial Plots",
            status="D0",
            description="Abnormally Dry",
            soil_moisture=0.55,
            days_since_rain=12
        ),
    ]

    # Determine if alert is active
    has_drought = any(r.status in ["D1", "D2", "D3", "D4"] for r in regions)
    has_watch = any(r.status == "D0" for r in regions)

    alert_active = has_drought or has_watch
    alert_message = None
    if has_drought:
        alert_message = "Drought conditions detected. Implement water conservation measures immediately."
    elif has_watch:
        alert_message = "Below-normal rainfall for 2 consecutive weeks. Monitor soil moisture closely."

    recommendations = [
        {
            "priority": "high",
            "action": "Increase irrigation frequency for South Block (D1 status)",
            "impact": "Prevent crop stress and yield loss"
        },
        {
            "priority": "medium",
            "action": "Apply mulch to reduce evaporation in North Block",
            "impact": "Conserve soil moisture by 20-30%"
        },
        {
            "priority": "medium",
            "action": "Monitor soil moisture sensors daily until rain event",
            "impact": "Early detection of critical stress levels"
        },
        {
            "priority": "low",
            "action": "Review irrigation scheduling for efficiency",
            "impact": "Optimize water use across all blocks"
        },
    ]

    return DroughtData(
        location_id=location_id,
        alert_active=alert_active,
        alert_message=alert_message,
        indicators=indicators,
        regions=regions,
        recommendations=recommendations,
        generated_at=datetime.now(timezone.utc).isoformat()
    )


@router.get("/trends/{location_id}")
async def get_climate_trends(
    location_id: str,
    location_name: str = Query("Location"),
    parameter: str = Query("temperature", description="temperature, rainfall, or growing_season"),
    years: int = Query(30, ge=5, le=50),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Get historical climate trend data for visualization.
    """
    # Generate trend data for the specified parameter
    current_year = date.today().year
    trend_data = []

    if parameter == "temperature":
        base_value = 24.0
        trend_rate = 0.04  # °C per year
        for i in range(years):
            year = current_year - years + i + 1
            value = base_value + (i * trend_rate) + (0.5 if i % 3 == 0 else -0.3 if i % 5 == 0 else 0)
            trend_data.append({"year": year, "value": round(value, 1), "unit": "°C"})
    elif parameter == "rainfall":
        base_value = 950
        trend_rate = -2.5  # mm per year
        for i in range(years):
            year = current_year - years + i + 1
            value = base_value + (i * trend_rate) + (50 if i % 4 == 0 else -30 if i % 3 == 0 else 0)
            trend_data.append({"year": year, "value": round(value, 0), "unit": "mm"})
    else:  # growing_season
        base_value = 220
        trend_rate = 0.5  # days per year
        for i in range(years):
            year = current_year - years + i + 1
            value = base_value + (i * trend_rate) + (3 if i % 5 == 0 else -2 if i % 4 == 0 else 0)
            trend_data.append({"year": year, "value": round(value, 0), "unit": "days"})

    return {
        "location_id": location_id,
        "location_name": location_name,
        "parameter": parameter,
        "period": f"{current_year - years + 1}-{current_year}",
        "data": trend_data,
        "generated_at": datetime.now(timezone.utc).isoformat()
    }
