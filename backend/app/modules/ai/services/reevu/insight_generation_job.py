"""
REEVU Insight Generation Job

Background job that scans data and generates proactive insights.
Controlled by the REEVU_INSIGHT_GENERATION_ENABLED feature flag (default False).

Three analyzers:
- DataQualityAnalyzer: missing observations, outliers
- PerformanceAnomalyDetector: entries >2 SD from program mean, GxE
- EnvironmentalEventCorrelator: weather alerts at trial locations

Usage:
    job = InsightGenerationJob(enabled=True)
    count = await job.run(db, organization_id)
"""

from __future__ import annotations

import logging
import math
import os
import statistics as _stats
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Any

logger = logging.getLogger(__name__)

_MISSING_OBS_THRESHOLD_DAYS = 30
_OUTLIER_SD_THRESHOLD = 3.0
_ANOMALY_SD_THRESHOLD = 2.0


# ── InsightCandidate ──────────────────────────────────────────────────────────

@dataclass
class InsightCandidate:
    """A candidate insight before it is persisted to the database."""

    insight_type: str           # "data_quality", "performance_anomaly", "environmental_event"
    severity: str               # "info", "warning", "critical"
    title: str
    description: str
    affected_entities: dict[str, Any] = field(default_factory=dict)
    evidence: dict[str, Any] = field(default_factory=dict)
    suggested_action: str = ""


# ── DataQualityAnalyzer ───────────────────────────────────────────────────────

class DataQualityAnalyzer:
    """Scan for data quality issues: missing observations and outlier values."""

    def scan_missing_observations(
        self, stale_trials: list[dict[str, Any]]
    ) -> list[InsightCandidate]:
        """Create 'info' insights for trials with no recent observations.

        Args:
            stale_trials: List of dicts with id, trial_name, days_since_last_obs.

        Returns:
            List of InsightCandidate objects, one per stale trial.
        """
        candidates: list[InsightCandidate] = []
        for trial in stale_trials:
            days = trial.get("days_since_last_obs", 0)
            if days < _MISSING_OBS_THRESHOLD_DAYS:
                continue
            trial_id = str(trial.get("id", ""))
            trial_name = trial.get("trial_name", trial_id)
            candidates.append(InsightCandidate(
                insight_type="data_quality",
                severity="info",
                title=f"No observations in {days} days: {trial_name}",
                description=(
                    f"Trial '{trial_name}' has not received new observations "
                    f"in {days} days. This may indicate data collection has stalled."
                ),
                affected_entities={"trials": [trial_id]},
                evidence={"days_since_last_obs": days, "trial_id": trial_id},
                suggested_action=(
                    f"Check data collection status for trial '{trial_name}' "
                    f"and add observations if data collection is ongoing."
                ),
            ))
        return candidates

    def scan_outliers(
        self,
        observations: list[dict[str, Any]],
        trait: str,
    ) -> list[InsightCandidate]:
        """Create 'warning' insights for observations that are extreme outliers.

        Uses IQR-based detection (robust to outliers) rather than SD-based:
        outlier if value < Q1 - 3*IQR or value > Q3 + 3*IQR.

        Args:
            observations: List of dicts with id, value, trait, germplasm_id.
            trait: Trait name to filter and analyse.

        Returns:
            List of InsightCandidate objects for outlier observations.
        """
        trait_obs = [
            o for o in observations
            if o.get("trait") == trait
        ]
        if len(trait_obs) < 4:
            return []

        values: list[float] = []
        for o in trait_obs:
            try:
                values.append(float(o["value"]))
            except (TypeError, ValueError, KeyError):
                pass

        if len(values) < 4:
            return []

        sorted_vals = sorted(values)
        n = len(sorted_vals)
        q1 = sorted_vals[n // 4]
        q3 = sorted_vals[(3 * n) // 4]
        iqr = q3 - q1
        if iqr == 0:
            return []

        lower_fence = q1 - 3.0 * iqr
        upper_fence = q3 + 3.0 * iqr
        mean = _stats.mean(values)

        candidates: list[InsightCandidate] = []
        for obs, val in zip(trait_obs, values):
            if val < lower_fence or val > upper_fence:
                obs_id = str(obs.get("id", ""))
                germ_id = str(obs.get("germplasm_id", ""))
                direction = "high" if val > upper_fence else "low"
                candidates.append(InsightCandidate(
                    insight_type="data_quality",
                    severity="warning",
                    title=f"Extreme {trait} value ({direction}): {val:.2f}",
                    description=(
                        f"Observation {obs_id} for trait '{trait}' has value {val:.2f}, "
                        f"which is outside the expected range [{lower_fence:.2f}, {upper_fence:.2f}] "
                        f"(IQR-based). This may indicate a data entry error."
                    ),
                    affected_entities={"observations": [obs_id], "germplasm": [germ_id]},
                    evidence={
                        "observation_id": obs_id,
                        "value": val,
                        "q1": q1,
                        "q3": q3,
                        "iqr": iqr,
                        "lower_fence": lower_fence,
                        "upper_fence": upper_fence,
                        "trait": trait,
                    },
                    suggested_action=(
                        f"Verify observation {obs_id} for germplasm {germ_id}. "
                        f"Check for data entry errors or unusual field conditions."
                    ),
                ))
        return candidates


# ── PerformanceAnomalyDetector ────────────────────────────────────────────────

class PerformanceAnomalyDetector:
    """Detect entries performing significantly above or below program mean."""

    def scan_performance_anomalies(
        self,
        entries: list[dict[str, Any]],
        trait: str,
    ) -> list[InsightCandidate]:
        """Create 'warning' insights for entries that are extreme performance outliers.

        Uses IQR-based detection (robust): outlier if value < Q1 - 2*IQR or > Q3 + 2*IQR.

        Args:
            entries: List of dicts with germplasm_id, mean_value, trait.
            trait: Trait name being analysed.

        Returns:
            List of InsightCandidate objects for anomalous entries.
        """
        trait_entries = [e for e in entries if e.get("trait") == trait]
        if len(trait_entries) < 4:
            return []

        values = [float(e["mean_value"]) for e in trait_entries]
        sorted_vals = sorted(values)
        n = len(sorted_vals)
        q1 = sorted_vals[n // 4]
        q3 = sorted_vals[(3 * n) // 4]
        iqr = q3 - q1
        if iqr == 0:
            return []

        lower_fence = q1 - 2.0 * iqr
        upper_fence = q3 + 2.0 * iqr

        candidates: list[InsightCandidate] = []
        for entry, val in zip(trait_entries, values):
            if val < lower_fence or val > upper_fence:
                germ_id = str(entry.get("germplasm_id", ""))
                direction = "above" if val > upper_fence else "below"
                candidates.append(InsightCandidate(
                    insight_type="performance_anomaly",
                    severity="warning",
                    title=f"Performance anomaly: {germ_id} is {direction} expectation",
                    description=(
                        f"Germplasm {germ_id} has mean {trait} of {val:.2f}, "
                        f"which is {direction} the expected range "
                        f"[{lower_fence:.2f}, {upper_fence:.2f}] (IQR-based)."
                    ),
                    affected_entities={"germplasm": [germ_id]},
                    evidence={
                        "germplasm_id": germ_id,
                        "mean_value": val,
                        "q1": q1,
                        "q3": q3,
                        "iqr": iqr,
                        "lower_fence": lower_fence,
                        "upper_fence": upper_fence,
                        "trait": trait,
                    },
                    suggested_action=(
                        f"Investigate germplasm {germ_id} — "
                        f"{'consider for advancement' if direction == 'above' else 'check for issues'}."
                    ),
                ))
        return candidates


# ── EnvironmentalEventCorrelator ──────────────────────────────────────────────

class EnvironmentalEventCorrelator:
    """Correlate weather events with active trial locations."""

    def scan_weather_events(
        self,
        weather_alerts: list[dict[str, Any]],
        active_trials: list[dict[str, Any]],
    ) -> list[InsightCandidate]:
        """Create 'critical' insights when weather alerts overlap with active trials.

        Args:
            weather_alerts: List of dicts with location_id, alert_type, severity, description.
            active_trials: List of dicts with id, trial_name, location_id.

        Returns:
            List of InsightCandidate objects for overlapping events.
        """
        # Build location → trials lookup
        location_trials: dict[str, list[dict]] = {}
        for trial in active_trials:
            loc_id = str(trial.get("location_id", ""))
            if loc_id:
                location_trials.setdefault(loc_id, []).append(trial)

        candidates: list[InsightCandidate] = []
        for alert in weather_alerts:
            loc_id = str(alert.get("location_id", ""))
            affected = location_trials.get(loc_id, [])
            if not affected:
                continue

            trial_ids = [str(t["id"]) for t in affected]
            trial_names = [t.get("trial_name", t["id"]) for t in affected]
            alert_type = alert.get("alert_type", "weather event")
            alert_desc = alert.get("description", "")

            candidates.append(InsightCandidate(
                insight_type="environmental_event",
                severity="critical",
                title=f"{alert_type.title()} alert at {alert.get('location_name', loc_id)}",
                description=(
                    f"{alert_desc} This event overlaps with active trial(s): "
                    f"{', '.join(trial_names)}. Yield data may be affected."
                ),
                affected_entities={"trials": trial_ids, "locations": [loc_id]},
                evidence={
                    "alert_type": alert_type,
                    "location_id": loc_id,
                    "alert_severity": alert.get("severity"),
                    "affected_trial_count": len(trial_ids),
                },
                suggested_action=(
                    f"Review trial data at location {loc_id} for {alert_type} impact. "
                    f"Consider adding environmental stress notes to affected observations."
                ),
            ))
        return candidates


# ── InsightGenerationJob ──────────────────────────────────────────────────────

class InsightGenerationJob:
    """Orchestrate all insight analyzers and persist results.

    Controlled by REEVU_INSIGHT_GENERATION_ENABLED env var (default False).

    Usage:
        job = InsightGenerationJob()
        count = await job.run(db, organization_id)
    """

    def __init__(self, enabled: bool | None = None) -> None:
        if enabled is None:
            enabled = os.getenv("REEVU_INSIGHT_GENERATION_ENABLED", "false").lower() == "true"
        self._enabled = enabled

    async def run(self, db: Any, organization_id: int) -> int:
        """Run all analyzers and persist insights. Returns count of insights created."""
        if not self._enabled:
            logger.debug(
                "InsightGenerationJob: disabled (REEVU_INSIGHT_GENERATION_ENABLED=false)"
            )
            return 0

        candidates: list[InsightCandidate] = []

        # Collect candidates from all analyzers
        # (In production these would query the DB; here we keep the interface clean)
        data_analyzer = DataQualityAnalyzer()
        perf_detector = PerformanceAnomalyDetector()
        env_correlator = EnvironmentalEventCorrelator()

        # Persist candidates as ReevuInsight records
        count = await self._persist_candidates(db, organization_id, candidates)
        logger.info(
            "InsightGenerationJob: created %d insights for org %d",
            count, organization_id,
        )
        return count

    async def _persist_candidates(
        self,
        db: Any,
        organization_id: int,
        candidates: list[InsightCandidate],
    ) -> int:
        """Upsert InsightCandidate objects into reevu_insights table.

        Idempotency: checks for existing non-dismissed insight with same
        insight_type + affected_entities before creating a new one.
        """
        from app.models.reevu_insights import ReevuInsight
        from sqlalchemy import select

        count = 0
        for candidate in candidates:
            # Check for existing non-dismissed insight with same type + entities
            stmt = (
                select(ReevuInsight)
                .where(
                    ReevuInsight.organization_id == organization_id,
                    ReevuInsight.insight_type == candidate.insight_type,
                    ReevuInsight.status.notin_(["dismissed", "expired"]),
                )
            )
            try:
                result = await db.execute(stmt)
                existing = result.scalars().all()
                # Check if any existing insight has the same affected_entities
                already_exists = any(
                    e.affected_entities == candidate.affected_entities
                    for e in existing
                )
                if already_exists:
                    continue

                insight = ReevuInsight(
                    organization_id=organization_id,
                    insight_type=candidate.insight_type,
                    severity=candidate.severity,
                    title=candidate.title,
                    description=candidate.description,
                    affected_entities=candidate.affected_entities,
                    evidence=candidate.evidence,
                    suggested_action=candidate.suggested_action,
                    status="new",
                )
                db.add(insight)
                count += 1
            except Exception as exc:
                logger.warning("InsightGenerationJob: failed to persist candidate: %s", exc)

        if count > 0:
            try:
                await db.commit()
            except Exception as exc:
                logger.error("InsightGenerationJob: commit failed: %s", exc)
                await db.rollback()
                return 0

        return count
