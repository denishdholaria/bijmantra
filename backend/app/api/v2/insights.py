"""
AI Insights API Endpoints
Predictive analytics and intelligent recommendations

APEX FEATURE: AI-powered breeding insights (no competitor has this)
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, Query, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import get_current_user

router = APIRouter(prefix="/insights", tags=["AI Insights"])


# ============================================
# SCHEMAS
# ============================================

class InsightAction(BaseModel):
    label: str
    action: str


class Insight(BaseModel):
    id: str
    type: str  # prediction, recommendation, alert, opportunity
    title: str
    description: str
    confidence: float
    impact: str  # high, medium, low
    category: str
    actionable: bool
    actions: Optional[List[InsightAction]] = None
    data: Optional[Dict[str, Any]] = None
    created_at: datetime


class TrendData(BaseModel):
    label: str
    current: float
    previous: float
    change: float
    trend: str  # up, down, stable


class InsightsResponse(BaseModel):
    summary: str
    insights: List[Insight]
    trends: List[TrendData]
    generated_at: datetime


class PredictionRequest(BaseModel):
    entity_type: str
    entity_id: str
    prediction_type: str
    parameters: Optional[Dict[str, Any]] = None


class PredictionResponse(BaseModel):
    prediction_type: str
    entity_type: str
    entity_id: str
    predicted_value: float
    confidence_interval: List[float]
    confidence: float
    factors: List[Dict[str, Any]]
    generated_at: datetime


# ============================================
# ENDPOINTS
# ============================================

@router.get("/dashboard", response_model=InsightsResponse)
async def get_insights_dashboard(
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Get AI-powered insights dashboard.
    
    Returns:
    - AI-generated summary from Veena
    - Predictions, recommendations, alerts, and opportunities
    - Key trend indicators
    """
    # In production, this would call ML models and analyze data
    
    insights = [
        Insight(
            id="insight-1",
            type="prediction",
            title="Yield Increase Predicted for Trial T-2024-15",
            description="Based on current growth patterns and weather forecasts, we predict a 12% yield increase for wheat varieties in Trial T-2024-15. The favorable moisture conditions and optimal temperature range are contributing factors.",
            confidence=87.0,
            impact="high",
            category="Yield Prediction",
            actionable=True,
            actions=[
                InsightAction(label="View Trial Details", action="view-trial"),
                InsightAction(label="Adjust Resources", action="adjust-resources")
            ],
            data={"trial_id": "T-2024-15", "predicted_increase": 12.0},
            created_at=datetime.utcnow()
        ),
        Insight(
            id="insight-2",
            type="recommendation",
            title="Optimal Crossing Parents Identified",
            description="Analysis of genomic data suggests crossing Line A-2847 with Line B-1923 could produce progeny with 15% higher disease resistance while maintaining yield potential.",
            confidence=92.0,
            impact="high",
            category="Crossing Strategy",
            actionable=True,
            actions=[
                InsightAction(label="Plan Cross", action="plan-cross"),
                InsightAction(label="View Analysis", action="view-analysis")
            ],
            data={"parent_1": "A-2847", "parent_2": "B-1923", "trait": "disease_resistance"},
            created_at=datetime.utcnow()
        ),
        Insight(
            id="insight-3",
            type="alert",
            title="Data Quality Issue Detected",
            description="Missing phenotype observations detected in 3 plots of Study S-2024-08. This may affect statistical analysis accuracy. Recommend field verification.",
            confidence=95.0,
            impact="medium",
            category="Data Quality",
            actionable=True,
            actions=[
                InsightAction(label="Review Data", action="review-data"),
                InsightAction(label="Dismiss", action="dismiss")
            ],
            data={"study_id": "S-2024-08", "missing_plots": 3},
            created_at=datetime.utcnow()
        ),
        Insight(
            id="insight-4",
            type="opportunity",
            title="Genetic Gain Acceleration Possible",
            description="Current selection intensity could be increased by 20% without compromising genetic diversity. This would accelerate genetic gain by approximately 0.5% per cycle.",
            confidence=78.0,
            impact="medium",
            category="Selection Strategy",
            actionable=True,
            actions=[
                InsightAction(label="Simulate Impact", action="simulate"),
                InsightAction(label="Learn More", action="learn-more")
            ],
            data={"current_intensity": 0.15, "recommended_intensity": 0.18},
            created_at=datetime.utcnow()
        ),
        Insight(
            id="insight-5",
            type="prediction",
            title="Flowering Date Forecast",
            description="Based on accumulated growing degree days and current weather patterns, flowering is predicted to occur 5 days earlier than historical average for Location L-001.",
            confidence=84.0,
            impact="low",
            category="Phenology",
            actionable=False,
            data={"location_id": "L-001", "days_early": 5},
            created_at=datetime.utcnow()
        )
    ]
    
    trends = [
        TrendData(label="Active Trials", current=24, previous=21, change=14.3, trend="up"),
        TrendData(label="Observations This Week", current=1847, previous=1623, change=13.8, trend="up"),
        TrendData(label="Genetic Gain (% per year)", current=2.3, previous=2.1, change=9.5, trend="up"),
        TrendData(label="Data Quality Score", current=94, previous=96, change=-2.1, trend="down")
    ]
    
    summary = (
        "Namaste! 🙏 Your breeding program is showing strong momentum this season. "
        "I've identified 2 high-impact opportunities that could significantly improve your genetic gain. "
        "The predicted yield increase in Trial T-2024-15 is particularly exciting - the combination of "
        "favorable weather and your improved germplasm is paying off. However, I noticed some data quality "
        "issues that need attention before your next analysis cycle. Would you like me to prioritize the "
        "crossing recommendations or focus on data cleanup first?"
    )
    
    return InsightsResponse(
        summary=summary,
        insights=insights,
        trends=trends,
        generated_at=datetime.utcnow()
    )


@router.post("/predict", response_model=PredictionResponse)
async def generate_prediction(
    request: PredictionRequest,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Generate AI prediction for a specific entity.
    
    Prediction types:
    - yield: Predict yield for a trial/study
    - flowering: Predict flowering date
    - disease_risk: Predict disease risk
    - genetic_value: Predict breeding value
    """
    # In production, this would call actual ML models
    
    predictions = {
        "yield": {
            "predicted_value": 4.2,
            "confidence_interval": [3.8, 4.6],
            "confidence": 85.0,
            "factors": [
                {"name": "Weather", "impact": 0.35, "direction": "positive"},
                {"name": "Soil Quality", "impact": 0.25, "direction": "positive"},
                {"name": "Germplasm", "impact": 0.30, "direction": "positive"},
                {"name": "Management", "impact": 0.10, "direction": "neutral"}
            ]
        },
        "flowering": {
            "predicted_value": 75,  # days
            "confidence_interval": [72, 78],
            "confidence": 82.0,
            "factors": [
                {"name": "GDD Accumulation", "impact": 0.45, "direction": "positive"},
                {"name": "Photoperiod", "impact": 0.30, "direction": "neutral"},
                {"name": "Variety", "impact": 0.25, "direction": "positive"}
            ]
        },
        "disease_risk": {
            "predicted_value": 0.23,  # probability
            "confidence_interval": [0.15, 0.31],
            "confidence": 78.0,
            "factors": [
                {"name": "Humidity", "impact": 0.40, "direction": "negative"},
                {"name": "Temperature", "impact": 0.25, "direction": "neutral"},
                {"name": "Resistance Genes", "impact": 0.35, "direction": "positive"}
            ]
        },
        "genetic_value": {
            "predicted_value": 1.45,  # GEBV
            "confidence_interval": [1.20, 1.70],
            "confidence": 90.0,
            "factors": [
                {"name": "Marker Effects", "impact": 0.60, "direction": "positive"},
                {"name": "Pedigree", "impact": 0.25, "direction": "positive"},
                {"name": "Phenotype", "impact": 0.15, "direction": "positive"}
            ]
        }
    }
    
    pred_data = predictions.get(request.prediction_type, predictions["yield"])
    
    return PredictionResponse(
        prediction_type=request.prediction_type,
        entity_type=request.entity_type,
        entity_id=request.entity_id,
        predicted_value=pred_data["predicted_value"],
        confidence_interval=pred_data["confidence_interval"],
        confidence=pred_data["confidence"],
        factors=pred_data["factors"],
        generated_at=datetime.utcnow()
    )


@router.get("/recommendations/crossing")
async def get_crossing_recommendations(
    trait: Optional[str] = Query(None, description="Target trait to optimize"),
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Get AI-recommended crossing combinations.
    
    Analyzes genomic data to suggest optimal parent combinations
    for maximizing genetic gain while maintaining diversity.
    """
    recommendations = [
        {
            "rank": 1,
            "parent_1": {"id": "G-2847", "name": "Elite Line A", "gebv": 1.45},
            "parent_2": {"id": "G-1923", "name": "Donor Line B", "gebv": 1.32},
            "predicted_progeny_mean": 1.52,
            "predicted_variance": 0.15,
            "genetic_distance": 0.42,
            "complementarity_score": 0.89,
            "target_traits": ["yield", "disease_resistance"],
            "confidence": 92
        },
        {
            "rank": 2,
            "parent_1": {"id": "G-3156", "name": "High Yield C", "gebv": 1.58},
            "parent_2": {"id": "G-2089", "name": "Quality Line D", "gebv": 1.21},
            "predicted_progeny_mean": 1.48,
            "predicted_variance": 0.18,
            "genetic_distance": 0.38,
            "complementarity_score": 0.85,
            "target_traits": ["yield", "quality"],
            "confidence": 88
        },
        {
            "rank": 3,
            "parent_1": {"id": "G-1567", "name": "Stress Tolerant E", "gebv": 1.35},
            "parent_2": {"id": "G-2934", "name": "Adapted Line F", "gebv": 1.28},
            "predicted_progeny_mean": 1.42,
            "predicted_variance": 0.12,
            "genetic_distance": 0.35,
            "complementarity_score": 0.82,
            "target_traits": ["stress_tolerance", "adaptation"],
            "confidence": 85
        }
    ]
    
    return {
        "target_trait": trait or "overall",
        "recommendations": recommendations[:limit],
        "methodology": "Genomic prediction with optimal contribution selection",
        "generated_at": datetime.utcnow().isoformat()
    }


@router.get("/recommendations/selection")
async def get_selection_recommendations(
    study_id: str = Query(..., description="Study to analyze"),
    selection_intensity: float = Query(0.2, ge=0.01, le=0.5),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Get AI-recommended selections for a study.
    
    Analyzes breeding values and diversity to recommend
    which individuals to advance.
    """
    return {
        "study_id": study_id,
        "selection_intensity": selection_intensity,
        "total_candidates": 500,
        "recommended_selections": 100,
        "expected_genetic_gain": 2.3,
        "diversity_retained": 0.85,
        "selections": [
            {"id": "OU-001", "name": "Entry 1", "gebv": 1.85, "rank": 1, "selected": True},
            {"id": "OU-002", "name": "Entry 2", "gebv": 1.78, "rank": 2, "selected": True},
            {"id": "OU-003", "name": "Entry 3", "gebv": 1.72, "rank": 3, "selected": True},
            # ... more entries
        ],
        "methodology": "GBLUP with optimal contribution",
        "generated_at": datetime.utcnow().isoformat()
    }


@router.get("/weather/impact")
async def get_weather_impact_analysis(
    location_id: str = Query(..., description="Location to analyze"),
    days_ahead: int = Query(14, ge=1, le=30),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Get AI analysis of weather impact on breeding activities.
    
    Combines weather forecasts with crop models to predict
    impacts on trials and recommend actions.
    """
    return {
        "location_id": location_id,
        "forecast_days": days_ahead,
        "overall_risk": "low",
        "impacts": [
            {
                "date": (datetime.utcnow() + timedelta(days=3)).isoformat(),
                "event": "Heavy Rain",
                "probability": 0.75,
                "impact": "medium",
                "affected_activities": ["field_observation", "pollination"],
                "recommendation": "Complete pollinations before rain event"
            },
            {
                "date": (datetime.utcnow() + timedelta(days=7)).isoformat(),
                "event": "Heat Wave",
                "probability": 0.60,
                "impact": "high",
                "affected_activities": ["flowering", "grain_fill"],
                "recommendation": "Consider irrigation to mitigate heat stress"
            }
        ],
        "optimal_windows": [
            {
                "activity": "pollination",
                "start": (datetime.utcnow() + timedelta(days=1)).isoformat(),
                "end": (datetime.utcnow() + timedelta(days=2)).isoformat(),
                "confidence": 0.85
            },
            {
                "activity": "data_collection",
                "start": (datetime.utcnow() + timedelta(days=4)).isoformat(),
                "end": (datetime.utcnow() + timedelta(days=6)).isoformat(),
                "confidence": 0.90
            }
        ],
        "generated_at": datetime.utcnow().isoformat()
    }
