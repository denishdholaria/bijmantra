from fastapi.testclient import TestClient

from app.tests.mocks.brapi_mock_server import app


client = TestClient(app)


def test_serverinfo_response_shape():
    response = client.get('/brapi/v2/serverinfo')
    assert response.status_code == 200
    payload = response.json()
    assert 'metadata' in payload
    assert 'result' in payload
    assert payload['result']['serverName'] == 'Mock BrAPI'


def test_programs_endpoint_returns_data_rows():
    response = client.get('/brapi/v2/programs')
    assert response.status_code == 200
    payload = response.json()
    assert payload['result']['data'][0]['programDbId'] == 'P-1'
