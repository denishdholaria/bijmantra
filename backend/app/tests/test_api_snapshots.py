import json
from pathlib import Path

from fastapi.testclient import TestClient

from app.tests.mocks.brapi_mock_server import app


SNAPSHOT_DIR = Path(__file__).parent / "snapshots"


client = TestClient(app)


def _snapshot_path(name: str) -> Path:
    return SNAPSHOT_DIR / f"{name}.json"


def _assert_snapshot(name: str, payload: dict):
    path = _snapshot_path(name)
    if not path.exists():
        path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    expected = json.loads(path.read_text(encoding="utf-8"))
    assert payload == expected


def test_serverinfo_snapshot():
    response = client.get('/brapi/v2/serverinfo')
    assert response.status_code == 200
    _assert_snapshot('serverinfo', response.json())


def test_programs_snapshot():
    response = client.get('/brapi/v2/programs')
    assert response.status_code == 200
    _assert_snapshot('programs', response.json())
