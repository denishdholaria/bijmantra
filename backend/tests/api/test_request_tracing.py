from fastapi.testclient import TestClient

from app.main import app
from app.middleware.request_tracing import TRACE_ID_HEADER


def test_root_returns_generated_trace_id_header():
    with TestClient(app) as client:
        response = client.get("/")

    assert response.status_code == 200
    trace_id = response.headers.get(TRACE_ID_HEADER)
    assert trace_id is not None
    assert len(trace_id) == 32


def test_root_echoes_client_trace_id_header():
    client_trace_id = "frontend-trace-12345678"

    with TestClient(app) as client:
        response = client.get("/", headers={TRACE_ID_HEADER: client_trace_id})

    assert response.status_code == 200
    assert response.headers.get(TRACE_ID_HEADER) == client_trace_id


def test_root_uses_sentry_trace_header_when_present():
    propagated_trace_id = "0123456789abcdef0123456789abcdef"

    with TestClient(app) as client:
        response = client.get(
            "/",
            headers={"sentry-trace": f"{propagated_trace_id}-0123456789abcdef-1"},
        )

    assert response.status_code == 200
    assert response.headers.get(TRACE_ID_HEADER) == propagated_trace_id