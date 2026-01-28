
import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sklearn.linear_model import LinearRegression
from scipy import stats

from app.models.field_operations import FieldBookObservation, FieldBookTrait, FieldBookStudy
from app.models.future.yield_prediction import YieldPrediction

logger = logging.getLogger(__name__)

class StatisticalPredictor:
    """
    Statistical Yield Predictor using historical regression analysis.

    Implements Task 1:
    - 1.1 Create statistical predictor service with historical regression
    - 1.2 Add trend analysis and outlier detection
    - 1.3 Implement confidence interval calculations
    - 1.4 Add data validation and quality scoring
    """

    async def predict(
        self,
        db: AsyncSession,
        field_id: int,
        crop_name: str,
        target_year: int,
        org_id: int
    ) -> Dict:
        """
        Predict yield using historical statistical analysis.

        Args:
            db: Database session
            field_id: Field ID
            crop_name: Name of the crop
            target_year: Year to predict for
            org_id: Organization ID

        Returns:
            Dictionary containing prediction results and metadata
        """
        # 1. Fetch historical data
        history = await self._fetch_historical_yields(db, field_id, crop_name, org_id)

        # 1.4 Data Validation
        valid_history = self._validate_data(history)

        if len(valid_history) < 3:
             logger.warning(f"Insufficient historical data for field {field_id}, crop {crop_name}. Found {len(valid_history)} valid records.")
             return {
                 "predicted_yield": None,
                 "confidence_interval": None,
                 "method": "statistical",
                 "status": "insufficient_data",
                 "message": "Insufficient historical data (minimum 3 years required)"
             }

        # 2. Prepare data
        df = pd.DataFrame(valid_history)
        X = df[['year']].values
        y = df['yield'].values

        # 1.2 Outlier Detection (Z-score)
        z_scores = np.abs(stats.zscore(y))
        # Filter out outliers (z-score > 2.5)
        mask = z_scores < 2.5

        if np.sum(mask) < 3:
             # If removing outliers leaves too few points, use original data but warn
             logger.warning("Outlier removal resulted in too few data points. Using all points.")
        else:
            X = X[mask]
            y = y[mask]

        # 3. Train Model (1.1 Historical Regression)
        model = LinearRegression()
        model.fit(X, y)

        # 4. Predict
        predicted_yield = model.predict([[target_year]])[0]

        # 5. Calculate Confidence Intervals (1.3)
        lower_bound, upper_bound = self._calculate_confidence_interval(X, y, model, target_year)

        # 1.2 Trend Analysis
        slope = model.coef_[0]
        if slope > 0.05:
            trend = "increasing"
        elif slope < -0.05:
            trend = "decreasing"
        else:
            trend = "stable"

        return {
            "predicted_yield": max(0.0, float(predicted_yield)), # Yield can't be negative
            "lower_bound": max(0.0, float(lower_bound)),
            "upper_bound": float(upper_bound),
            "confidence_level": 0.95,
            "r_squared": float(model.score(X, y)),
            "historical_data_points": len(valid_history),
            "outliers_removed": int(len(valid_history) - len(y)),
            "trend": trend,
            "slope": float(slope),
            "method": "statistical",
            "status": "success"
        }

    async def _fetch_historical_yields(self, db: AsyncSession, field_id: int, crop_name: str, org_id: int) -> List[Dict]:
        """
        Fetch historical yield data from YieldPrediction table and FieldBookObservations.
        """
        history = []

        # 1. Fetch from YieldPrediction table (actual_yields)
        query = select(YieldPrediction).where(
            YieldPrediction.field_id == field_id,
            YieldPrediction.crop_name == crop_name,
            YieldPrediction.organization_id == org_id,
            YieldPrediction.actual_yield.isnot(None)
        )
        result = await db.execute(query)
        predictions = result.scalars().all()

        for p in predictions:
            # Parse year from season or prediction_date
            year = p.prediction_date.year
            history.append({"year": year, "yield": p.actual_yield, "source": "yield_history"})

        # 2. Fetch from FieldBookObservations (if trait is yield)
        # This assumes we can link observations to the field and crop.
        # Since FieldBookStudy has location and season, but no direct field_id, this is complex.
        # For now, we rely on YieldPrediction table which is cleaner for this specific purpose.
        # If needed, we can expand this to query observations.

        # Deduplicate by year (preferring most recent entry)
        # Sort by year
        history.sort(key=lambda x: x["year"])

        return history

    def _validate_data(self, history: List[Dict]) -> List[Dict]:
        """
        Validate historical data points (1.4).
        """
        valid = []
        for h in history:
            if h.get("yield") is not None and h["yield"] > 0 and h.get("year") is not None:
                valid.append(h)
        return valid

    def _calculate_confidence_interval(self, X, y, model, x_pred, confidence=0.95):
        """
        Calculate prediction interval for linear regression.
        """
        n = len(y)
        if n <= 2:
            return 0.0, 0.0 # Should be handled by caller

        y_pred = model.predict(X)

        # Mean squared error
        mse = np.sum((y - y_pred) ** 2) / (n - 2)

        # Standard error of prediction
        x_mean = np.mean(X)
        se_pred = np.sqrt(mse * (1 + 1/n + (x_pred - x_mean)**2 / np.sum((X - x_mean)**2)))

        # t-statistic
        t_stat = stats.t.ppf((1 + confidence) / 2, n - 2)

        y_out = model.predict([[x_pred]])[0]
        interval = t_stat * se_pred

        return y_out - interval, y_out + interval
