"""Tests for AuthService."""

import pytest
import uuid
from unittest.mock import Mock, MagicMock, patch
from src.backend.app.services.auth import AuthService
from src.backend.domain.exceptions import AuthError
from src.shared.schemas import auth as auth_schema


class TestAuthService:
    """Tests for AuthService class."""

    @pytest.fixture
    def auth_service(self, mock_auth_repository):
        """Create an AuthService instance with mock repository."""
        return AuthService(auth_repo=mock_auth_repository)

    @pytest.fixture
    def user_create_request(self):
        """Sample user create request."""
        return auth_schema.UserCreate(
            email="test@example.com", password="Password123", username="testuser"
        )

    @pytest.fixture
    def login_request(self):
        """Sample login request."""
        return auth_schema.LoginRequest(
            email="test@example.com", password="Password123"
        )

    def test_auth_service_initialization(self, mock_auth_repository):
        """Test AuthService initialization."""
        service = AuthService(auth_repo=mock_auth_repository)
        assert service.auth_repo == mock_auth_repository

    def test_register_success(
        self, auth_service, mock_auth_repository, user_create_request
    ):
        """Test successful user registration."""
        test_uuid = "12345678-1234-1234-1234-123456789abc"
        mock_auth_repository.create_user.return_value = {
            "id": test_uuid,
            "email": "test@example.com",
            "username": "testuser",
        }

        result = auth_service.register(user_create_request)

        # Verify repository was called correctly
        mock_auth_repository.create_user.assert_called_once_with(
            email="test@example.com", password="Password123", username="testuser"
        )

        # Verify result
        assert isinstance(result, auth_schema.UserRegisterResponse)
        assert str(result.id) == test_uuid

    def test_register_with_repository_exception(
        self, auth_service, mock_auth_repository, user_create_request
    ):
        """Test register when repository raises exception."""
        mock_auth_repository.create_user.side_effect = Exception("Database error")

        with pytest.raises(AuthError) as exc_info:
            auth_service.register(user_create_request)

        assert "请稍后重试" in str(exc_info.value.message)

    def test_register_with_auth_error(
        self, auth_service, mock_auth_repository, user_create_request
    ):
        """Test register when repository raises AuthError."""
        mock_auth_repository.create_user.side_effect = AuthError("User already exists")

        with pytest.raises(AuthError) as exc_info:
            auth_service.register(user_create_request)

        assert "User already exists" in str(exc_info.value.message)

    def test_login_success(self, auth_service, mock_auth_repository, login_request):
        """Test successful login."""
        test_uuid = "12345678-1234-1234-1234-123456789abc"
        mock_session = MagicMock()
        mock_session.access_token = "access-token-123"
        mock_session.refresh_token = "refresh-token-123"
        mock_auth_user = MagicMock()
        mock_auth_user.id = test_uuid
        mock_auth_user.email = "test@example.com"
        mock_auth_user.username = "testuser"
        mock_auth_repository.authenticate.return_value = MagicMock(
            session=mock_session, user=mock_auth_user
        )

        result = auth_service.login(login_request)

        # Verify repository was called
        mock_auth_repository.authenticate.assert_called_once_with(
            email="test@example.com", password="Password123"
        )

        # Verify result
        assert isinstance(result, auth_schema.LoginResponse)
        assert result.access_token == "access-token-123"
        assert result.refresh_token == "refresh-token-123"
        assert result.token_type == "bearer"

    def test_login_with_invalid_credentials(
        self, auth_service, mock_auth_repository, login_request
    ):
        """Test login with invalid credentials."""
        mock_auth_repository.authenticate.side_effect = AuthError("Invalid credentials")

        with pytest.raises(AuthError) as exc_info:
            auth_service.login(login_request)

        assert "Invalid credentials" in str(exc_info.value.message)

    def test_login_with_repository_exception(
        self, auth_service, mock_auth_repository, login_request
    ):
        """Test login when repository raises generic exception."""
        mock_auth_repository.authenticate.side_effect = Exception("Database error")

        with pytest.raises(AuthError) as exc_info:
            auth_service.login(login_request)

        assert "请稍后重试" in str(exc_info.value.message)

    def test_get_current_user_success(self, auth_service, mock_auth_repository):
        """Test get_current_user with valid token."""
        test_uuid = "12345678-1234-1234-1234-123456789abc"
        mock_auth_repository.get_user_by_token.return_value = {
            "id": test_uuid,
            "email": "test@example.com",
            "username": "testuser",
            "avatar_url": None,
            "role": "user",
        }

        result = auth_service.get_current_user("valid-token-123")

        # Verify repository was called
        mock_auth_repository.get_user_by_token.assert_called_once_with(
            "valid-token-123"
        )

        # Verify result
        assert isinstance(result, auth_schema.UserInfo)
        assert str(result.id) == test_uuid
        assert result.email == "test@example.com"

    def test_get_current_user_with_invalid_token(
        self, auth_service, mock_auth_repository
    ):
        """Test get_current_user with invalid token."""
        mock_auth_repository.get_user_by_token.return_value = None

        with pytest.raises(AuthError) as exc_info:
            auth_service.get_current_user("invalid-token")

        assert "无效的会话或 Token 已过期" in str(exc_info.value.message)

    def test_get_current_user_with_repository_exception(
        self, auth_service, mock_auth_repository
    ):
        """Test get_current_user when repository raises exception."""
        mock_auth_repository.get_user_by_token.side_effect = Exception("Database error")

        with pytest.raises(AuthError) as exc_info:
            auth_service.get_current_user("token-123")

        assert "无效的会话或 Token 已过期" in str(exc_info.value.message)

    def test_logout_success(self, auth_service, mock_auth_repository):
        """Test successful logout."""
        result = auth_service.logout()

        # Verify repository was called
        mock_auth_repository.sign_out.assert_called_once()

        # Verify result
        assert isinstance(result, auth_schema.LogoutResponse)
        assert result.message == "已安全退出登录"

    def test_logout_with_repository_exception(self, auth_service, mock_auth_repository):
        """Test logout when repository raises exception."""
        mock_auth_repository.sign_out.side_effect = Exception("Logout error")

        with pytest.raises(AuthError) as exc_info:
            result = auth_service.logout()

        assert "Logout error" in exc_info.value.message

    @patch("src.backend.app.services.auth.logger")
    def test_register_logs_exception(
        self, mock_logger, auth_service, mock_auth_repository, user_create_request
    ):
        """Test register logs exception on failure."""
        mock_auth_repository.create_user.side_effect = Exception("Test error")

        with pytest.raises(AuthError):
            auth_service.register(user_create_request)

        # Verify logger was called
        assert mock_logger.exception.called

    @patch("src.backend.app.services.auth.logger")
    def test_login_logs_exception(
        self, mock_logger, auth_service, mock_auth_repository, login_request
    ):
        """Test login logs exception on failure."""
        mock_auth_repository.authenticate.side_effect = Exception("Test error")

        with pytest.raises(AuthError):
            auth_service.login(login_request)

        # Verify logger was called
        assert mock_logger.exception.called

    @patch("src.backend.app.services.auth.logger")
    def test_get_current_user_logs_exception(
        self, mock_logger, auth_service, mock_auth_repository
    ):
        """Test get_current_user logs exception on failure."""
        mock_auth_repository.get_user_by_token.side_effect = Exception("Test error")

        with pytest.raises(AuthError):
            auth_service.get_current_user("token")

        # Verify logger was called
        assert mock_logger.exception.called

    def test_register_with_different_email(self, auth_service, user_create_request):
        """Test register with different email."""
        user_create_request.email = "different@example.com"
        test_uuid = "12345678-1234-1234-1234-123456789abc"
        mock_repo = Mock()
        mock_repo.create_user = Mock(
            return_value={
                "id": test_uuid,
                "email": "different@example.com",
                "username": "testuser",
            }
        )
        service = AuthService(auth_repo=mock_repo)

        result = service.register(user_create_request)
        assert result.email == "different@example.com"

    def test_login_with_different_email(
        self, auth_service, mock_auth_repository, login_request
    ):
        """Test login with different email."""
        test_uuid = "12345678-1234-1234-1234-123456789abc"
        login_request.email = "another@example.com"
        mock_session = MagicMock()
        mock_session.access_token = "new-access-token"
        mock_session.refresh_token = "new-refresh-token"
        mock_auth_user = MagicMock()
        mock_auth_user.id = test_uuid
        mock_auth_user.email = "another@example.com"
        mock_auth_user.username = "testuser"
        mock_auth_repository.authenticate.return_value = MagicMock(
            session=mock_session, user=mock_auth_user
        )

        result = auth_service.login(login_request)
        assert result.access_token == "new-access-token"

    def test_login_returns_token_type_bearer(
        self, auth_service, mock_auth_repository, login_request
    ):
        """Test login returns correct token type."""
        test_uuid = "12345678-1234-1234-1234-123456789abc"
        mock_session = MagicMock()
        mock_session.access_token = "token"
        mock_session.refresh_token = "refresh"
        mock_auth_user = MagicMock()
        mock_auth_user.id = test_uuid
        mock_auth_user.email = "test@example.com"
        mock_auth_user.username = "testuser"
        mock_auth_repository.authenticate.return_value = MagicMock(
            session=mock_session, user=mock_auth_user
        )

        result = auth_service.login(login_request)
        assert result.token_type == "bearer"

    def test_register_with_empty_optional_fields(
        self, auth_service, user_create_request
    ):
        """Test register with None optional fields."""
        user_create_request.username = None
        test_uuid = "12345678-1234-1234-1234-123456789abc"
        mock_repo = Mock()
        mock_repo.create_user = Mock(
            return_value={
                "id": test_uuid,
                "email": "test@example.com",
                "username": None,
            }
        )
        service = AuthService(auth_repo=mock_repo)

        result = service.register(user_create_request)
        assert result.username is None

    def test_logout_message_chinese(self, auth_service):
        """Test logout returns Chinese message."""
        result = auth_service.logout()
        assert "安全退出" in result.message
