"""Tests for chat routes."""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from fastapi.testclient import TestClient
from fastapi import FastAPI

from src.backend.api.deps import get_chat_service
from src.backend.api.routes.chat import chat_router
from src.shared.schemas import chat as chat_schema
from datetime import datetime


class TestChatRoutes:
    """Tests for chat routes."""

    @pytest.fixture
    def app(self, mock_chat_service):
        """Create a test FastAPI app."""
        app = FastAPI()
        app.include_router(chat_router)
        app.dependency_overrides[get_chat_service] = lambda: mock_chat_service
        return app

    @pytest.fixture
    def client(self, app):
        """Create a test client."""
        return TestClient(app)

    @pytest.fixture
    def mock_chat_service(self):
        """Mock chat service."""
        service = Mock()
        service.handle_chat = AsyncMock(return_value=chat_schema.ChatResponse(
            message_id=1,
            session_id=1,
            role=chat_schema.MessageRole.ASSISTANT,
            content="AI Response",
            created_at=datetime.now()
        ))
        service.get_history = AsyncMock(return_value=chat_schema.HistoryResponse(
            items=[],
            has_more=False,
            last_message_id=None
        ))
        return service

    def test_chat_route_defined(self, client):
        """Test chat route is defined."""
        response = client.post("/api/v1.0/chat", json={
            "session_id": 1,
            "content": "Hello"
        })
        # Route exists (may fail due to dependencies)
        assert response.status_code in [200, 422]

    def test_history_route_defined(self, client):
        """Test history route is defined."""
        response = client.get("/api/v1.0/chat/history")
        assert response.status_code == 200

    def test_chat_returns_200_on_success(self, client):
        """Test chat returns 200 on success."""
        response = client.post("/api/v1.0/chat", json={
            "session_id": 1,
            "content": "Hello"
        })
        assert response.status_code == 200

    def test_history_returns_200_on_success(self, client):
        """Test history returns 200 on success."""
        response = client.get("/api/v1.0/chat/history")
        assert response.status_code == 200

    def test_chat_with_missing_session_id(self, client):
        """Test chat with missing session_id returns validation error."""
        response = client.post("/api/v1.0/chat", json={
            "content": "Hello"
        })
        assert response.status_code == 422

    def test_chat_with_missing_content(self, client):
        """Test chat with missing content returns validation error."""
        response = client.post("/api/v1.0/chat", json={
            "session_id": 1
        })
        assert response.status_code == 422

    def test_chat_response_structure(self, client):
        """Test chat response has correct structure."""
        response = client.post("/api/v1.0/chat", json={
            "session_id": 1,
            "content": "Hello"
        })
        assert response.status_code == 200
        data = response.json()
        assert "message_id" in data
        assert "session_id" in data
        assert "role" in data
        assert "content" in data

    def test_history_response_structure(self, client):
        """Test history response has correct structure."""
        response = client.get("/api/v1.0/chat/history")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "has_more" in data
        assert "last_message_id" in data

    def test_chat_router_prefix(self):
        """Test chat router has correct prefix."""
        assert chat_router.prefix == "/api/v1.0/chat"

    def test_chat_endpoint_has_correct_method(self):
        """Test chat endpoint uses POST method."""
        chat_route = [r for r in chat_router.routes if hasattr(r, 'path') and r.path == "/api/v1.0/chat"]
        assert len(chat_route) > 0
        assert chat_route[0].methods == {'POST'}

    def test_history_endpoint_has_correct_method(self):
        """Test history endpoint uses GET method."""
        history_route = [r for r in chat_router.routes if hasattr(r, 'path') and 'history' in r.path]
        assert len(history_route) > 0
        assert 'GET' in history_route[0].methods

    def test_chat_with_model_id(self, client):
        """Test chat with model_id parameter."""
        response = client.post("/api/v1.0/chat", json={
            "session_id": 1,
            "content": "Hello",
            "model_id": "gpt-4o"
        })
        assert response.status_code == 200

    def test_chat_with_empty_content(self, client):
        """Test chat with empty content."""
        response = client.post("/api/v1.0/chat", json={
            "session_id": 1,
            "content": ""
        })
        # Should validate based on schema
        assert response.status_code == 422

    def test_chat_with_session_id_zero(self, client):
        """Test chat with session_id=0."""
        response = client.post("/api/v1.0/chat", json={
            "session_id": 0,
            "content": "Hello"
        })
        assert response.status_code == 200

    def test_chat_with_negative_session_id(self, client):
        """Test chat with negative session_id."""
        response = client.post("/api/v1.0/chat", json={
            "session_id": -1,
            "content": "Hello"
        })
        assert response.status_code == 200

    def test_history_without_params(self, client, mock_chat_service):
        """Test history without query parameters."""
        response = client.get("/api/v1.0/chat/history")
        mock_chat_service.get_history.assert_called_once()
