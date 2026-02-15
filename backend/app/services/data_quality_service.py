# backend/app/services/data_quality_service.py
from typing import List, Dict, Any, Tuple
import numpy as np

class DataQualityService:
    def detect_outliers(self, temperatures: List[float]) -> Tuple[List[int], Dict[str, Any]]:
        """
        Detects outliers in a list of temperatures using the Z-score method.
        """
        if not temperatures:
            return [], {}

        outliers = []
        mean = np.mean(temperatures)
        std = np.std(temperatures)
        threshold = 3.0

        for i, temp in enumerate(temperatures):
            z_score = (temp - mean) / std if std > 0 else 0
            if abs(z_score) > threshold:
                outliers.append(i)

        return outliers, {"mean": mean, "std_dev": std, "threshold": threshold}

    def calculate_completeness(self, data: List[Any]) -> float:
        """
        Calculates the completeness of a dataset, assuming None values are missing data.
        """
        if not data:
            return 0.0

        valid_points = sum(1 for item in data if item is not None)
        return valid_points / len(data)

    def validate_temperature_range(self, temp: float, min_temp: float = -50.0, max_temp: float = 60.0) -> bool:
        """
        Validates if a temperature is within a reasonable range.
        """
        return min_temp <= temp <= max_temp
