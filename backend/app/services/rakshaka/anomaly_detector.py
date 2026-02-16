"""
RAKSHAKA Anomaly Detector - Statistical anomaly detection
Pillar 2: SMRITI (स्मृति) - Memory - Threat intelligence
Pillar 3: VIVEK (विवेक) - Discrimination - Friend or foe detection
"""

import statistics
from datetime import datetime, UTC, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from collections import deque
from enum import Enum


class AnomalySeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AnomalyType(str, Enum):
    LATENCY_SPIKE = "latency_spike"
    ERROR_RATE = "error_rate"
    MEMORY_PRESSURE = "memory_pressure"
    CPU_SPIKE = "cpu_spike"
    DISK_PRESSURE = "disk_pressure"
    CONNECTION_POOL = "connection_pool"
    TRAFFIC_ANOMALY = "traffic_anomaly"


@dataclass
class Anomaly:
    id: str
    type: AnomalyType
    severity: AnomalySeverity
    detected_at: datetime
    metric_name: str
    current_value: float
    baseline_value: float
    threshold: float
    description: str
    resolved: bool = False
    resolved_at: Optional[datetime] = None


class AnomalyDetector:
    """
    Statistical anomaly detection engine.
    Uses moving averages and standard deviation for baseline comparison.
    """

    def __init__(self, baseline_window: int = 100):
        self.baseline_window = baseline_window
        self._baselines: Dict[str, deque] = {}
        self._anomalies: List[Anomaly] = []
        self._anomaly_counter = 0

        # Thresholds (configurable)
        self.thresholds = {
            "api_latency_ms": {"warn": 500, "crit": 1000, "std_multiplier": 2.5},
            "db_latency_ms": {"warn": 200, "crit": 500, "std_multiplier": 2.5},
            "error_rate": {"warn": 1.0, "crit": 5.0, "std_multiplier": 3.0},
            "cpu_percent": {"warn": 70, "crit": 90, "std_multiplier": 2.0},
            "memory_percent": {"warn": 70, "crit": 90, "std_multiplier": 2.0},
            "disk_percent": {"warn": 80, "crit": 95, "std_multiplier": 2.0},
        }

    def update_baseline(self, metric_name: str, value: float):
        """Update the baseline for a metric"""
        if metric_name not in self._baselines:
            self._baselines[metric_name] = deque(maxlen=self.baseline_window)
        self._baselines[metric_name].append(value)

    def get_baseline_stats(self, metric_name: str) -> Dict[str, float]:
        """Get baseline statistics for a metric"""
        if metric_name not in self._baselines or len(self._baselines[metric_name]) < 10:
            return {"mean": 0, "std": 0, "min": 0, "max": 0}

        values = list(self._baselines[metric_name])
        return {
            "mean": round(statistics.mean(values), 2),
            "std": round(statistics.stdev(values), 2) if len(values) > 1 else 0,
            "min": round(min(values), 2),
            "max": round(max(values), 2)
        }

    def check_anomaly(self, metric_name: str, value: float) -> Optional[Anomaly]:
        """Check if a value is anomalous and create anomaly if so"""
        self.update_baseline(metric_name, value)

        threshold_config = self.thresholds.get(metric_name)
        if not threshold_config:
            return None

        stats = self.get_baseline_stats(metric_name)

        # Threshold-based detection
        severity = None
        if value >= threshold_config["crit"]:
            severity = AnomalySeverity.CRITICAL
        elif value >= threshold_config["warn"]:
            severity = AnomalySeverity.HIGH

        # Statistical detection (if we have enough baseline data)
        if stats["std"] > 0 and severity is None:
            z_score = (value - stats["mean"]) / stats["std"]
            if z_score > threshold_config["std_multiplier"]:
                severity = AnomalySeverity.MEDIUM

        if severity:
            anomaly = self._create_anomaly(
                metric_name=metric_name,
                current_value=value,
                baseline_value=stats["mean"],
                threshold=threshold_config["warn"],
                severity=severity
            )
            return anomaly

        return None

    def _create_anomaly(self, metric_name: str, current_value: float,
                       baseline_value: float, threshold: float,
                       severity: AnomalySeverity) -> Anomaly:
        """Create and register a new anomaly"""
        self._anomaly_counter += 1
        anomaly_type = self._get_anomaly_type(metric_name)

        anomaly = Anomaly(
            id=f"ANM-{self._anomaly_counter:06d}",
            type=anomaly_type,
            severity=severity,
            detected_at=datetime.now(UTC),
            metric_name=metric_name,
            current_value=current_value,
            baseline_value=baseline_value,
            threshold=threshold,
            description=self._generate_description(metric_name, current_value, baseline_value)
        )
        self._anomalies.append(anomaly)
        return anomaly

    def _get_anomaly_type(self, metric_name: str) -> AnomalyType:
        """Map metric name to anomaly type"""
        mapping = {
            "api_latency_ms": AnomalyType.LATENCY_SPIKE,
            "db_latency_ms": AnomalyType.LATENCY_SPIKE,
            "error_rate": AnomalyType.ERROR_RATE,
            "cpu_percent": AnomalyType.CPU_SPIKE,
            "memory_percent": AnomalyType.MEMORY_PRESSURE,
            "disk_percent": AnomalyType.DISK_PRESSURE,
        }
        return mapping.get(metric_name, AnomalyType.TRAFFIC_ANOMALY)

    def _generate_description(self, metric_name: str, current: float, baseline: float) -> str:
        """Generate human-readable anomaly description"""
        diff = current - baseline
        pct = (diff / baseline * 100) if baseline > 0 else 0
        return f"{metric_name} is {current:.1f} ({pct:+.1f}% from baseline {baseline:.1f})"

    def resolve_anomaly(self, anomaly_id: str) -> bool:
        """Mark an anomaly as resolved"""
        for anomaly in self._anomalies:
            if anomaly.id == anomaly_id and not anomaly.resolved:
                anomaly.resolved = True
                anomaly.resolved_at = datetime.now(UTC)
                return True
        return False

    def get_active_anomalies(self) -> List[Dict[str, Any]]:
        """Get all unresolved anomalies"""
        return [self._anomaly_to_dict(a) for a in self._anomalies if not a.resolved]

    def get_all_anomalies(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent anomalies (resolved and unresolved)"""
        sorted_anomalies = sorted(self._anomalies, key=lambda x: x.detected_at, reverse=True)
        return [self._anomaly_to_dict(a) for a in sorted_anomalies[:limit]]

    def _anomaly_to_dict(self, anomaly: Anomaly) -> Dict[str, Any]:
        return {
            "id": anomaly.id,
            "type": anomaly.type.value,
            "severity": anomaly.severity.value,
            "detected_at": anomaly.detected_at.isoformat(),
            "metric_name": anomaly.metric_name,
            "current_value": anomaly.current_value,
            "baseline_value": anomaly.baseline_value,
            "threshold": anomaly.threshold,
            "description": anomaly.description,
            "resolved": anomaly.resolved,
            "resolved_at": anomaly.resolved_at.isoformat() if anomaly.resolved_at else None
        }

    def get_config(self) -> Dict[str, Any]:
        """Get current detector configuration"""
        return {
            "baseline_window": self.baseline_window,
            "thresholds": self.thresholds,
            "baselines": {
                name: self.get_baseline_stats(name)
                for name in self._baselines.keys()
            }
        }

    def update_config(self, thresholds: Dict[str, Dict] = None,
                     baseline_window: int = None) -> Dict[str, Any]:
        """Update detector configuration"""
        if baseline_window:
            self.baseline_window = baseline_window
        if thresholds:
            for metric, config in thresholds.items():
                if metric in self.thresholds:
                    self.thresholds[metric].update(config)
        return self.get_config()


# Singleton instance
anomaly_detector = AnomalyDetector()
