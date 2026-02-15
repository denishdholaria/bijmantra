
import logging
import asyncio
import pandas as pd
import numpy as np
from typing import Dict, List, Any
from concurrent.futures import ThreadPoolExecutor
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

# Import ML libraries
# Wrapped in try-except to avoid crashing if not installed in environment
try:
    from sklearn.ensemble import RandomForestRegressor
    import xgboost as xgb
    import shap
    ML_AVAILABLE = True
except Exception as e:
    ML_AVAILABLE = False
    MISSING_LIB = str(e)
    logging.warning(f"ML libraries import failed: {e}")

from app.models.future.yield_prediction import YieldPrediction

logger = logging.getLogger(__name__)

class MLPredictor:
    """
    ML-Based Yield Predictor.

    Implements Task 3:
    - 3.1 Create ML predictor service with feature engineering
    - 3.2 Add Random Forest regression model
    - 3.3 Implement Gradient Boosting (XGBoost) model
    - 3.4 Add SHAP-based feature importance analysis
    """

    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=3)

    async def predict(
        self,
        db: AsyncSession,
        field_id: int,
        crop_name: str,
        org_id: int,
        features: Dict[str, Any]
    ) -> Dict:
        """
        Predict yield using ML models.

        Args:
            features: Dictionary of features (weather, soil, management)
        """
        if not ML_AVAILABLE:
            logger.error(f"ML libraries not available: {MISSING_LIB if 'MISSING_LIB' in locals() else 'Unknown'}")
            return {
                "predicted_yield": None,
                "method": "ml_based",
                "status": "error",
                "message": "ML libraries (sklearn, xgboost, shap) not available."
            }

        # 1. Fetch Training Data (Async I/O)
        training_data = await self._fetch_training_data(db, crop_name, org_id)

        if len(training_data) < 10: # Minimum data points for ML
             logger.warning(f"Insufficient training data for ML. Found {len(training_data)}, need 10+.")
             return {
                "predicted_yield": None,
                "method": "ml_based",
                "status": "insufficient_data",
                "message": f"Insufficient training data. Found {len(training_data)}, need 10+."
            }

        # 2. Run Training and Prediction in ThreadPool (CPU bound)
        loop = asyncio.get_running_loop()
        try:
            result = await loop.run_in_executor(
                self.executor,
                self._train_and_predict_sync,
                training_data,
                features
            )
            return result
        except Exception as e:
             logger.error(f"Async execution of ML prediction failed: {str(e)}")
             return {
                "predicted_yield": None,
                "status": "error",
                "message": f"ML model execution failed: {str(e)}"
            }

    def _train_and_predict_sync(self, training_data: List[Dict], features: Dict[str, Any]) -> Dict:
        """
        Synchronous method for training and prediction (CPU bound).
        """
        # 2. Feature Engineering (3.1)
        df = pd.DataFrame(training_data)

        # Prepare X and y
        if 'yield' not in df.columns:
             return {
                "predicted_yield": None,
                "status": "error",
                "message": "Training data missing yield column."
            }

        y = df['yield']
        X = df.drop(columns=['yield', 'id', 'field_id', 'prediction_date'], errors='ignore')

        # Handle non-numeric data
        # Simple encoding: drop non-numeric or one-hot encode
        # For simplicity and robustness with sparse data, we'll try to get dummies but fillna first
        X = X.fillna(0)
        X = pd.get_dummies(X)

        # Align input features with training columns
        input_df = pd.DataFrame([features])
        input_df = pd.get_dummies(input_df)

        # Add missing columns to input_df (that were in training)
        for col in X.columns:
            if col not in input_df.columns:
                input_df[col] = 0

        # Remove columns in input_df that were not in training (model doesn't know them)
        input_df = input_df[X.columns]

        # 3. Train Models (3.2, 3.3)
        try:
            # Random Forest
            rf_model = RandomForestRegressor(n_estimators=100, random_state=42)
            rf_model.fit(X, y)
            rf_pred = rf_model.predict(input_df)[0]

            # XGBoost
            xgb_model = xgb.XGBRegressor(objective ='reg:squarederror', n_estimators=100, seed=42)
            xgb_model.fit(X, y)
            xgb_pred = xgb_model.predict(input_df)[0]

            # Ensemble average
            final_pred = (rf_pred + xgb_pred) / 2

            # 4. Feature Importance (3.4)
            # Using TreeExplainer for XGBoost
            explainer = shap.TreeExplainer(xgb_model)
            shap_values = explainer.shap_values(input_df)

            # shap_values can be a list or array
            if isinstance(shap_values, list):
                 vals = shap_values[0]
            else:
                 vals = shap_values

            feature_importance = {}
            for i, col in enumerate(X.columns):
                # vals has shape (n_samples, n_features), here n_samples=1
                val = vals[0][i] if len(vals.shape) > 1 else vals[i]
                feature_importance[col] = float(val)

            # Sort by absolute importance
            sorted_importance = dict(sorted(feature_importance.items(), key=lambda item: abs(item[1]), reverse=True)[:5])

            return {
                "predicted_yield": float(max(0, final_pred)),
                "rf_prediction": float(max(0, rf_pred)),
                "xgb_prediction": float(max(0, xgb_pred)),
                "feature_importance": sorted_importance,
                "training_samples": len(training_data),
                "method": "ml_based",
                "status": "success"
            }
        except Exception as e:
            logger.error(f"ML Prediction sync logic failed: {str(e)}")
            raise e

    async def _fetch_training_data(self, db: AsyncSession, crop_name: str, org_id: int) -> List[Dict]:
        """
        Fetch historical data for training.
        """
        query = select(YieldPrediction).where(
            YieldPrediction.crop_name == crop_name,
            YieldPrediction.organization_id == org_id,
            YieldPrediction.actual_yield.isnot(None)
        )
        result = await db.execute(query)
        predictions = result.scalars().all()

        data = []
        for p in predictions:
            row = {
                "yield": p.actual_yield,
                "id": p.id,
                "field_id": p.field_id,
                "prediction_date": p.prediction_date,
            }
            if p.weather_factors:
                row.update(p.weather_factors)
            if p.soil_factors:
                row.update(p.soil_factors)
            if p.management_factors:
                row.update(p.management_factors)

            data.append(row)

        return data
