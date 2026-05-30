"""
TDD tests for REEVU Proactive Insights.

Written BEFORE the implementation. RED → GREEN → REFACTOR.

Covers:
- Task 1.3: ReevuInsight model structure
- Task 2: InsightDeliveryService (get_active, mark_read, dismiss, expire_old)
- Task 3: DataQualityAnalyzer (missing obs, outliers, idempotency)
- Task 4: PerformanceAnomalyDetector (anomaly detection)
- Task 5: EnvironmentalEventCorrelator (weather alert → insight)
- Task 6: InsightGenerationJob orchestration + feature flag
- Task 7.1: get_insights function pattern detection
"""

import pytest
from datetime import datetime, UTC, timedelta
from unittest.mock import AsyncMock, MagicMock, patch


# ── Helpers ──────────────────────────────────────────────────────────────────

def _make_db() -> AsyncMock:
    return AsyncMock()


def _make_insight(
    id: int = 1,
    organization_id: int = 1,
    insight_type: str = "data_quality",
    severity: str = "warning",
    title: str = "Missing observations",
    description: str = "Trial T1 has no observations in 35 days",
    status: str = "new",
    expires_at: datetime | None = None,
) -> MagicMock:
    obj = MagicMock()
    obj.id = id
    obj.organization_id = organization_id
    obj.insight_type = insight_type
    obj.severity = severity
    obj.title = title
    obj.description = description
    obj.status = status
    obj.expires_at = expires_at or (datetime.now(UTC) + timedelta(days=30))
    obj.created_at = datetime.now(UTC)
    obj.updated_at = datetime.now(UTC)
    obj.affected_entities = {"trials": ["T1"]}
    obj.evidence = {"days_since_last_obs": 35}
    obj.suggested_action = "Add observations for trial T1"
    return obj


# ── Task 1.3: ReevuInsight model ──────────────────────────────────────────────

def test_reevu_insight_model_is_importable():
    """ReevuInsight model can be imported."""
    from app.models.reevu_insights import ReevuInsight
    assert ReevuInsight is not None


def test_reevu_insight_model_has_required_columns():
    """ReevuInsight has all required columns."""
    from app.models.reevu_insights import ReevuInsight
    cols = {c.name for c in ReevuInsight.__table__.columns}
    required = {
        "id", "organization_id", "insight_type", "severity",
        "title", "description", "affected_entities", "evidence",
        "suggested_action", "status", "expires_at", "created_at", "updated_at",
    }
    assert required.issubset(cols), f"Missing columns: {required - cols}"


def test_reevu_insight_tablename():
    from app.models.reevu_insights import ReevuInsight
    assert ReevuInsight.__tablename__ == "reevu_insights"


# ── Task 2: InsightDeliveryService ────────────────────────────────────────────

def test_insight_delivery_service_is_importable():
    from app.modules.ai.services.reevu.insight_delivery_service import InsightDeliveryService
    assert InsightDeliveryService is not None


@pytest.mark.asyncio
async def test_get_active_insights_returns_new_and_read():
    """get_active_insights returns insights with status 'new' or 'read' that haven't expired."""
    from app.modules.ai.services.reevu.insight_delivery_service import InsightDeliveryService

    svc = InsightDeliveryService()
    db = _make_db()

    active_insights = [
        _make_insight(id=1, status="new"),
        _make_insight(id=2, status="read"),
    ]
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = active_insights
    db.execute = AsyncMock(return_value=mock_result)

    result = await svc.get_active_insights(db=db, organization_id=1)

    assert len(result) == 2
    db.execute.assert_called_once()


@pytest.mark.asyncio
async def test_get_active_insights_excludes_dismissed():
    """get_active_insights does not return dismissed insights."""
    from app.modules.ai.services.reevu.insight_delivery_service import InsightDeliveryService

    svc = InsightDeliveryService()
    db = _make_db()

    # Only active insights returned (dismissed filtered by query)
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = []
    db.execute = AsyncMock(return_value=mock_result)

    result = await svc.get_active_insights(db=db, organization_id=1)

    assert result == []
    # Verify query was executed (filtering happens in DB)
    db.execute.assert_called_once()


@pytest.mark.asyncio
async def test_mark_read_updates_status():
    """mark_read sets insight status to 'read'."""
    from app.modules.ai.services.reevu.insight_delivery_service import InsightDeliveryService

    svc = InsightDeliveryService()
    db = _make_db()
    insight = _make_insight(status="new")
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = insight
    db.execute = AsyncMock(return_value=mock_result)

    await svc.mark_read(db=db, insight_id=1)

    assert insight.status == "read"
    db.commit.assert_called_once()


@pytest.mark.asyncio
async def test_dismiss_updates_status():
    """dismiss sets insight status to 'dismissed'."""
    from app.modules.ai.services.reevu.insight_delivery_service import InsightDeliveryService

    svc = InsightDeliveryService()
    db = _make_db()
    insight = _make_insight(status="new")
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = insight
    db.execute = AsyncMock(return_value=mock_result)

    await svc.dismiss(db=db, insight_id=1)

    assert insight.status == "dismissed"
    db.commit.assert_called_once()


@pytest.mark.asyncio
async def test_mark_read_noop_when_insight_not_found():
    """mark_read does nothing when insight_id doesn't exist."""
    from app.modules.ai.services.reevu.insight_delivery_service import InsightDeliveryService

    svc = InsightDeliveryService()
    db = _make_db()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    db.execute = AsyncMock(return_value=mock_result)

    # Should not raise
    await svc.mark_read(db=db, insight_id=999)
    db.commit.assert_not_called()


# ── Task 3: DataQualityAnalyzer ───────────────────────────────────────────────

def test_data_quality_analyzer_is_importable():
    from app.modules.ai.services.reevu.insight_generation_job import DataQualityAnalyzer
    assert DataQualityAnalyzer is not None


def test_data_quality_analyzer_detects_missing_observations():
    """DataQualityAnalyzer creates 'info' insight for trials with no recent observations."""
    from app.modules.ai.services.reevu.insight_generation_job import (
        DataQualityAnalyzer,
        InsightCandidate,
    )

    analyzer = DataQualityAnalyzer()
    stale_trials = [
        {"id": "T1", "trial_name": "Trial 1", "days_since_last_obs": 45},
        {"id": "T2", "trial_name": "Trial 2", "days_since_last_obs": 35},
    ]

    candidates = analyzer.scan_missing_observations(stale_trials)

    assert len(candidates) == 2
    for c in candidates:
        assert isinstance(c, InsightCandidate)
        assert c.severity == "info"
        assert c.insight_type == "data_quality"
        assert len(c.title) > 0
        assert len(c.suggested_action) > 0


def test_data_quality_analyzer_detects_outliers():
    """DataQualityAnalyzer creates 'warning' insight for observations >3 SD from mean."""
    from app.modules.ai.services.reevu.insight_generation_job import (
        DataQualityAnalyzer,
        InsightCandidate,
    )

    analyzer = DataQualityAnalyzer()
    # Tight cluster around 5.0 with one extreme outlier at 50.0
    # Mean ≈ 13.2, SD ≈ 20.1, threshold ≈ 60.3 — wait, still not enough
    # Use a very tight cluster: mean=5.0, SD≈0.07, threshold≈0.21 → 9.0 is 57 SD away
    observations = [
        {"id": "O1", "value": 5.00, "trait": "yield", "germplasm_id": "G1"},
        {"id": "O2", "value": 5.05, "trait": "yield", "germplasm_id": "G2"},
        {"id": "O3", "value": 4.95, "trait": "yield", "germplasm_id": "G3"},
        {"id": "O4", "value": 5.02, "trait": "yield", "germplasm_id": "G4"},
        {"id": "O5", "value": 5.03, "trait": "yield", "germplasm_id": "G5"},
        {"id": "O6", "value": 50.0, "trait": "yield", "germplasm_id": "G6"},  # extreme outlier
    ]

    candidates = analyzer.scan_outliers(observations, trait="yield")

    outlier_candidates = [c for c in candidates if "O6" in str(c.affected_entities)]
    assert len(outlier_candidates) >= 1
    assert outlier_candidates[0].severity == "warning"


def test_data_quality_analyzer_idempotency():
    """Scanning the same data twice produces the same insight candidates (no duplicates)."""
    from app.modules.ai.services.reevu.insight_generation_job import DataQualityAnalyzer

    analyzer = DataQualityAnalyzer()
    stale_trials = [{"id": "T1", "trial_name": "Trial 1", "days_since_last_obs": 45}]

    candidates1 = analyzer.scan_missing_observations(stale_trials)
    candidates2 = analyzer.scan_missing_observations(stale_trials)

    # Same input → same output (idempotent)
    assert len(candidates1) == len(candidates2)
    assert candidates1[0].title == candidates2[0].title


# ── Task 4: PerformanceAnomalyDetector ───────────────────────────────────────

def test_performance_anomaly_detector_is_importable():
    from app.modules.ai.services.reevu.insight_generation_job import PerformanceAnomalyDetector
    assert PerformanceAnomalyDetector is not None


def test_performance_anomaly_detector_flags_extreme_values():
    """Entry >2 SD from program mean → 'warning' insight."""
    from app.modules.ai.services.reevu.insight_generation_job import (
        PerformanceAnomalyDetector,
        InsightCandidate,
    )

    detector = PerformanceAnomalyDetector()
    # Tight cluster around 5.0 with two extreme outliers
    entries = [
        {"germplasm_id": "G1", "mean_value": 5.00, "trait": "yield"},
        {"germplasm_id": "G2", "mean_value": 5.05, "trait": "yield"},
        {"germplasm_id": "G3", "mean_value": 4.95, "trait": "yield"},
        {"germplasm_id": "G4", "mean_value": 5.02, "trait": "yield"},
        {"germplasm_id": "G5", "mean_value": 5.03, "trait": "yield"},
        {"germplasm_id": "G6", "mean_value": 50.0, "trait": "yield"},  # far above
        {"germplasm_id": "G7", "mean_value": -30.0, "trait": "yield"},  # far below
    ]

    candidates = detector.scan_performance_anomalies(entries, trait="yield")

    anomaly_ids = {str(c.affected_entities) for c in candidates}
    assert any("G6" in s for s in anomaly_ids)
    assert any("G7" in s for s in anomaly_ids)
    for c in candidates:
        assert c.severity == "warning"
        assert isinstance(c, InsightCandidate)


def test_performance_anomaly_detector_no_anomalies_when_all_normal():
    """No anomalies when all entries are within 2 SD."""
    from app.modules.ai.services.reevu.insight_generation_job import PerformanceAnomalyDetector

    detector = PerformanceAnomalyDetector()
    entries = [
        {"germplasm_id": f"G{i}", "mean_value": 5.0 + i * 0.1, "trait": "yield"}
        for i in range(5)
    ]

    candidates = detector.scan_performance_anomalies(entries, trait="yield")

    assert candidates == []


# ── Task 5: EnvironmentalEventCorrelator ─────────────────────────────────────

def test_environmental_event_correlator_is_importable():
    from app.modules.ai.services.reevu.insight_generation_job import EnvironmentalEventCorrelator
    assert EnvironmentalEventCorrelator is not None


def test_environmental_correlator_creates_critical_insight_for_weather_alert():
    """Weather alert at trial location → 'critical' insight."""
    from app.modules.ai.services.reevu.insight_generation_job import (
        EnvironmentalEventCorrelator,
        InsightCandidate,
    )

    correlator = EnvironmentalEventCorrelator()
    weather_alerts = [
        {
            "location_id": "L1",
            "location_name": "Ludhiana",
            "alert_type": "drought",
            "severity": "high",
            "description": "Severe drought conditions",
        }
    ]
    active_trials = [
        {"id": "T1", "trial_name": "Wheat Trial", "location_id": "L1"},
    ]

    candidates = correlator.scan_weather_events(weather_alerts, active_trials)

    assert len(candidates) >= 1
    assert candidates[0].severity == "critical"
    assert candidates[0].insight_type == "environmental_event"
    assert isinstance(candidates[0], InsightCandidate)


def test_environmental_correlator_no_insight_when_no_overlap():
    """No insight when weather alert location doesn't match any active trial."""
    from app.modules.ai.services.reevu.insight_generation_job import EnvironmentalEventCorrelator

    correlator = EnvironmentalEventCorrelator()
    weather_alerts = [{"location_id": "L99", "alert_type": "drought", "severity": "high", "description": "Drought"}]
    active_trials = [{"id": "T1", "trial_name": "Trial 1", "location_id": "L1"}]

    candidates = correlator.scan_weather_events(weather_alerts, active_trials)

    assert candidates == []


# ── Task 6: InsightGenerationJob ─────────────────────────────────────────────

def test_insight_generation_job_is_importable():
    from app.modules.ai.services.reevu.insight_generation_job import InsightGenerationJob
    assert InsightGenerationJob is not None


def test_insight_generation_job_respects_feature_flag():
    """InsightGenerationJob.run() returns 0 when feature flag is disabled."""
    from app.modules.ai.services.reevu.insight_generation_job import InsightGenerationJob

    job = InsightGenerationJob(enabled=False)
    # Should return 0 without doing any work
    import asyncio
    result = asyncio.get_event_loop().run_until_complete(
        job.run(db=_make_db(), organization_id=1)
    )
    assert result == 0


def test_insight_candidate_has_required_fields():
    """InsightCandidate dataclass has all required fields."""
    from app.modules.ai.services.reevu.insight_generation_job import InsightCandidate

    candidate = InsightCandidate(
        insight_type="data_quality",
        severity="warning",
        title="Test insight",
        description="Test description",
        affected_entities={"trials": ["T1"]},
        evidence={"key": "value"},
        suggested_action="Do something",
    )
    assert candidate.insight_type == "data_quality"
    assert candidate.severity == "warning"
    assert len(candidate.title) > 0


# ── Task 7.1: get_insights function pattern detection ─────────────────────────

def test_get_insights_detected_from_alert_phrases():
    """'any alerts', 'any insights', 'what should i know' → get_insights function."""
    from app.modules.ai.services.function_calling_service import FunctionCallingService

    svc = FunctionCallingService(api_key=None, function_schemas=[])
    for phrase in [
        "are there any alerts?",
        "any insights I should know about?",
        "what should i know today?",
        "anything unusual in my data?",
        "any notifications?",
    ]:
        result = svc._detect_get_insights(phrase)
        assert result is True, f"Expected get_insights detection for: '{phrase}'"


def test_get_insights_not_detected_for_normal_queries():
    """Normal queries do not trigger get_insights detection."""
    from app.modules.ai.services.function_calling_service import FunctionCallingService

    svc = FunctionCallingService(api_key=None, function_schemas=[])
    for phrase in [
        "show me trial results",
        "which variety has highest yield?",
        "what is the weather forecast?",
    ]:
        result = svc._detect_get_insights(phrase)
        assert result is False, f"Expected False for: '{phrase}'"
