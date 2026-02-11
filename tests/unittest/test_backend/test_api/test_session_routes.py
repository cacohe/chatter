"""Tests for session routes."""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from fastapi.testclient import TestClient
from fastapi import FastAPI
from datetime import datetime

from src.backend.api.deps import get_session_service, get_current_active_user
from src.backend.api.routes.session import session_router
from src.shared.schemas.session import SessionRead
from src.shared.schemas import session as session_schema


class TestSessionRoutes:
    """Tests for session routes."""

    @pytest.fixture
    def app(self, mock_session_service, mock_current_user):
        """Create a test FastAPI app."""
        app = FastAPI()
        app.include_router(session_router)
        app.dependency_overrides[get_session_service] = lambda: mock_session_service
        app.dependency_overrides[get_current_active_user] = lambda: mock_current_user
        return app

    @pytest.fixture
    def client(self, app):
        """Create a test client."""
        return TestClient(app)

    @pytest.fixture
    def mock_session_service(self):
        """Mock session service."""
        service = Mock()
        service.create_session = AsyncMock(return_value=SessionRead(
            id=1,
            title="New Conversation",
            model_name="gpt-4o",
            created_at=datetime.now(),
            updated_at=datetime.now()
        ))
        service.rename_session = AsyncMock(return_value=True)
        service.get_history = AsyncMock(return_value=session_schema.SessionListResponse(
            sessions=[],
            total_count=0
        ))
        service.delete_session = AsyncMock(return_value=True)
        return service

    @pytest.fixture
    def mock_current_user(self):
        """Mock current user."""
        return Mock(id=123)

    def test_create_session_route_defined(self, client):
        """Test create session route is defined."""
        response = client.post("/api/v1.0/session/create")
        # Route exists
        assert response.status_code in [200, 401]

    def test_rename_session_route_defined(self, client):
        """Test rename session route is defined."""
        response = client.post("/api/v1.0/session/rename?new_title=New%20Title")
        # Route exists
        assert response.status_code in [200, 401]

    def test_get_history_route_defined(self, client):
        """Test get history route is defined."""
        response = client.get("/api/v1.0/session/history")
        # Route exists
        assert response.status_code in [200, 401]

    def test_delete_session_route_defined(self, client):
        """Test delete session route is defined."""
        response = client.post("/api/v1.0/session/delete", json={"session_id": 1})
        # Route exists
        assert response.status_code in [200, 401, 422]

    def test_create_session_returns_200_on_success(self, client):
        """Test create session returns 200 on success."""
        response = client.post("/api/v1.0/session/create")
        assert response.status_code == 200

    def test_rename_session_returns_200_on_success(self, client):
        """Test rename session returns 200 on success."""
        response = client.post("/api/v1.0/session/rename?new_title=New%20Title")
        assert response.status_code == 200

    def test_get_history_returns_200_on_success(self, client):
        """Test get history returns 200 on success."""
        response = client.get("/api/v1.0/session/history")
        assert response.status_code == 200

    def test_delete_session_returns_200_on_success(self, client):
        """Test delete session returns 200 on success."""
        response = client.post("/api/v1.0/session/delete", json={"session_id": 1})
        assert response.status_code == 200

    def test_create_session_response_structure(self, client):
        """Test create session response has correct structure."""
        response = client.post("/api/v1.0/session/create")
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert "title" in data
        assert "model_name" in data
        assert "created_at" in data
        assert "updated_at" in data

    def test_get_history_response_structure(self, client):
        """Test get history response has correct structure."""
        response = client.get("/api/v1.0/session/history")
        assert response.status_code == 200
        data = response.json()
        assert "sessions" in data
        assert "total_count" in data

    def test_session_router_prefix(self):
        """Test session router has correct prefix."""
        assert session_router.prefix == "/api/v1.0/session"

    def test_create_session_endpoint_has_correct_method(self):
        """Test create session endpoint uses POST method."""
        create_route = [r for r in session_router.routes if hasattr(r, 'path') and 'create' in r.path]
        assert len(create_route) > 0
        assert create_route[0].methods == {'POST'}

    def test_rename_session_endpoint_has_correct_method(self):
        """Test rename session endpoint uses POST method."""
        rename_route = [r for r in session_router.routes if hasattr(r, 'path') and 'rename' in r.path]
        assert len(rename_route) > 0
        assert rename_route[0].methods == {'POST'}

    def test_get_history_endpoint_has_correct_method(self):
        """Test get history endpoint uses GET method."""
        history_route = [r for r in session_router.routes if hasattr(r, 'path') and 'history' in r.path]
        assert len(history_route) > 0
        assert 'GET' in history_route[0].methods

    def test_delete_session_endpoint_has_correct_method(self):
        """Test delete session endpoint uses POST method."""
        delete_route = [r for r in session_router.routes if hasattr(r, 'path') and 'delete' in r.path]
        assert len(delete_route) > 0
        assert delete_route[0].methods == {'POST'}

    def test_rename_session_with_query_param(self, client, mock_session_service):
        """Test rename session with new_title query parameter."""
        response = client.post("/api/v1.0/session/rename?new_title=My%20Title")
        mock_session_service.rename_session.assert_called_once()

    def test_delete_session_with_missing_session_id(self, client):
        """Test delete session with missing session_id returns validation error."""
        response = client.post("/api/v1.0/session/delete", json={})
        assert response.status_code == 422

    def test_delete_session_with_zero_session_id(self, client):
        """Test delete session with session_id=0."""
        response = client.post("/api/v1.0/session/delete", json={"session_id": 0})
        assert response.status_code == 200

    def test_session_router_has_tags(self):
        """Test session router has tags."""
        assert session_router.tags == ["Session Management"]

    def test_get_history_empty_sessions(self, client, mock_session_service):
        """Test get history with empty sessions."""
        mock_session_service.get_history = AsyncMock(return_value=session_schema.SessionListResponse(
            sessions=[],
            total_count=0
        ))
        response = client.get("/api/v1.0/session/history")
        assert response.status_code == 200
        data = response.json()
        assert len(data["sessions"]) == 0
        assert data["total_count"] == 0

    def test_rename_session_with_unicode_title(self, client, mock_session_service):
        """Test rename session with unicode title."""
        response = client.post("/api/v1.0/session/rename?new_title=中文标题")
        mock_session_service.rename_session.assert_called_once()

    def test_create_session_uses_user_from_dependency(self, app, mock_session_service, mock_current_user):
        """Test create session uses user from dependency."""
        mock_current_user.id = "custom-user-id"
        app.dependency_overrides[get_current_active_user] = lambda: mock_current_user
        client = TestClient(app)
        response = client.post("/api/v1.0/session/create")
        mock_session_service.create_session.assert_called_once_with(user_id="custom-user-id")
