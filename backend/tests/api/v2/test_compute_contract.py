from __future__ import annotations

from typing import Any

import numpy as np
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.deps import get_current_user
from app.api.v2 import compute as compute_api
from app.services.compute_engine import BLUPResult, compute_engine


@pytest.fixture
def client() -> TestClient:
    app = FastAPI()
    app.include_router(compute_api.router, prefix="/api/v2")
    app.dependency_overrides[get_current_user] = lambda: {"id": 1, "organization_id": 7, "email": "test@example.com"}

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


class _FakeAsyncSession:
    def __init__(self, sink: list[dict[str, Any]]):
        self.sink = sink

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    def add(self, item: Any) -> None:
        self.sink.append(
            {
                "action": item.action,
                "target_type": item.target_type,
                "target_id": item.target_id,
                "organization_id": item.organization_id,
                "user_id": item.user_id,
                "changes": item.changes,
                "method": item.method,
            }
        )

    async def commit(self) -> None:
        return None


async def _record_lineage(lineage_entries: list[dict[str, Any]], **kwargs: Any) -> None:
    lineage_entries.append(kwargs)


def test_gblup_returns_stable_contract_with_provenance(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    audit_entries: list[dict[str, Any]] = []
    lineage_entries: list[dict[str, Any]] = []

    def fake_compute_gblup(*args: Any, **kwargs: Any) -> BLUPResult:
        return BLUPResult(
            fixed_effects=np.array([2.8]),
            breeding_values=np.array([0.12, -0.05, 0.08]),
            converged=True,
        )

    monkeypatch.setattr(compute_engine, "compute_gblup", fake_compute_gblup)
    monkeypatch.setattr(compute_api, "AsyncSessionLocal", lambda: _FakeAsyncSession(audit_entries))
    monkeypatch.setattr(compute_api, "_persist_compute_lineage", lambda **kwargs: _record_lineage(lineage_entries, **kwargs))

    response = client.post(
        "/api/v2/compute/gblup",
        json={
            "genotypes": [[0, 1, 2], [1, 1, 0], [2, 0, 1]],
            "phenotypes": [2.5, 3.1, 2.8],
            "heritability": 0.4,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["contract_version"] == "compute.v1"
    assert payload["routine"] == "gblup"
    assert payload["output_kind"] == "breeding_values"
    assert payload["status"] == "succeeded"
    assert payload["output"]["breeding_values"] == [0.12, -0.05, 0.08]
    assert payload["provenance"]["routine"] == "gblup"
    assert payload["provenance"]["execution_mode"] == "sync"
    assert payload["provenance"]["lineage_record_id"] is not None
    assert payload["provenance"]["input_summary"] == {
        "n_observations": 3,
        "n_individuals": 3,
        "n_markers": 3,
        "n_fixed_effects": None,
        "n_random_effects": None,
        "relationship_matrix_shape": None,
        "heritability": 0.4,
        "method": None,
        "max_iter": None,
        "input_snapshot_at": payload["provenance"]["input_summary"]["input_snapshot_at"],
        "input_reliability_score": 0.85,
        "calculation_method_identifiers": ["genomic_relationship_matrix", "additive_model", "blup_solver"],
    }
    assert payload["provenance"]["input_summary"]["input_snapshot_at"] is not None
    assert payload["provenance"]["evidence_refs"][0]["entity_id"] == "fn:compute.gblup"
    assert payload["provenance"]["policy_flags"] == []
    assert lineage_entries == [
        {
            "lineage_record_id": payload["provenance"]["lineage_record_id"],
            "current_user": {"id": 1, "organization_id": 7, "email": "test@example.com"},
            "routine": "gblup",
            "output_kind": "breeding_values",
            "execution_mode": "sync",
            "status": "succeeded",
            "contract_version": "compute.v1",
            "input_summary": payload["provenance"]["input_summary"],
            "provenance": payload["provenance"],
            "policy_flags": [],
            "result_summary": {
                "breeding_value_count": 3,
                "mean": 2.8,
                "converged": True,
            },
        }
    ]
    assert audit_entries == [
        {
            "action": "COMPUTE",
            "target_type": "compute_run",
            "target_id": "gblup:sync",
            "organization_id": 7,
            "user_id": 1,
            "changes": {
                "routine": "gblup",
                "execution_mode": "sync",
                "status": "succeeded",
                "contract_version": "compute.v1",
                "lineage_record_id": payload["provenance"]["lineage_record_id"],
                "input_summary": payload["provenance"]["input_summary"],
                "policy_flags": [],
                "compute_time_ms": payload["compute_time_ms"],
            },
            "method": "POST",
        }
    ]


def test_gblup_surfaces_quality_flags_in_provenance(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_compute_gblup(*args: Any, **kwargs: Any) -> BLUPResult:
        return BLUPResult(
            fixed_effects=np.array([2.8]),
            breeding_values=np.array([0.12, -0.05, 0.08]),
            converged=False,
        )

    monkeypatch.setattr(compute_engine, "compute_gblup", fake_compute_gblup)

    response = client.post(
        "/api/v2/compute/gblup",
        json={
            "genotypes": [[0, 1, 2], [1, 1, 0], [2, 0, 1]],
            "phenotypes": [2.5, 3.1, 2.8],
            "heritability": 0.1,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["output"]["converged"] is False
    assert payload["provenance"]["policy_flags"] == ["low_heritability", "non_convergence_warning"]


def test_gblup_surfaces_input_provenance_metadata(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_compute_gblup(*args: Any, **kwargs: Any) -> BLUPResult:
        return BLUPResult(
            fixed_effects=np.array([2.8]),
            breeding_values=np.array([0.12, -0.05, 0.08]),
            converged=True,
        )

    monkeypatch.setattr(compute_engine, "compute_gblup", fake_compute_gblup)

    response = client.post(
        "/api/v2/compute/gblup",
        json={
            "genotypes": [[0, 1, 2]],
            "phenotypes": [2.5],
            "heritability": 0.05,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    input_summary = payload["provenance"]["input_summary"]
    assert input_summary["input_snapshot_at"] is not None
    assert input_summary["input_reliability_score"] == 0.55
    assert input_summary["calculation_method_identifiers"] == [
        "genomic_relationship_matrix",
        "additive_model",
        "blup_solver",
    ]


def test_grm_rejects_unsupported_method_with_structured_error(client: TestClient) -> None:
    response = client.post(
        "/api/v2/compute/grm",
        json={
            "genotypes": [[0, 1], [1, 0]],
            "method": "bogus",
        },
    )

    assert response.status_code == 422
    payload = response.json()
    assert payload["detail"]["contract_version"] == "compute.v1"
    assert payload["detail"]["code"] == "unsupported_method"
    assert payload["detail"]["routine"] == "grm"
    assert payload["detail"]["details"]["allowed_methods"] == ["vanraden1", "vanraden2", "yang"]


def test_reml_rejects_dimension_mismatch_with_structured_error(client: TestClient) -> None:
    response = client.post(
        "/api/v2/compute/reml",
        json={
            "phenotypes": [1.0, 2.0],
            "fixed_effects": [[1.0], [1.0]],
            "random_effects": [[1.0], [1.0]],
            "relationship_matrix": [[1.0, 0.1], [0.1, 1.0]],
            "var_additive_init": 0.5,
            "var_residual_init": 1.0,
            "method": "ai-reml",
            "max_iter": 25,
        },
    )

    assert response.status_code == 422
    payload = response.json()
    assert payload["detail"]["code"] == "invalid_input_shape"
    assert payload["detail"]["routine"] == "reml"
    assert payload["detail"]["message"] == "relationship_matrix dimensions must match random_effects columns."
    assert payload["detail"]["details"]["relationship_matrix_size"] == 2
    assert payload["detail"]["details"]["random_effects_columns"] == 1


def test_async_gblup_job_exposes_structured_failure(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    store: dict[str, dict[str, Any]] = {}
    audit_entries: list[dict[str, Any]] = []
    lineage_entries: list[dict[str, Any]] = []

    async def fake_create_job(job_type: str = "compute", metadata: dict[str, Any] | None = None) -> str:
        job_id = "job-1"
        store[job_id] = {
            "job_id": job_id,
            "job_type": job_type,
            "status": "pending",
            "progress": 0.0,
            "result": None,
            "error": None,
            "created_at": "2026-03-09T00:00:00+00:00",
            "updated_at": "2026-03-09T00:00:00+00:00",
            "completed_at": None,
            "metadata": metadata or {},
        }
        return job_id

    async def fake_update_job(
        job_id: str,
        status: Any = None,
        progress: float | None = None,
        result: dict[str, Any] | None = None,
        error: Any = None,
    ) -> bool:
        job = store[job_id]
        if status is not None:
            job["status"] = getattr(status, "value", status)
        if progress is not None:
            job["progress"] = progress
        if result is not None:
            job["result"] = result
        if error is not None:
            job["error"] = error
        job["updated_at"] = "2026-03-09T00:00:01+00:00"
        if job["status"] in {"completed", "failed"}:
            job["completed_at"] = "2026-03-09T00:00:01+00:00"
        return True

    async def fake_get_job(job_id: str) -> dict[str, Any] | None:
        return store.get(job_id)

    def fake_compute_gblup(*args: Any, **kwargs: Any) -> BLUPResult:
        raise RuntimeError("singular system")

    monkeypatch.setattr(compute_api.job_service, "create_job", fake_create_job)
    monkeypatch.setattr(compute_api.job_service, "update_job", fake_update_job)
    monkeypatch.setattr(compute_api.job_service, "get_job", fake_get_job)
    monkeypatch.setattr(compute_engine, "compute_gblup", fake_compute_gblup)
    monkeypatch.setattr(compute_api, "AsyncSessionLocal", lambda: _FakeAsyncSession(audit_entries))
    monkeypatch.setattr(compute_api, "_persist_compute_lineage", lambda **kwargs: _record_lineage(lineage_entries, **kwargs))

    submit_response = client.post(
        "/api/v2/compute/gblup/async",
        json={
            "genotypes": [[0, 1], [1, 0]],
            "phenotypes": [2.0, 2.4],
            "heritability": 0.5,
        },
    )

    assert submit_response.status_code == 200
    assert submit_response.json()["job_id"] == "job-1"
    lineage_record_id = submit_response.json()["lineage_record_id"]
    assert lineage_record_id is not None

    job_response = client.get("/api/v2/compute/jobs/job-1")

    assert job_response.status_code == 200
    payload = job_response.json()
    assert payload["contract_version"] == "compute.v1"
    assert payload["routine"] == "gblup"
    assert payload["lineage_record_id"] == lineage_record_id
    assert payload["status"] == "failed"
    assert payload["result"] is None
    assert payload["error"]["code"] == "computation_failed"
    assert payload["error"]["routine"] == "gblup"
    assert payload["error"]["details"]["exception_type"] == "RuntimeError"
    assert [entry["status"] for entry in lineage_entries] == ["pending", "running", "failed"]
    assert lineage_entries[0]["lineage_record_id"] == lineage_record_id
    assert lineage_entries[2]["error"]["code"] == "computation_failed"
    assert [entry["changes"]["status"] for entry in audit_entries] == ["accepted", "failed"]
    assert audit_entries[0]["target_type"] == "compute_job"
    assert audit_entries[0]["target_id"] == "job-1"
    assert audit_entries[1]["changes"]["error"]["code"] == "computation_failed"


def test_async_gblup_job_preserves_quality_flags_in_result(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    store: dict[str, dict[str, Any]] = {}
    audit_entries: list[dict[str, Any]] = []
    lineage_entries: list[dict[str, Any]] = []

    async def fake_create_job(job_type: str = "compute", metadata: dict[str, Any] | None = None) -> str:
        job_id = "job-2"
        store[job_id] = {
            "job_id": job_id,
            "job_type": job_type,
            "status": "pending",
            "progress": 0.0,
            "result": None,
            "error": None,
            "created_at": "2026-03-09T00:00:00+00:00",
            "updated_at": "2026-03-09T00:00:00+00:00",
            "completed_at": None,
            "metadata": metadata or {},
        }
        return job_id

    async def fake_update_job(
        job_id: str,
        status: Any = None,
        progress: float | None = None,
        result: dict[str, Any] | None = None,
        error: Any = None,
    ) -> bool:
        job = store[job_id]
        if status is not None:
            job["status"] = getattr(status, "value", status)
        if progress is not None:
            job["progress"] = progress
        if result is not None:
            job["result"] = result
        if error is not None:
            job["error"] = error
        job["updated_at"] = "2026-03-09T00:00:01+00:00"
        if job["status"] in {"completed", "failed"}:
            job["completed_at"] = "2026-03-09T00:00:01+00:00"
        return True

    async def fake_get_job(job_id: str) -> dict[str, Any] | None:
        return store.get(job_id)

    def fake_compute_gblup(*args: Any, **kwargs: Any) -> BLUPResult:
        return BLUPResult(
            fixed_effects=np.array([2.0]),
            breeding_values=np.array([0.3, -0.1]),
            converged=False,
        )

    monkeypatch.setattr(compute_api.job_service, "create_job", fake_create_job)
    monkeypatch.setattr(compute_api.job_service, "update_job", fake_update_job)
    monkeypatch.setattr(compute_api.job_service, "get_job", fake_get_job)
    monkeypatch.setattr(compute_engine, "compute_gblup", fake_compute_gblup)
    monkeypatch.setattr(compute_api, "AsyncSessionLocal", lambda: _FakeAsyncSession(audit_entries))
    monkeypatch.setattr(compute_api, "_persist_compute_lineage", lambda **kwargs: _record_lineage(lineage_entries, **kwargs))

    submit_response = client.post(
        "/api/v2/compute/gblup/async",
        json={
            "genotypes": [[0, 1], [1, 0]],
            "phenotypes": [2.0, 2.4],
            "heritability": 0.1,
        },
    )

    assert submit_response.status_code == 200
    assert submit_response.json()["job_id"] == "job-2"
    lineage_record_id = submit_response.json()["lineage_record_id"]
    assert lineage_record_id is not None

    job_response = client.get("/api/v2/compute/jobs/job-2")

    assert job_response.status_code == 200
    payload = job_response.json()
    assert payload["status"] == "completed"
    assert payload["lineage_record_id"] == lineage_record_id
    assert payload["result"]["output"]["converged"] is False
    assert payload["result"]["provenance"]["execution_mode"] == "async"
    assert payload["result"]["provenance"]["lineage_record_id"] == lineage_record_id
    assert payload["result"]["provenance"]["input_summary"]["input_snapshot_at"] is not None
    assert payload["result"]["provenance"]["input_summary"]["input_reliability_score"] == 0.55
    assert payload["result"]["provenance"]["input_summary"]["calculation_method_identifiers"] == [
        "genomic_relationship_matrix",
        "additive_model",
        "blup_solver",
    ]
    assert payload["result"]["provenance"]["policy_flags"] == ["low_heritability", "non_convergence_warning"]
    assert [entry["status"] for entry in lineage_entries] == ["pending", "running", "completed"]
    assert lineage_entries[2]["policy_flags"] == ["low_heritability", "non_convergence_warning"]
    assert [entry["changes"]["status"] for entry in audit_entries] == ["accepted", "completed"]
    assert audit_entries[1]["changes"]["policy_flags"] == ["low_heritability", "non_convergence_warning"]