"""
Agricultural Economics Service
Business logic for Cost-Benefit Analysis and Market Demand Forecasting
"""

import math
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import statistics

from sqlalchemy.ext.asyncio import AsyncSession
from app.models.economics import CostBenefitAnalysis, MarketTrend

class EconomicsService:
    """
    Service for calculating financial and market metrics.
    """

    def calculate_roi(
        self,
        total_cost: float,
        expected_revenue: float
    ) -> float:
        """
        Calculate simple ROI percentage.
        ROI = (Net Profit / Cost) * 100
        """
        if total_cost == 0:
            return 0.0
        
        net_profit = expected_revenue - total_cost
        return (net_profit / total_cost) * 100.0

    def calculate_npv(
        self,
        initial_investment: float,
        cash_flows: List[float],
        discount_rate: float = 0.05
    ) -> float:
        """
        Calculate Net Present Value (NPV).
        NPV = Sum( CashFlow_t / (1 + r)^t ) - Initial Invevstment
        """
        npv = -initial_investment
        for t, cash_flow in enumerate(cash_flows, start=1):
            npv += cash_flow / ((1 + discount_rate) ** t)
            
        return npv

    def forecast_demand_exponential_smoothing(
        self,
        historical_data: List[float],
        alpha: float = 0.2, # Smoothing factor (0 < alpha < 1)
        periods_to_forecast: int = 1
    ) -> List[float]:
        """
        Forecast demand using Simple Exponential Smoothing.
        Suitable for data without clear trend or seasonality.
        
        New Forecast = alpha * Actual_Last + (1 - alpha) * Forecast_Last
        """
        if not historical_data:
            return []
            
        # Initial forecast is the first data point
        forecast = [historical_data[0]]
        
        # Calculate smoothed values for historical period
        for i in range(1, len(historical_data)):
            next_val = alpha * historical_data[i] + (1 - alpha) * forecast[-1]
            forecast.append(next_val)
            
        # Project into future
        future_forecast = []
        last_smoothed = forecast[-1]
        for _ in range(periods_to_forecast):
            future_forecast.append(last_smoothed) # Flat forecast for SES
            
        return future_forecast

    async def create_cost_benefit_analysis(
        self,
        db: AsyncSession,
        organization_id: int,
        name: str,
        total_cost: float,
        expected_revenue: float,
        discount_rate: float = 0.05,
        cash_flows: Optional[List[float]] = None
    ) -> CostBenefitAnalysis:
        """
        Perform and save a Cost-Benefit Analysis.
        """
        roi = self.calculate_roi(total_cost, expected_revenue)
        
        npv = None
        if cash_flows:
            npv = self.calculate_npv(total_cost, cash_flows, discount_rate)
            
        analysis = CostBenefitAnalysis(
            organization_id=organization_id,
            analysis_name=name,
            total_cost=total_cost,
            expected_revenue=expected_revenue,
            discount_rate=discount_rate,
            roi_percent=roi,
            net_present_value=npv,
            benefit_cost_ratio=(expected_revenue / total_cost) if total_cost > 0 else 0
        )
        
        db.add(analysis)
        await db.commit()
        await db.refresh(analysis)
        return analysis

# Global instance
economics_service = EconomicsService()
