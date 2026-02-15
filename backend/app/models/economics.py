"""
Agricultural Economics Models
Cost-Benefit Analysis, Market Trends, and Inventory Optimization
"""

from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, JSON, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.models.base import Base

class CostBenefitAnalysis(Base):
    """
    Financial analysis for a breeding program, trial, or specific cross.
    Used to calculate ROI and NPV.
    """
    __tablename__ = "cost_benefit_analyses"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    
    # Target of Analysis (Polymorphic-like association)
    entity_type = Column(String(50)) # e.g. "program", "trial", "cross"
    entity_id = Column(Integer)
    
    analysis_name = Column(String(255), nullable=False)
    currency = Column(String(3), default="USD")
    
    # Financial Inputs
    total_cost = Column(Float, nullable=False, comment="Total investment cost")
    expected_revenue = Column(Float, nullable=False, comment="Projected total revenue")
    discount_rate = Column(Float, default=0.05, comment="Discount rate for NPV (e.g. 0.05 for 5%)")
    time_horizon_years = Column(Integer, default=5)
    
    # Calculated Metrics
    net_present_value = Column(Float, comment="NPV")
    roi_percent = Column(Float, comment="Return on Investment %")
    benefit_cost_ratio = Column(Float, comment="B/C Ratio")
    break_even_point = Column(Float, comment="Years to break even")
    
    # Detailed Data
    cost_breakdown = Column(JSON, comment="Detailed cost components")
    revenue_streams = Column(JSON, comment="Detailed revenue projections")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    organization = relationship("Organization")


class MarketTrend(Base):
    """
    Market demand forecast for specific crops or traits.
    Used to guide breeding objectives.
    """
    __tablename__ = "market_trends"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    
    crop_name = Column(String(100), nullable=False, index=True)
    trait_name = Column(String(100), index=True) # Optional: if specific to a trait (e.g. "Drought Tolerance")
    region = Column(String(100)) # Specific market region
    
    # Time Series Data
    historical_data = Column(JSON, comment="Checkpoints: [{date, value}, ...]")
    forecast_data = Column(JSON, comment="Predicted: [{date, value, confidence_interval}, ...]")
    
    # Forecast Metadata
    forecast_method = Column(String(50), default="exponential_smoothing")
    accuracy_metric = Column(Float, comment="e.g. MAPE")
    last_updated = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    organization = relationship("Organization")
