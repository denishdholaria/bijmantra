"""
Tests for Veena AI Chat Streaming Endpoint

Tests the /api/v2/chat/stream SSE endpoint.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from starlette.testclient import TestClient


class TestChatStreamingEndpoint:
    """Test cases for the streaming chat endpoint"""

    @pytest.fixture
    def client(self):
        """Create test client"""
        from app.main import app
        with TestClient(app) as client:
            yield client

    @pytest.fixture
    def mock_llm_service(self):
        """Mock the LLM service"""
        with patch('app.api.v2.chat.get_llm_service') as mock:
            service = MagicMock()
            
            # Mock get_status
            async def mock_status():
                return {
                    "active_provider": "template",
                    "active_model": "template-v1",
                    "providers": {
                        "template": {"available": True}
                    }
                }
            service.get_status = mock_status
            
            # Mock stream_chat as async generator
            async def mock_stream_chat(*args, **kwargs):
                yield "Hello"
                yield " from"
                yield " Veena!"
            
            service.stream_chat = mock_stream_chat
            mock.return_value = service
            yield service

    @pytest.fixture
    def mock_breeding_service(self):
        """Mock the breeding service"""
        with patch('app.api.v2.chat.get_breeding_service') as mock:
            service = MagicMock()
            
            async def mock_search(*args, **kwargs):
                return []
            
            service.search_breeding_knowledge = mock_search
            mock.return_value = service
            yield service

    def test_streaming_endpoint_returns_200(self, client):
        """Test that streaming endpoint returns 200 OK"""
        response = client.post(
            '/api/v2/chat/stream',
            json={'message': 'Hello', 'include_context': False}
        )
        assert response.status_code == 200

    def test_streaming_endpoint_returns_sse_content_type(self, client):
        """Test that streaming endpoint returns correct SSE content type"""
        response = client.post(
            '/api/v2/chat/stream',
            json={'message': 'Hello', 'include_context': False}
        )
        assert 'text/event-stream' in response.headers.get('content-type', '')

    def test_streaming_endpoint_has_no_cache_header(self, client):
        """Test that streaming endpoint has proper cache control"""
        response = client.post(
            '/api/v2/chat/stream',
            json={'message': 'Hello', 'include_context': False}
        )
        cache_control = response.headers.get('cache-control', '')
        assert 'no-cache' in cache_control or 'no-store' in cache_control

    def test_streaming_endpoint_disables_buffering(self, client):
        """Test that streaming endpoint disables nginx buffering"""
        response = client.post(
            '/api/v2/chat/stream',
            json={'message': 'Hello', 'include_context': False}
        )
        assert response.headers.get('x-accel-buffering') == 'no'

    def test_streaming_format_has_start_event(self, client):
        """Test that SSE stream starts with a 'start' event"""
        response = client.post(
            '/api/v2/chat/stream',
            json={'message': 'Hello', 'include_context': False}
        )
        # First line should be the start event
        lines = response.text.split('\n\n')
        assert len(lines) > 0
        first_event = lines[0]
        assert 'data: ' in first_event
        assert '"type": "start"' in first_event or '"type":"start"' in first_event

    def test_streaming_format_has_chunk_events(self, client):
        """Test that content is sent as 'chunk' events"""
        response = client.post(
            '/api/v2/chat/stream',
            json={'message': 'Hello', 'include_context': False}
        )
        # Should have chunk events
        assert '"type": "chunk"' in response.text or '"type":"chunk"' in response.text

    def test_streaming_format_has_done_event(self, client):
        """Test that SSE stream ends with a 'done' event"""
        response = client.post(
            '/api/v2/chat/stream',
            json={'message': 'Hello', 'include_context': False}
        )
        # Last data event should be done
        assert '"type": "done"' in response.text or '"type":"done"' in response.text

    def test_streaming_with_conversation_history(self, client):
        """Test streaming with conversation history"""
        response = client.post(
            '/api/v2/chat/stream',
            json={
                'message': 'What about disease resistance?',
                'include_context': False,
                'conversation_history': [
                    {'role': 'user', 'content': 'Tell me about wheat'},
                    {'role': 'assistant', 'content': 'Wheat is a cereal grain...'}
                ]
            }
        )
        assert response.status_code == 200

    def test_streaming_with_preferred_provider(self, client):
        """Test streaming with preferred provider"""
        response = client.post(
            '/api/v2/chat/stream',
            json={
                'message': 'Hello',
                'include_context': False,
                'preferred_provider': 'ollama'
            }
        )
        assert response.status_code == 200


class TestStreamChatMethod:
    """Test the stream_chat method in LLM service"""

    def test_stream_chat_method_exists(self):
        """Test that stream_chat method exists on LLM service"""
        from app.services.llm_service import MultiTierLLMService
        service = MultiTierLLMService()
        assert hasattr(service, 'stream_chat')
        assert callable(service.stream_chat)

    def test_streaming_methods_exist_for_providers(self):
        """Test that streaming methods exist for all supported providers"""
        from app.services.llm_service import MultiTierLLMService
        service = MultiTierLLMService()
        
        streaming_methods = [
            '_stream_ollama',
            '_stream_groq',
            '_stream_google',
            '_stream_openai',
            '_stream_anthropic'
        ]
        
        for method in streaming_methods:
            assert hasattr(service, method), f"Missing streaming method: {method}"


# Run with: python -m pytest tests/units/api/v2/test_chat_streaming.py -v
