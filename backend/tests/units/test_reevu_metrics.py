"""Unit tests for REEVU runtime metrics collector and KPI reporting helper scripts."""

import threading
import time

from app.modules.ai.services.reevu.metrics import ReevuMetrics


class TestReevuMetricsSingleton:
    """Verify singleton and reset behavior."""

    def setup_method(self):
        ReevuMetrics.reset()

    def test_singleton_identity(self):
        m1 = ReevuMetrics.get()
        m2 = ReevuMetrics.get()
        assert m1 is m2

    def test_reset_creates_new_instance(self):
        m1 = ReevuMetrics.get()
        ReevuMetrics.reset()
        m2 = ReevuMetrics.get()
        assert m1 is not m2


class TestRecordRequest:
    """Verify counter and histogram recording."""

    def setup_method(self):
        ReevuMetrics.reset()

    def test_basic_counter(self):
        m = ReevuMetrics.get()
        m.record_request(domain="breeding", function_name="search_germplasm", status="ok")
        m.record_request(domain="breeding", function_name="search_germplasm", status="ok")
        snap = m.get_metrics_snapshot()
        assert snap["total_requests"] == 2
        assert len(snap["requests"]) == 1
        assert snap["requests"][0]["count"] == 2

    def test_latency_recording(self):
        m = ReevuMetrics.get()
        m.record_request(latency_seconds=0.5, stage="total")
        m.record_request(latency_seconds=1.5, stage="total")
        snap = m.get_metrics_snapshot()
        assert "total" in snap["latency"]
        lat = snap["latency"]["total"]
        assert lat["count"] == 2
        assert lat["min"] == 0.5
        assert lat["max"] == 1.5
        assert abs(lat["mean"] - 1.0) < 0.001

    def test_policy_flags_counted(self):
        m = ReevuMetrics.get()
        m.record_request(policy_flags=["stale_evidence:s1", "citation_mismatch:[3]"])
        m.record_request(policy_flags=["stale_evidence:s1"])
        snap = m.get_metrics_snapshot()
        flags_by_name = {f["flag"]: f["count"] for f in snap["policy_flags"]}
        assert flags_by_name["stale_evidence:s1"] == 2
        assert flags_by_name["citation_mismatch:[3]"] == 1

    def test_different_statuses(self):
        m = ReevuMetrics.get()
        m.record_request(domain="weather", status="ok")
        m.record_request(domain="weather", status="error")
        snap = m.get_metrics_snapshot()
        assert snap["total_requests"] == 2
        assert len(snap["requests"]) == 2


class TestSnapshotShape:
    """Verify the snapshot dict has the expected structure."""

    def setup_method(self):
        ReevuMetrics.reset()

    def test_empty_snapshot(self):
        m = ReevuMetrics.get()
        snap = m.get_metrics_snapshot()
        assert "uptime_seconds" in snap
        assert snap["total_requests"] == 0
        assert snap["requests"] == []
        assert snap["latency"] == {}
        assert snap["policy_flags"] == []

    def test_uptime_increases(self):
        m = ReevuMetrics.get()
        time.sleep(0.05)
        snap = m.get_metrics_snapshot()
        assert snap["uptime_seconds"] >= 0.04


class TestThreadSafety:
    """Basic concurrency check — no crashes under parallel writes."""

    def setup_method(self):
        ReevuMetrics.reset()

    def test_concurrent_recording(self):
        m = ReevuMetrics.get()
        errors: list[Exception] = []

        def worker(domain: str, count: int):
            try:
                for _ in range(count):
                    m.record_request(
                        domain=domain,
                        latency_seconds=0.001,
                        policy_flags=["test_flag"],
                    )
            except Exception as exc:
                errors.append(exc)

        threads = [
            threading.Thread(target=worker, args=("breeding", 100)),
            threading.Thread(target=worker, args=("weather", 100)),
            threading.Thread(target=worker, args=("genomics", 100)),
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert errors == []
        snap = m.get_metrics_snapshot()
        assert snap["total_requests"] == 300

import pytest

from scripts.compare_reevu_kpi_delta import build_delta_report


def _sample_ops() -> dict:
    return {
        "kpi_checks": {
            "trace_completeness": {"value": 0.99, "floor": 0.99, "met": True},
            "tool_call_precision": {"value": 0.95, "floor": 0.92, "met": True},
            "domain_detection_accuracy": {"value": 0.85, "floor": 0.85, "met": True},
            "compound_classification": {"value": 0.80, "floor": 0.80, "met": True},
            "step_adequacy": {"value": 0.85, "floor": 0.85, "met": True},
        }
    }


def test_build_delta_report_computes_core_deltas_and_floor_status() -> None:
    baseline_cross = {
        "domain_detection_accuracy": 0.80,
        "compound_classification_accuracy": 0.75,
        "step_adequacy_rate": 0.90,
    }
    latest_cross = {
        "domain_detection_accuracy": 0.88,
        "compound_classification_accuracy": 0.78,
        "step_adequacy_rate": 0.82,
    }

    report = build_delta_report(baseline_cross, latest_cross, _sample_ops())

    domain = report["metrics"]["domain_detection_accuracy"]
    assert domain["delta"] == pytest.approx(0.08)
    assert domain["before_floor_met"] is False
    assert domain["after_floor_met"] is True

    step = report["metrics"]["step_adequacy"]
    assert step["delta"] == pytest.approx(-0.08)
    assert step["before_floor_met"] is True
    assert step["after_floor_met"] is False

    trace = report["metrics"]["trace_completeness"]
    assert trace["before"] is None
    assert trace["delta"] is None
    assert trace["after_floor_met"] is True

    assert report["overall_after_floor_met"] is False


def test_build_delta_report_raises_on_missing_required_core_metric() -> None:
    baseline_cross = {
        "domain_detection_accuracy": 0.80,
        "compound_classification_accuracy": 0.75,
    }
    latest_cross = {
        "domain_detection_accuracy": 0.88,
        "compound_classification_accuracy": 0.78,
        "step_adequacy_rate": 0.82,
    }

    with pytest.raises(ValueError, match="step_adequacy_rate"):
        build_delta_report(baseline_cross, latest_cross, _sample_ops())
