"""Tests for auth routes."""
import pytest
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
from fastapi import FastAPI

from src.backend.api.deps import get_auth_service
from src.backend.api.routes.auth import auth_router
from src.shared.schemas import auth as auth_schema
from datetime import datetime


class TestAuthRoutes:
    """Tests for authentication routes."""

    @pytest.fixture
    def app(self, mock_auth_service):
        """Create a test FastAPI app."""
        app = FastAPI()
        app.include_router(auth_router)
        app.dependency_overrides[get_auth_service] = lambda: mock_auth_service
        return app

    @pytest.fixture
    def client(self, app):
        """Create a test client."""
        return TestClient(app)

    @pytest.fixture
    def mock_auth_service(self):
        with patch('src.backend.api.routes.auth.get_auth_service') as mock_auth_service:
            mock_auth_service.register = Mock(return_value=auth_schema.UserRegisterResponse(
                id=123,
                email="test@example.com",
                username="testuser",
                created_at=datetime.now()
            ))
            mock_auth_service.login = Mock(return_value=auth_schema.LoginResponse(
                access_token="access-token-123",
                refresh_token="refresh-token-123",
                token_type="bearer"
            ))
            mock_auth_service.logout = Mock(return_value=auth_schema.LogoutResponse(message="已安全退出登录"))
            mock_auth_service.get_current_user = Mock(return_value=auth_schema.UserInfo(
                id=123,
                email="test@example.com",
                username="testuser",
                created_at=datetime.utcnow()
            ))
            return mock_auth_service

    def test_register_route_defined(self, client):
        """Test register route is defined."""
        response = client.post("/api/v1.0/auth/register", json={
            "email": "test@example.com",
            "password": "password123",
            "username": "testuser"
        })
        # Will fail due to dependency injection, but route exists
        assert response.status_code in [201, 422]

    def test_login_route_defined(self, client):
        """Test login route is defined."""
        response = client.post("/api/v1.0/auth/login", json={
            "email": "test@example.com",
            "password": "password123"
        })
        # Will fail due to dependency injection, but route exists
        assert response.status_code in [200, 422]

    def test_me_route_defined(self, client):
        """Test /me route is defined."""
        response = client.get("/api/v1.0/auth/me")
        # Will fail due to auth, but route exists
        assert response.status_code == 401

    def test_logout_route_defined(self, client):
        """Test logout route is defined."""
        response = client.post("/api/v1.0/auth/logout")
        # Will fail due to dependency injection, but route exists
        assert response.status_code in [200, 422]

    def test_register_returns_201_on_success(self, client):
        response = client.post(
            "/api/v1.0/auth/register",
            json={
                'email': "test@example.com",
                'username': "new_username",
                'password': "new_password"
            }
        )

        assert response.status_code == 201

    def test_login_returns_200_on_success(self, client):
        """Test login returns 200 on success."""
        response = client.post("/api/v1.0/auth/login", json={
            "email": "test@example.com",
            "password": "password123"
        })
        assert response.status_code == 200

    def test_me_returns_200_on_success(self, client):
        """Test /me returns 200 on success."""
        response = client.get("/api/v1.0/auth/me", headers={
            "Authorization": "Bearer test-token"
        })
        assert response.status_code == 200

    def test_logout_returns_200_on_success(self, client):
        """Test logout returns 200 on success."""
        response = client.post("/api/v1.0/auth/logout")
        assert response.status_code == 200

    def test_register_with_missing_email(self, client):
        """Test register with missing email returns validation error."""
        response = client.post("/api/v1.0/auth/register", json={
            "password": "password123",
            "username": "testuser"
        })
        assert response.status_code == 422

    def test_register_with_missing_password(self, client):
        """Test register with missing password returns validation error."""
        response = client.post("/api/v1.0/auth/register", json={
            "email": "test@example.com",
            "username": "testuser"
        })
        assert response.status_code == 422

    def test_login_with_missing_email(self, client):
        """Test login with missing email returns validation error."""
        response = client.post("/api/v1.0/auth/login", json={
            "password": "password123"
        })
        assert response.status_code == 422

    def test_login_with_missing_password(self, client):
        """Test login with missing password returns validation error."""
        response = client.post("/api/v1.0/auth/login", json={
            "email": "test@example.com"
        })
        assert response.status_code == 422

    def test_register_response_structure(self, client):
        """Test register response has correct structure."""
        response = client.post("/api/v1.0/auth/register", json={
            "email": "test@example.com",
            "password": "password123",
            "username": "testuser"
        })
        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        assert "email" in data
        assert "username" in data

    def test_login_response_structure(self, client):
        """Test login response has correct structure."""
        response = client.post("/api/v1.0/auth/login", json={
            "email": "test@example.com",
            "password": "password123"
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert "token_type" in data
        assert data["token_type"] == "bearer"

    def test_logout_response_structure(self, client):
        """Test logout response has correct structure."""
        response = client.post("/api/v1.0/auth/logout")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data

    def test_auth_router_prefix(self):
        """Test auth router has correct prefix."""
        assert auth_router.prefix == "/api/v1.0/auth"

    def test_register_endpoint_has_correct_method(self):
        """Test register endpoint uses POST method."""
        register_route = [r for r in auth_router.routes if hasattr(r, 'path') and 'register' in r.path]
        assert len(register_route) > 0
        assert register_route[0].methods == {'POST'}

    def test_login_endpoint_has_correct_method(self):
        """Test login endpoint uses POST method."""
        login_route = [r for r in auth_router.routes if hasattr(r, 'path') and 'login' in r.path]
        assert len(login_route) > 0
        assert login_route[0].methods == {'POST'}

    def test_me_endpoint_has_correct_method(self):
        """Test /me endpoint uses GET method."""
        me_route = [r for r in auth_router.routes if hasattr(r, 'path') and '/me' in r.path]
        assert len(me_route) > 0
        assert 'GET' in me_route[0].methods

    def test_logout_endpoint_has_correct_method(self):
        """Test logout endpoint uses POST method."""
        logout_route = [r for r in auth_router.routes if hasattr(r, 'path') and 'logout' in r.path]
        assert len(logout_route) > 0
        assert logout_route[0].methods == {'POST'}

    def test_register_with_invalid_email_format(self, client):
        """Test register with invalid email format."""
        response = client.post("/api/v1.0/auth/register", json={
            "email": "invalid-email",
            "password": "password123",
            "username": "testuser"
        })
        assert response.status_code == 422

    def test_me_without_token(self, app, mock_auth_service):
        """Test /me without token returns 401."""
        app.dependency_overrides[get_auth_service] = lambda: mock_auth_service
        client = TestClient(app)
        response = client.get("/api/v1.0/auth/me")
        # Should handle auth error
        assert response.status_code == 401
