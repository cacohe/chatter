"""Tests for SessionService."""
from datetime import datetime

import pytest
from unittest.mock import Mock, AsyncMock, patch


# Add parent directories to path for imports
import sys
import os
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from src.backend.app.services.session import SessionService
from src.backend.domain.exceptions import BusinessException
from src.shared.schemas.session import SessionListResponse, SessionRead


class TestSessionService:
    """Tests for SessionService."""

    # Local fixtures moved to shared conftest.py for reuse and consistency

    def test_session_service_initialization(self, mock_session_repository):
        """Test SessionService initialization."""
        service = SessionService(session_repo=mock_session_repository)
        assert service.session_repo == mock_session_repository

    @pytest.mark.asyncio
    async def test_create_session_success(self, session_service, mock_session_repository, sample_session):
        """Test successful session creation."""
        mock_session_repository.create.return_value = sample_session
        result = await session_service.create_session(user_id="user-uuid-123")
        assert isinstance(result, SessionRead)
        assert result.id == sample_session.id
        assert result.title == sample_session.title
        assert result.model_name == sample_session.model_name

    @pytest.mark.asyncio
    async def test_create_session_with_repository_exception(self, session_service, mock_session_repository):
        """Test create_session handles repository exception."""
        mock_session_repository.create = AsyncMock(side_effect=Exception("Database error"))
        
        with pytest.raises(BusinessException) as exc_info:
            await session_service.create_session(user_id="user-uuid-123")
        assert "创建会话失败" in str(exc_info.value)

    @pytest.mark.asyncio
    @patch('src.backend.app.services.session.logger')
    async def test_create_session_logs_exception(self, mock_logger, session_service, mock_session_repository):
        """Test create_session logs exceptions."""
        mock_session_repository.create = AsyncMock(side_effect=Exception("Test error"))
        
        with pytest.raises(BusinessException):
            await session_service.create_session(user_id="user-uuid-123")
        assert mock_logger.exception.called

    @pytest.mark.asyncio
    async def test_create_session_default_title(self, session_service, mock_session_repository):
        """Test create_session uses default title."""
        mock_session = Mock(
            id=1,
            user_id="user-123",
            title="新对话",
            model_name="gpt-4o",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        mock_session.dict.return_value = {
            "id": 1,
            "user_id": "user-123",
            "title": "新对话",
            "model_name": "gpt-4o",
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }
        mock_session_repository.create.return_value = mock_session
        
        result = await session_service.create_session(user_id="user-uuid-123")
        
        assert isinstance(result, SessionRead)
        assert result.title == "新对话"

    @pytest.mark.asyncio
    async def test_rename_session_success(self, session_service, mock_session_repository):
        """Test successful session rename."""
        mock_session_repository.update_title.return_value = True
        
        result = await session_service.rename_session(session_id=1, new_title="New Title")
        
        assert result is True

    @pytest.mark.asyncio
    async def test_rename_session_empty_title(self, session_service):
        """Test rename session with empty title."""
        with pytest.raises(BusinessException) as exc_info:
            await session_service.rename_session(session_id=1, new_title="")
        assert "标题长度不合法" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_rename_session_none_title(self, session_service):
        """Test rename session with None title."""
        with pytest.raises(BusinessException) as exc_info:
            await session_service.rename_session(session_id=1, new_title=None)
        assert "标题长度不合法" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_rename_session_too_long(self, session_service):
        """Test rename session with title exceeding max length."""
        with pytest.raises(BusinessException) as exc_info:
            await session_service.rename_session(session_id=1, new_title="A" * 51)
        assert "标题长度不合法" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_rename_session_exactly_50_chars(self, session_service, mock_session_repository):
        """Test rename session with exactly 50 chars."""
        mock_session_repository.update_title.return_value = True
        
        result = await session_service.rename_session(session_id=1, new_title="A" * 50)
        
        assert result is True

    @pytest.mark.asyncio
    async def test_rename_session_whitespace_only(self, session_service):
        """Test rename session with whitespace only title."""
        with pytest.raises(BusinessException) as exc_info:
            await session_service.rename_session(session_id=1, new_title="   ")
        assert "标题长度不合法" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_rename_session_not_found(self, session_service, mock_session_repository):
        """Test rename session when session doesn't exist."""
        mock_session_repository.update_title.return_value = False
        
        with pytest.raises(BusinessException) as exc_info:
            await session_service.rename_session(session_id=1, new_title="New Title")
        
        assert "会话不存在或重命名失败" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_history_success(self, session_service, mock_session_repository, sample_session):
        """Test get_history returns sessions."""
        mock_session_repository.get_sessions_by_user.return_value = [sample_session]
        
        result = await session_service.get_history(user_id="user-uuid-123")
        
        assert isinstance(result, SessionListResponse)
        assert len(result.sessions) == 1
        assert result.total_count == 1

    @pytest.mark.asyncio
    async def test_get_history_empty_list(self, session_service, mock_session_repository):
        """Test get_history with empty session list."""
        mock_session_repository.get_sessions_by_user.return_value = []
        
        result = await session_service.get_history(user_id="user-uuid-123")
        
        assert isinstance(result, SessionListResponse)
        assert len(result.sessions) == 0
        assert result.total_count == 0

    @pytest.mark.asyncio
    async def test_get_history_multiple_sessions(self, session_service, mock_session_repository):
        """Test get_history with multiple sessions."""
        session1 = Mock(id=1, user_id="user-123", title="Session 1", model_name="gpt-4o", 
                     created_at=datetime.now(), updated_at=datetime.now())
        session1.dict.return_value = {
            "id": 1, "user_id": "user-123", "title": "Session 1", "model_name": "gpt-4o",
            "created_at": datetime.now(), "updated_at": datetime.now()
        }
        session2 = Mock(id=2, user_id="user-123", title="Session 2", model_name="gpt-3.5-turbo", 
                     created_at=datetime.now(), updated_at=datetime.now())
        session2.dict.return_value = {
            "id": 2, "user_id": "user-123", "title": "Session 2", "model_name": "gpt-3.5-turbo",
            "created_at": datetime.now(), "updated_at": datetime.now()
        }
        
        mock_session_repository.get_sessions_by_user.return_value = [session1, session2]
        
        result = await session_service.get_history(user_id="user-123")
        
        assert isinstance(result, SessionListResponse)
        assert len(result.sessions) == 2
        assert result.total_count == 2

    @pytest.mark.asyncio
    async def test_delete_session_success(self, session_service, mock_session_repository):
        """Test successful session deletion."""
        mock_session_repository.delete_by_user.return_value = True
        
        result = await session_service.delete_session(session_id=1, user_id=123)
        
        assert result is True

    @pytest.mark.asyncio
    async def test_delete_session_not_found(self, session_service, mock_session_repository):
        """Test delete session when session doesn't exist."""
        mock_session_repository.delete_by_user.return_value = False
        
        with pytest.raises(BusinessException) as exc_info:
            await session_service.delete_session(session_id=1, user_id=123)
        
        assert "删除失败，会话可能已被删除" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_delete_session_wrong_user(self, session_service, mock_session_repository):
        """Test delete session when user doesn't own session."""
        mock_session_repository.delete_by_user.return_value = False
        
        with pytest.raises(BusinessException) as exc_info:
            await session_service.delete_session(session_id=1, user_id=456)
        
        assert "删除失败，会话可能已被删除" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_delete_session_wrong_user(self, session_service, mock_session_repository):
        """Test delete session when user doesn't own session."""
        mock_session_repository.delete_by_user.return_value = False
        
        with pytest.raises(BusinessException) as exc_info:
            await session_service.delete_session(session_id=1, user_id=456)
        
        assert "删除失败，会话可能已被删除" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_delete_session_with_session_id_zero(self, session_service, mock_session_repository):
        """Test delete session with session_id=0."""
        mock_session_repository.delete_by_user.return_value = True
        
        result = await session_service.delete_session(session_id=0, user_id=123)
        
        assert result is True

    @pytest.mark.asyncio
    async def test_delete_session_with_negative_session_id(self, session_service, mock_session_repository):
        """Test delete session with negative session_id."""
        mock_session_repository.delete_by_user.return_value = True
        
        result = await session_service.delete_session(session_id=-1, user_id=123)
        
        assert result is True

    @pytest.mark.asyncio
    async def test_rename_session_unicode_title(self, session_service, mock_session_repository):
        """Test rename session with unicode title."""
        mock_session_repository.update_title.return_value = True
        
        result = await session_service.rename_session(session_id=1, new_title="中文标题")
        
        assert result is True

    @pytest.mark.asyncio
    async def test_rename_session_emoji_title(self, session_service, mock_session_repository):
        """Test rename session with emoji in title."""
        mock_session_repository.update_title.return_value = True
        
        result = await session_service.rename_session(session_id=1, new_title="🎉 Chat Title")
        
        assert result is True

    @pytest.mark.asyncio
    async def test_create_session_with_different_user_ids(self, session_service, mock_session_repository):
        """Test create session with different user IDs."""
        user_ids = ["user-1", "user-2", "user-3"]
        
        for i, user_id in enumerate(user_ids):
            mock_session = Mock(
                id=i+1,
                user_id=user_id,
                title="Test",
                model_name="gpt-4o",
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            mock_session.dict.return_value = {
                "id": i+1,
                "user_id": user_id,
                "title": "Test",
                "model_name": "gpt-4o",
                "created_at": datetime.now(),
                "updated_at": datetime.now()
            }
            mock_session_repository.create.return_value = mock_session
            result = await session_service.create_session(user_id=user_id)
            assert isinstance(result, SessionRead)

    @pytest.mark.asyncio
    async def test_get_history_total_count_matches_length(self, session_service, mock_session_repository):
        """Test get_history total_count matches actual session count."""
        session1 = Mock(id=1, user_id="user-123", title="Session 1", model_name="gpt-4o", 
                     created_at=datetime.now(), updated_at=datetime.now())
        session1.dict.return_value = {
            "id": 1, "user_id": "user-123", "title": "Session 1", "model_name": "gpt-4o",
            "created_at": datetime.now(), "updated_at": datetime.now()
        }
        session2 = Mock(id=2, user_id="user-123", title="Session 2", model_name="gpt-3.5-turbo", 
                     created_at=datetime.now(), updated_at=datetime.now())
        session2.dict.return_value = {
            "id": 2, "user_id": "user-123", "title": "Session 2", "model_name": "gpt-3.5-turbo",
            "created_at": datetime.now(), "updated_at": datetime.now()
        }
        sessions = [session1, session2]
        
        mock_session_repository.get_sessions_by_user.return_value = sessions
        
        result = await session_service.get_history(user_id="user-123")
        
        assert result.total_count == len(sessions)

    @pytest.mark.asyncio
    async def test_create_session_repository_exception_message(self, session_service, mock_session_repository):
        """Test create_session raises BusinessException with correct message."""
        mock_session_repository.create = AsyncMock(side_effect=Exception("Connection failed"))
        
        with pytest.raises(BusinessException) as exc_info:
            await session_service.create_session(user_id="user-uuid-123")
        assert "创建会话失败" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_delete_session_repository_exception_message(self, session_service, mock_session_repository):
        """Test delete_session raises BusinessException with correct message."""
        mock_session_repository.delete_by_user = AsyncMock(side_effect=Exception("Connection failed"))
        
        with pytest.raises(BusinessException) as exc_info:
            await session_service.delete_session(session_id=1, user_id=123)
        assert "删除失败，会话可能已被删除" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_rename_session_repository_exception_message(self, session_service, mock_session_repository):
        """Test rename_session raises BusinessException with correct message."""
        mock_session_repository.update_title = AsyncMock(side_effect=Exception("Connection failed"))
        
        with pytest.raises(BusinessException) as exc_info:
            await session_service.rename_session(session_id=1, new_title="New Title")
        assert "会话不存在或重命名失败" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_history_empty_user_id(self, session_service, mock_session_repository):
        """Test get_history with empty user_id."""
        mock_session_repository.get_sessions_by_user.return_value = []
        
        result = await session_service.get_history(user_id="")
        
        assert isinstance(result, SessionListResponse)
        assert len(result.sessions) == 0
        assert result.total_count == 0


# Removed: rely on centralized conftest.py fixtures for session_service
