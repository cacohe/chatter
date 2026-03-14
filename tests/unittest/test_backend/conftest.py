import pytest
from unittest.mock import AsyncMock, Mock
from src.backend.domain.repository_interfaces.session import ISessionRepository
from src.backend.domain.repository_interfaces.auth import IAuthRepository
from src.backend.app.services.session import SessionService


@pytest.fixture
def mock_session_repository():
    repo = Mock(spec=ISessionRepository)
    # Common async methods with sensible defaults
    repo.create = AsyncMock(
        return_value=Mock(
            id=1,
            user_id="user-uuid-123",
            title="Test",
            model_name="gpt-4o",
            created_at=None,
            updated_at=None,
        )
    )
    repo.update_title = AsyncMock(return_value=True)
    repo.update_session_model = AsyncMock(return_value=True)
    repo.get_sessions_by_user = AsyncMock(return_value=[])
    repo.get_session_by_id = AsyncMock(return_value=None)
    repo.delete_by_user = AsyncMock(return_value=True)
    return repo


@pytest.fixture
def mock_chat_repository():
    return Mock()


@pytest.fixture
def mock_auth_repository():
    repo = Mock(spec=IAuthRepository)
    test_uuid = "12345678-1234-1234-1234-123456789abc"
    repo.create_user = Mock(
        return_value={
            "id": test_uuid,
            "email": "test@example.com",
            "username": "testuser",
        }
    )
    repo.authenticate = Mock(
        return_value=Mock(
            session=Mock(
                access_token="access-token-123", refresh_token="refresh-token-123"
            ),
            user=Mock(id=test_uuid, email="test@example.com", username="testuser"),
        )
    )
    repo.get_user_by_token = Mock(
        return_value={
            "id": test_uuid,
            "email": "test@example.com",
            "username": "testuser",
            "avatar_url": None,
            "role": "user",
        }
    )
    repo.sign_out = Mock()
    return repo


@pytest.fixture
def sample_session():
    from datetime import datetime

    s = Mock(
        id=1,
        user_id="user-uuid-123",
        title="Test",
        model_name="gpt-4o",
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    s.dict.return_value = {
        "id": 1,
        "user_id": "user-uuid-123",
        "title": "Test",
        "model_name": "gpt-4o",
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
    }
    return s


@pytest.fixture
def session_service(mock_session_repository):
    # SessionService only takes session_repo parameter
    return SessionService(session_repo=mock_session_repository)


@pytest.fixture
def mock_logger():
    return Mock()
