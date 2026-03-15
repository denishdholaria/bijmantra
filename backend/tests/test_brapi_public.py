"""
Tests for BrAPI v2 public endpoints (no auth required).
"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import pytest
from fastapi.testclient import TestClient
from app import main
from app.main import app


class TestServerInfo:
    """Tests for /brapi/v2/serverinfo endpoint."""

    def test_get_serverinfo_returns_200(self):
        """Test that serverinfo endpoint returns 200."""
        with TestClient(app) as client:
            response = client.get("/brapi/v2/serverinfo")
            assert response.status_code == 200

    def test_serverinfo_has_correct_structure(self):
        """Test that serverinfo response has BrAPI structure."""
        with TestClient(app) as client:
            response = client.get("/brapi/v2/serverinfo")
            data = response.json()

            # Check BrAPI response structure
            assert "metadata" in data
            assert "result" in data

            # Check result fields
            result = data["result"]
            assert "serverName" in result
            assert "organizationName" in result

    def test_serverinfo_contains_bijmantra(self):
        """Test that serverinfo identifies as Bijmantra."""
        with TestClient(app) as client:
            response = client.get("/brapi/v2/serverinfo")
            result = response.json()["result"]

            assert "Bijmantra" in result["serverName"]


class TestHealthEndpoint:
    """Tests for /health endpoint."""

    def test_health_returns_200(self):
        """Test health endpoint returns 200."""
        with TestClient(app) as client:
            response = client.get("/health")
            assert response.status_code == 200

    def test_health_returns_status(self):
        """Test health endpoint returns status information."""
        with TestClient(app) as client:
            response = client.get("/health")
            data = response.json()
            assert "status" in data

    def test_health_reports_all_dependency_surfaces(self, monkeypatch: pytest.MonkeyPatch):
        """Test health endpoint reports core dependency surfaces."""

        async def healthy_probe() -> dict:
            return {"status": "healthy", "critical": False}

        monkeypatch.setattr(main, "_probe_postgres_health", lambda: _async_result({"status": "healthy", "critical": True}))
        monkeypatch.setattr(main, "_probe_redis_health", healthy_probe)
        monkeypatch.setattr(main, "_probe_meilisearch_health", healthy_probe)
        monkeypatch.setattr(main, "_probe_task_queue_health", healthy_probe)

        with TestClient(app) as client:
            response = client.get("/health")

        data = response.json()
        assert data["status"] == "healthy"
        assert set(data["dependencies"].keys()) == {"postgres", "redis", "meilisearch", "task_queue"}

    def test_health_reports_degraded_when_optional_dependency_fails(self, monkeypatch: pytest.MonkeyPatch):
        """Test health endpoint degrades when an optional dependency is unavailable."""

        monkeypatch.setattr(main, "_probe_postgres_health", lambda: _async_result({"status": "healthy", "critical": True}))
        monkeypatch.setattr(main, "_probe_redis_health", lambda: _async_result({"status": "healthy", "critical": False}))
        monkeypatch.setattr(main, "_probe_meilisearch_health", lambda: _async_result({"status": "healthy", "critical": False}))
        monkeypatch.setattr(
            main,
            "_probe_task_queue_health",
            lambda: _async_result({"status": "degraded", "critical": False, "detail": "task queue not running"}),
        )

        with TestClient(app) as client:
            response = client.get("/health")

        data = response.json()
        assert data["status"] == "degraded"
        assert data["dependencies"]["task_queue"]["status"] == "degraded"

    def test_health_reports_critical_when_postgres_fails(self, monkeypatch: pytest.MonkeyPatch):
        """Test health endpoint becomes critical when PostgreSQL is unavailable."""

        monkeypatch.setattr(
            main,
            "_probe_postgres_health",
            lambda: _async_result({"status": "critical", "critical": True, "error": "database unavailable"}),
        )
        monkeypatch.setattr(main, "_probe_redis_health", lambda: _async_result({"status": "healthy", "critical": False}))
        monkeypatch.setattr(main, "_probe_meilisearch_health", lambda: _async_result({"status": "healthy", "critical": False}))
        monkeypatch.setattr(main, "_probe_task_queue_health", lambda: _async_result({"status": "healthy", "critical": False}))

        with TestClient(app) as client:
            response = client.get("/health")

        data = response.json()
        assert data["status"] == "critical"
        assert data["dependencies"]["postgres"]["status"] == "critical"


class TestRootEndpoint:
    """Tests for root / endpoint."""

    def test_root_returns_200(self):
        """Test root endpoint returns 200."""
        with TestClient(app) as client:
            response = client.get("/")
            assert response.status_code == 200

    def test_root_returns_welcome(self):
        """Test root endpoint returns welcome message."""
        with TestClient(app) as client:
            response = client.get("/")
            data = response.json()
            assert "message" in data or "status" in data


async def _async_result(value: dict) -> dict:
    return value
