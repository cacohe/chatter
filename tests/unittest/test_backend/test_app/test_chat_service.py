"""Tests for ChatService."""
import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from src.backend.app.services.chat import ChatService
from src.backend.domain.exceptions import BusinessException
from src.shared.schemas import chat as chat_schema
from datetime import datetime


class TestChatService:
    """Tests for ChatService class."""

    @pytest.fixture
    def chat_service(self, mock_chat_repository, mock_session_repository):
        """Create a ChatService instance with mock repositories."""
        return ChatService(chat_repo=mock_chat_repository, session_repo=mock_session_repository)

    @pytest.fixture
    def chat_request(self):
        """Sample chat request."""
        return chat_schema.ChatRequest(
            session_id=1,
            content="Hello, how are you?",
            model_id="gpt-4o"
        )

    @pytest.fixture
    def sample_message(self):
        """Sample message."""
        return Mock(
            id=1,
            session_id=1,
            role="user",
            content="Hello",
            created_at=datetime.now()
        )

    @pytest.fixture
    def sample_ai_message(self):
        """Sample AI message."""
        return Mock(
            id=2,
            session_id=1,
            role="assistant",
            content="I'm fine!",
            created_at=datetime.now()
        )

    @pytest.fixture
    def sample_session(self):
        """Sample session."""
        return Mock(
            id=1,
            user_id="user-123",
            title="Test",
            active_model_id="gpt-4o",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

    def test_chat_service_initialization(self, mock_chat_repository, mock_session_repository):
        """Test ChatService initialization."""
        service = ChatService(chat_repo=mock_chat_repository, session_repo=mock_session_repository)
        assert service.chat_repo == mock_chat_repository
        assert service.session_repo == mock_session_repository

    @pytest.mark.asyncio
    async def test_handle_chat_success(self, chat_service, mock_chat_repository, mock_session_repository,
                                         chat_request, sample_message, sample_ai_message, sample_session):
        """Test successful chat handling."""
        mock_chat_repository.save_message = AsyncMock(side_effect=[sample_message, Mock(
            id=2,
            session_id=1,
            role="assistant",
            content="AI Response",  # This should match what adapter.chat() returns
            created_at=datetime.now()
        )])
        mock_chat_repository.get_recent_messages = AsyncMock(return_value=[sample_message])
        mock_session_repository.get_session_by_id = AsyncMock(return_value=sample_session)

        with patch('src.backend.app.services.chat.LLMFactory') as mock_factory, \
             patch('src.backend.app.services.chat.ModelRegistry') as mock_registry, \
             patch('src.backend.app.services.chat.settings') as mock_settings:
            mock_registry.exists.return_value = True
            mock_adapter = AsyncMock()
            mock_adapter.chat = AsyncMock(return_value="AI Response")
            mock_factory.get_instance.return_value = mock_adapter
            mock_settings.context_limit = 10
            mock_settings.default_llm = "gpt-3.5-turbo"

            result = await chat_service.handle_chat(chat_request)

            # Verify result - content should come from adapter.chat() response
            assert isinstance(result, chat_schema.ChatResponse)
            assert result.content == "AI Response"  # This comes from mock_adapter.chat()
            assert result.role == chat_schema.MessageRole.ASSISTANT

    @pytest.mark.asyncio
    async def test_handle_chat_saves_user_message(self, chat_service, mock_chat_repository, mock_session_repository,
                                                     chat_request, sample_message, sample_ai_message):
        """Test handle_chat saves user message."""
        mock_chat_repository.save_message = AsyncMock(side_effect=[sample_message, sample_ai_message])
        mock_chat_repository.get_recent_messages = AsyncMock(return_value=[])
        mock_session_repository.get_session_by_id = AsyncMock(return_value=None)

        with patch('src.backend.app.services.chat.LLMFactory') as mock_factory, \
             patch('src.backend.app.services.chat.ModelRegistry') as mock_registry, \
             patch('src.backend.app.services.chat.settings') as mock_settings:
            mock_registry.exists.return_value = True
            mock_adapter = AsyncMock()
            mock_adapter.chat = AsyncMock(return_value="Response")
            mock_factory.get_instance.return_value = mock_adapter
            mock_settings.context_limit = 10
            mock_settings.default_llm = "gpt-3.5-turbo"

            await chat_service.handle_chat(chat_request)

            # Verify user message was saved
            assert mock_chat_repository.save_message.call_count >= 2
            first_call = mock_chat_repository.save_message.call_args_list[0]
            assert first_call[1]['role'] == chat_schema.MessageRole.USER

    @pytest.mark.asyncio
    async def test_handle_chat_saves_ai_response(self, chat_service, mock_chat_repository, mock_session_repository, chat_request,
                                                   sample_message, sample_ai_message):
        """Test handle_chat saves AI response."""
        mock_chat_repository.save_message = AsyncMock(side_effect=[sample_message, sample_ai_message])
        mock_chat_repository.get_recent_messages = AsyncMock(return_value=[])
        mock_session_repository.get_session_by_id = AsyncMock(return_value=None)

        with patch('src.backend.app.services.chat.LLMFactory') as mock_factory, \
             patch('src.backend.app.services.chat.ModelRegistry') as mock_registry, \
             patch('src.backend.app.services.chat.settings') as mock_settings:
            mock_registry.exists.return_value = True
            mock_adapter = AsyncMock()
            mock_adapter.chat = AsyncMock(return_value="Response")
            mock_factory.get_instance.return_value = mock_adapter
            mock_settings.context_limit = 10
            mock_settings.default_llm = "gpt-3.5-turbo"

            await chat_service.handle_chat(chat_request)

            # Verify AI message was saved
            save_calls = mock_chat_repository.save_message.call_args_list
            ai_call = save_calls[1]
            assert ai_call[1]['role'] == chat_schema.MessageRole.ASSISTANT

    @pytest.mark.asyncio
    async def test_handle_chat_without_model_id(self, chat_service, mock_chat_repository, mock_session_repository,
                                                 chat_request, sample_message, sample_ai_message, sample_session):
        """Test handle_chat uses session model when model_id not provided."""
        chat_request.model_id = None
        mock_chat_repository.save_message = AsyncMock(side_effect=[sample_message, sample_ai_message])
        mock_chat_repository.get_recent_messages = AsyncMock(return_value=[])
        sample_session.active_model_id = "gemini-1.5-pro"
        mock_session_repository.get_session_by_id = AsyncMock(return_value=sample_session)

        with patch('src.backend.app.services.chat.LLMFactory') as mock_factory, \
             patch('src.backend.app.services.chat.ModelRegistry') as mock_registry, \
             patch('src.backend.app.services.chat.settings') as mock_settings:
            mock_registry.exists.return_value = True
            mock_adapter = AsyncMock()
            mock_adapter.chat = AsyncMock(return_value="Response")
            mock_factory.get_instance.return_value = mock_adapter
            mock_settings.context_limit = 10
            mock_settings.default_llm = "gpt-3.5-turbo"

            await chat_service.handle_chat(chat_request)

            # Verify LLMFactory was called with session's model
            mock_factory.get_instance.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_chat_with_invalid_model_fallback(self, chat_service, mock_chat_repository, mock_session_repository, chat_request,
                                                             sample_message, sample_ai_message):
        """Test handle_chat falls back to default model when model is invalid."""
        mock_chat_repository.save_message = AsyncMock(side_effect=[sample_message, sample_ai_message])
        mock_chat_repository.get_recent_messages = AsyncMock(return_value=[])
        mock_session_repository.get_session_by_id = AsyncMock(return_value=None)

        with patch('src.backend.app.services.chat.LLMFactory') as mock_factory, \
             patch('src.backend.app.services.chat.ModelRegistry') as mock_registry, \
             patch('src.backend.app.services.chat.settings') as mock_settings:
            mock_registry.exists.return_value = False
            mock_adapter = AsyncMock()
            mock_adapter.chat = AsyncMock(return_value="Response")
            mock_factory.get_instance.return_value = mock_adapter
            mock_settings.context_limit = 10
            mock_settings.default_llm = "gpt-3.5-turbo"

            await chat_service.handle_chat(chat_request)

            # Should fall back to default model
            mock_factory.get_instance.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_chat_with_no_session_uses_default(self, chat_service, mock_chat_repository, mock_session_repository, chat_request,
                                                             sample_message, sample_ai_message):
        """Test handle_chat uses default model when session doesn't exist."""
        mock_chat_repository.save_message = AsyncMock(side_effect=[sample_message, sample_ai_message])
        mock_chat_repository.get_recent_messages = AsyncMock(return_value=[])
        mock_session_repository.get_session_by_id = AsyncMock(return_value=None)

        with patch('src.backend.app.services.chat.LLMFactory') as mock_factory, \
             patch('src.backend.app.services.chat.ModelRegistry') as mock_registry, \
             patch('src.backend.app.services.chat.settings') as mock_settings:
            mock_registry.exists.return_value = True
            mock_adapter = AsyncMock()
            mock_adapter.chat = AsyncMock(return_value="Response")
            mock_factory.get_instance.return_value = mock_adapter
            mock_settings.context_limit = 10
            mock_settings.default_llm = "gpt-3.5-turbo"

            await chat_service.handle_chat(chat_request)

            # Should use default model when session is None
            mock_factory.get_instance.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_chat_gets_recent_messages(self, chat_service, mock_chat_repository, mock_session_repository, chat_request,
                                                     sample_message, sample_ai_message):
        """Test handle_chat fetches recent messages for context."""
        mock_chat_repository.save_message = AsyncMock(side_effect=[sample_message, sample_ai_message])
        mock_chat_repository.get_recent_messages = AsyncMock(return_value=[sample_message])
        mock_session_repository.get_session_by_id = AsyncMock(return_value=None)

        with patch('src.backend.app.services.chat.LLMFactory') as mock_factory, \
             patch('src.backend.app.services.chat.ModelRegistry') as mock_registry, \
             patch('src.backend.app.services.chat.settings') as mock_settings:
            mock_registry.exists.return_value = True
            mock_adapter = AsyncMock()
            mock_adapter.chat = AsyncMock(return_value="Response")
            mock_factory.get_instance.return_value = mock_adapter
            mock_settings.context_limit = 10
            mock_settings.default_llm = "gpt-3.5-turbo"

            await chat_service.handle_chat(chat_request)

# Verify recent messages were fetched
            mock_chat_repository.get_recent_messages.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_chat_exception(self, chat_service, mock_chat_repository, mock_session_repository, chat_request):
        """Test handle_chat handles exceptions."""
        mock_chat_repository.save_message = AsyncMock(side_effect=Exception("Database error"))

        with pytest.raises(BusinessException) as exc_info:
            await chat_service.handle_chat(chat_request)

        assert "聊天处理异常" in str(exc_info.value)

    @pytest.mark.asyncio
    @patch('src.backend.app.services.chat.logger')
    async def test_handle_chat_logs_exception(self, mock_logger, chat_service, mock_chat_repository, chat_request):
        """Test handle_chat logs exceptions."""
        mock_chat_repository.save_message = AsyncMock(side_effect=Exception("Test error"))

        with pytest.raises(BusinessException):
            await chat_service.handle_chat(chat_request)

        # Verify logger was called
        assert mock_logger.exception.called

    @pytest.mark.asyncio
    async def test_get_history_success(self, chat_service, mock_chat_repository):
        """Test get_history returns messages."""
        messages = [
            Mock(id=3, session_id=1, role="assistant", content="Hi 3", created_at=datetime.now()),
            Mock(id=2, session_id=1, role="user", content="Hi 2", created_at=datetime.now()),
            Mock(id=1, session_id=1, role="assistant", content="Hi 1", created_at=datetime.now())
        ]
        mock_chat_repository.get_paged_messages = AsyncMock(return_value=(messages[:2], True))

        result = await chat_service.get_history(session_id=1, last_message_id=3, limit=20)

        # Verify result
        assert isinstance(result, chat_schema.HistoryResponse)
        assert len(result.items) == 2
        assert result.has_more is True
        assert result.last_message_id == 2

    @pytest.mark.asyncio
    async def test_get_history_sorts_messages(self, chat_service, mock_chat_repository):
        """Test get_history sorts messages by id."""
        messages = [
            Mock(id=3, session_id=1, role="assistant", content="Hi 3", created_at=datetime.now()),
            Mock(id=2, session_id=1, role="user", content="Hi 2", created_at=datetime.now()),
            Mock(id=1, session_id=1, role="assistant", content="Hi 1", created_at=datetime.now())
        ]
        mock_chat_repository.get_paged_messages = AsyncMock(return_value=(messages[:2], True))

        result = await chat_service.get_history(session_id=1, last_message_id=3, limit=20)

        # Verify messages are sorted
        assert result.items[0].id < result.items[1].id

    @pytest.mark.asyncio
    async def test_get_history_empty_result(self, chat_service, mock_chat_repository):
        """Test get_history with no messages."""
        mock_chat_repository.get_paged_messages = AsyncMock(return_value=([], False))

        result = await chat_service.get_history(session_id=1)

        assert len(result.items) == 0
        assert result.has_more is False
        assert result.last_message_id is None

    @pytest.mark.asyncio
    async def test_get_history_with_last_message_id(self, chat_service, mock_chat_repository):
        """Test get_history with last_message_id parameter."""
        messages = [Mock(id=2, session_id=1, role="user", content="Hi", created_at=datetime.now())]
        mock_chat_repository.get_paged_messages = AsyncMock(return_value=(messages, False))

        result = await chat_service.get_history(session_id=1, last_message_id=5, limit=10)

        mock_chat_repository.get_paged_messages.assert_called_once_with(
            session_id=1, last_id=5, limit=10
        )

    @pytest.mark.asyncio
    async def test_get_history_exception(self, chat_service, mock_chat_repository):
        """Test get_history handles exceptions."""
        mock_chat_repository.get_paged_messages = AsyncMock(side_effect=Exception("Database error"))

        with pytest.raises(BusinessException) as exc_info:
            await chat_service.get_history(session_id=1)

        assert "获取历史记录失败" in str(exc_info.value)

    @pytest.mark.asyncio
    @patch('src.backend.app.services.chat.logger')
    async def test_get_history_logs_exception(self, mock_logger, chat_service, mock_chat_repository):
        """Test get_history logs exceptions."""
        mock_chat_repository.get_paged_messages = AsyncMock(side_effect=Exception("Test error"))

        with pytest.raises(BusinessException):
            await chat_service.get_history(session_id=1)

        assert mock_logger.exception.called

    @pytest.mark.asyncio
    async def test_get_history_default_limit(self, chat_service, mock_chat_repository):
        """Test get_history uses default limit."""
        messages = [Mock(id=1, session_id=1, role="user", content="Hi", created_at=datetime.now())]
        mock_chat_repository.get_paged_messages = AsyncMock(return_value=(messages, False))

        result = await chat_service.get_history(session_id=1)

        # Should use default limit of 20
        call_args = mock_chat_repository.get_paged_messages.call_args
        assert call_args[1]['limit'] == 20

    @pytest.mark.asyncio
    async def test_get_history_with_custom_limit(self, chat_service, mock_chat_repository):
        """Test get_history with custom limit."""
        messages = [Mock(id=1, session_id=1, role="user", content="Hi", created_at=datetime.now())]
        mock_chat_repository.get_paged_messages = AsyncMock(return_value=(messages, False))

        await chat_service.get_history(session_id=1, limit=50)

        # Should use custom limit
        call_args = mock_chat_repository.get_paged_messages.call_args
        assert call_args[1]['limit'] == 50

    @pytest.mark.asyncio
    async def test_get_history_has_more_false(self, chat_service, mock_chat_repository):
        """Test get_history with has_more=False."""
        messages = [Mock(id=1, session_id=1, role="user", content="Hi", created_at=datetime.now())]
        mock_chat_repository.get_paged_messages = AsyncMock(return_value=(messages, False))

        result = await chat_service.get_history(session_id=1)

        assert result.has_more is False
        assert result.last_message_id is None
