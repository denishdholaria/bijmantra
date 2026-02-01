"""
Spatial Analysis Service
GIS and spatial analysis for field trials and breeding programs
"""

from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from uuid import uuid4
import math


class SpatialAnalysisService:
    """Service for spatial analysis and field mapping"""
    
    def __init__(self):
        # In-memory storage
        self.fields: Dict[str, Dict] = {}
        self.plots: Dict[str, List[Dict]] = {}
        self.spatial_adjustments: Dict[str, Dict] = {}
        
        # Initialize sample data
        self._init_sample_data()
    
    def _init_sample_data(self):
        """Initialize with sample field data"""
        field = {
            "field_id": "FLD-001",
            "name": "Research Station Field A",
            "location": "Punjab, India",
            "latitude": 30.9010,
            "longitude": 75.8573,
            "area_ha": 5.0,
            "soil_type": "Loamy",
            "irrigation": "Canal",
            "rows": 20,
            "columns": 25,
            "plot_size_m2": 10,
            "created_at": datetime.now().isoformat(),
        }
        self.fields["FLD-001"] = field
        self.plots["FLD-001"] = []
    
    def create_field(
        self,
        name: str,
        location: str,
        latitude: float,
        longitude: float,
        area_ha: float,
        rows: int,
        columns: int,
        plot_size_m2: float,
        soil_type: Optional[str] = None,
        irrigation: Optional[str] = None,
    ) -> Dict:
        """Create a new field for spatial analysis"""
        field_id = f"FLD-{str(uuid4())[:8].upper()}"
        
        field = {
            "field_id": field_id,
            "name": name,
            "location": location,
            "latitude": latitude,
            "longitude": longitude,
            "area_ha": area_ha,
            "soil_type": soil_type,
            "irrigation": irrigation,
            "rows": rows,
            "columns": columns,
            "plot_size_m2": plot_size_m2,
            "total_plots": rows * columns,
            "created_at": datetime.now().isoformat(),
        }
        
        self.fields[field_id] = field
        self.plots[field_id] = []
        
        return field
    
    def get_field(self, field_id: str) -> Optional[Dict]:
        """Get field details"""
        return self.fields.get(field_id)
    
    def list_fields(self) -> List[Dict]:
        """List all fields"""
        return list(self.fields.values())
    
    def generate_plot_coordinates(
        self,
        field_id: str,
        plot_width_m: float,
        plot_length_m: float,
        alley_width_m: float = 0.5,
        border_m: float = 2.0,
    ) -> List[Dict]:
        """Generate plot coordinates for a field"""
        if field_id not in self.fields:
            raise ValueError(f"Field {field_id} not found")
        
        field = self.fields[field_id]
        rows = field["rows"]
        columns = field["columns"]
        
        plots = []
        plot_num = 1
        
        for row in range(rows):
            for col in range(columns):
                # Calculate plot center coordinates (relative to field origin)
                x = border_m + col * (plot_width_m + alley_width_m) + plot_width_m / 2
                y = border_m + row * (plot_length_m + alley_width_m) + plot_length_m / 2
                
                plot = {
                    "plot_id": f"PLT-{field_id}-{plot_num:04d}",
                    "field_id": field_id,
                    "plot_number": plot_num,
                    "row": row + 1,
                    "column": col + 1,
                    "x_center_m": round(x, 2),
                    "y_center_m": round(y, 2),
                    "width_m": plot_width_m,
                    "length_m": plot_length_m,
                    "area_m2": plot_width_m * plot_length_m,
                }
                
                plots.append(plot)
                plot_num += 1
        
        self.plots[field_id] = plots
        
        return plots
    
    def get_plots(self, field_id: str) -> List[Dict]:
        """Get all plots for a field"""
        return self.plots.get(field_id, [])
    
    def calculate_distance(
        self,
        lat1: float,
        lon1: float,
        lat2: float,
        lon2: float,
    ) -> float:
        """Calculate distance between two GPS coordinates (Haversine formula)"""
        R = 6371000  # Earth's radius in meters
        
        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        delta_phi = math.radians(lat2 - lat1)
        delta_lambda = math.radians(lon2 - lon1)
        
        a = math.sin(delta_phi / 2) ** 2 + \
            math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        return R * c  # Distance in meters
    
    def spatial_autocorrelation(
        self,
        values: List[Dict[str, Any]],
        x_key: str = "x",
        y_key: str = "y",
        value_key: str = "value",
        max_distance: Optional[float] = None,
    ) -> Dict:
        """
        Calculate Moran's I spatial autocorrelation
        """
        n = len(values)
        if n < 3:
            return {"error": "Need at least 3 observations"}
        
        # Extract coordinates and values
        coords = [(v[x_key], v[y_key]) for v in values]
        vals = [v[value_key] for v in values]
        
        mean_val = sum(vals) / n
        
        # Calculate weights matrix (inverse distance)
        W = [[0.0] * n for _ in range(n)]
        total_weight = 0
        
        for i in range(n):
            for j in range(n):
                if i != j:
                    dist = math.sqrt(
                        (coords[i][0] - coords[j][0]) ** 2 +
                        (coords[i][1] - coords[j][1]) ** 2
                    )
                    if max_distance is None or dist <= max_distance:
                        if dist > 0:
                            W[i][j] = 1 / dist
                            total_weight += W[i][j]
        
        if total_weight == 0:
            return {"error": "No spatial weights calculated"}
        
        # Calculate Moran's I
        numerator = 0
        denominator = 0
        
        for i in range(n):
            denominator += (vals[i] - mean_val) ** 2
            for j in range(n):
                numerator += W[i][j] * (vals[i] - mean_val) * (vals[j] - mean_val)
        
        if denominator == 0:
            return {"error": "No variance in values"}
        
        morans_i = (n / total_weight) * (numerator / denominator)
        
        # Expected value under null hypothesis
        expected_i = -1 / (n - 1)
        
        return {
            "morans_i": round(morans_i, 4),
            "expected_i": round(expected_i, 4),
            "n_observations": n,
            "interpretation": "positive" if morans_i > 0 else "negative" if morans_i < 0 else "random",
            "note": "Positive = clustered, Negative = dispersed, ~0 = random",
        }
    
    def moving_average_adjustment(
        self,
        values: List[Dict[str, Any]],
        row_key: str = "row",
        col_key: str = "column",
        value_key: str = "value",
        window_size: int = 3,
    ) -> Dict:
        """
        Apply moving average spatial adjustment
        Adjusts values based on local neighborhood
        """
        n = len(values)
        if n < window_size ** 2:
            return {"error": f"Need at least {window_size ** 2} observations"}
        
        # Create grid
        max_row = max(v[row_key] for v in values)
        max_col = max(v[col_key] for v in values)
        
        grid = {}
        for v in values:
            grid[(v[row_key], v[col_key])] = v[value_key]
        
        # Calculate moving averages
        half_window = window_size // 2
        adjusted = []
        
        for v in values:
            row, col = v[row_key], v[col_key]
            neighbors = []
            
            for dr in range(-half_window, half_window + 1):
                for dc in range(-half_window, half_window + 1):
                    if dr == 0 and dc == 0:
                        continue
                    nr, nc = row + dr, col + dc
                    if (nr, nc) in grid:
                        neighbors.append(grid[(nr, nc)])
            
            if neighbors:
                local_mean = sum(neighbors) / len(neighbors)
                adjustment = v[value_key] - local_mean
            else:
                local_mean = v[value_key]
                adjustment = 0
            
            adjusted.append({
                "row": row,
                "column": col,
                "original_value": v[value_key],
                "local_mean": round(local_mean, 4),
                "adjusted_value": round(adjustment, 4),
                "n_neighbors": len(neighbors),
            })
        
        return {
            "method": "moving_average",
            "window_size": window_size,
            "n_observations": n,
            "adjusted_values": adjusted,
        }
    
    def nearest_neighbor_analysis(
        self,
        points: List[Dict[str, float]],
        x_key: str = "x",
        y_key: str = "y",
        area: Optional[float] = None,
    ) -> Dict:
        """
        Nearest neighbor analysis for point pattern
        """
        n = len(points)
        if n < 2:
            return {"error": "Need at least 2 points"}
        
        # Calculate nearest neighbor distances
        nn_distances = []
        
        for i, p1 in enumerate(points):
            min_dist = float('inf')
            for j, p2 in enumerate(points):
                if i != j:
                    dist = math.sqrt(
                        (p1[x_key] - p2[x_key]) ** 2 +
                        (p1[y_key] - p2[y_key]) ** 2
                    )
                    min_dist = min(min_dist, dist)
            nn_distances.append(min_dist)
        
        # Mean nearest neighbor distance
        mean_nn = sum(nn_distances) / n
        
        # Calculate expected distance under random distribution
        if area is None:
            # Estimate area from point extent
            x_vals = [p[x_key] for p in points]
            y_vals = [p[y_key] for p in points]
            area = (max(x_vals) - min(x_vals)) * (max(y_vals) - min(y_vals))
        
        density = n / area if area > 0 else 0
        expected_nn = 0.5 / math.sqrt(density) if density > 0 else 0
        
        # Nearest neighbor ratio
        nn_ratio = mean_nn / expected_nn if expected_nn > 0 else 0
        
        return {
            "mean_nn_distance": round(mean_nn, 4),
            "expected_nn_distance": round(expected_nn, 4),
            "nn_ratio": round(nn_ratio, 4),
            "n_points": n,
            "area": area,
            "interpretation": "clustered" if nn_ratio < 1 else "dispersed" if nn_ratio > 1 else "random",
        }
    
    def row_column_trend(
        self,
        values: List[Dict[str, Any]],
        row_key: str = "row",
        col_key: str = "column",
        value_key: str = "value",
    ) -> Dict:
        """
        Analyze row and column trends in field data
        """
        # Group by row
        row_means = {}
        col_means = {}
        
        for v in values:
            row = v[row_key]
            col = v[col_key]
            val = v[value_key]
            
            if row not in row_means:
                row_means[row] = []
            row_means[row].append(val)
            
            if col not in col_means:
                col_means[col] = []
            col_means[col].append(val)
        
        # Calculate means
        row_summary = [
            {"row": r, "mean": round(sum(vals) / len(vals), 4), "n": len(vals)}
            for r, vals in sorted(row_means.items())
        ]
        
        col_summary = [
            {"column": c, "mean": round(sum(vals) / len(vals), 4), "n": len(vals)}
            for c, vals in sorted(col_means.items())
        ]
        
        # Calculate trend (linear regression)
        def calc_trend(data, key):
            n = len(data)
            if n < 2:
                return 0
            x = [d[key] for d in data]
            y = [d["mean"] for d in data]
            x_mean = sum(x) / n
            y_mean = sum(y) / n
            
            num = sum((xi - x_mean) * (yi - y_mean) for xi, yi in zip(x, y))
            den = sum((xi - x_mean) ** 2 for xi in x)
            
            return num / den if den > 0 else 0
        
        row_trend = calc_trend(row_summary, "row")
        col_trend = calc_trend(col_summary, "column")
        
        return {
            "row_summary": row_summary,
            "column_summary": col_summary,
            "row_trend_slope": round(row_trend, 4),
            "column_trend_slope": round(col_trend, 4),
            "row_trend_direction": "increasing" if row_trend > 0 else "decreasing" if row_trend < 0 else "flat",
            "column_trend_direction": "increasing" if col_trend > 0 else "decreasing" if col_trend < 0 else "flat",
        }
    
    def get_statistics(self) -> Dict:
        """Get spatial analysis statistics"""
        fields = list(self.fields.values())
        total_plots = sum(len(self.plots.get(f["field_id"], [])) for f in fields)
        total_area = sum(f["area_ha"] for f in fields)
        
        return {
            "total_fields": len(fields),
            "total_plots": total_plots,
            "total_area_ha": total_area,
        }


# Singleton instance
spatial_analysis_service = SpatialAnalysisService()
