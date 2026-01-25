import pytest
from unittest.mock import MagicMock, AsyncMock
from app.integrations.brapi import BrAPIAdapter
from app.integrations.base import IntegrationConfig

@pytest.fixture
def mock_client():
    mock = AsyncMock()
    # Mock return value for requests
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"result": {"data": []}}
    mock_response.raise_for_status = MagicMock()

    # Ensure client.request returns the mock response when awaited
    mock.request.return_value = mock_response
    mock.get.return_value = mock_response
    mock.post.return_value = mock_response
    mock.put.return_value = mock_response
    return mock

@pytest.fixture
def adapter(mock_client):
    config = IntegrationConfig(base_url="http://test-brapi.org")
    adapter = BrAPIAdapter(config)
    adapter._client = mock_client
    return adapter

@pytest.mark.asyncio
async def test_make_request_get(adapter, mock_client):
    await adapter._make_request("GET", "test-endpoint")

    # We used client.request, not client.get
    mock_client.request.assert_called_once()
    args, kwargs = mock_client.request.call_args
    # args: (method, url)
    assert args[0] == "GET"
    assert args[1] == "http://test-brapi.org/brapi/v2/test-endpoint"

@pytest.mark.asyncio
async def test_make_request_post(adapter, mock_client):
    data = {"key": "value"}
    await adapter._make_request("POST", "test-endpoint", json=data)

    mock_client.request.assert_called_once()
    args, kwargs = mock_client.request.call_args
    assert args[0] == "POST"
    assert args[1] == "http://test-brapi.org/brapi/v2/test-endpoint"
    assert kwargs['json'] == data

@pytest.mark.asyncio
async def test_push_data_germplasm(adapter, mock_client):
    data = [{"germplasmName": "Wheat1"}]
    await adapter.push_data("germplasm", data)

    # Should call POST /brapi/v2/germplasm
    mock_client.request.assert_called()
    args, kwargs = mock_client.request.call_args
    assert args[0] == "POST"
    assert "/brapi/v2/germplasm" in args[1]
    assert kwargs['json'] == data

@pytest.mark.asyncio
async def test_push_data_programs(adapter, mock_client):
    data = [{"programName": "Breeding Program 1"}]
    await adapter.push_data("programs", data)

    mock_client.request.assert_called()
    args, kwargs = mock_client.request.call_args
    assert args[0] == "POST"
    assert "/brapi/v2/programs" in args[1]
    assert kwargs['json'] == data

@pytest.mark.asyncio
async def test_get_programs_refactored(adapter, mock_client):
    # This tests the existing method, which we will refactor to use _make_request
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"result": {"data": [{"programDbId": "1"}]}}

    # IMPORTANT: mocking request because get_programs uses _make_request which uses request
    mock_client.request.return_value = mock_response

    result = await adapter.get_programs()
    assert len(result) == 1
    assert result[0]["programDbId"] == "1"
