"""Tests for IChatRepository interface."""
import pytest
from abc import ABC
from unittest.mock import MagicMock
from src.backend.domain.repository_interfaces.chat import IChatRepository


class TestIChatRepository:
    """Tests for IChatRepository interface."""

    def test_i_chat_repository_is_abstract(self):
        """Test IChatRepository is an abstract class."""
        assert issubclass(IChatRepository, ABC)

    def test_i_chat_repository_has_save_message_method(self):
        """Test IChatRepository has save_message method."""
        assert hasattr(IChatRepository, 'save_message')
        assert callable(IChatRepository.save_message)

    def test_i_chat_repository_has_get_recent_messages_method(self):
        """Test IChatRepository has get_recent_messages method."""
        assert hasattr(IChatRepository, 'get_recent_messages')
        assert callable(IChatRepository.get_recent_messages)

    def test_i_chat_repository_has_get_paged_messages_method(self):
        """Test IChatRepository has get_paged_messages method."""
        assert hasattr(IChatRepository, 'get_paged_messages')
        assert callable(IChatRepository.get_paged_messages)

    def test_save_message_is_abstract(self):
        """Test save_message is an abstract method."""
        assert 'save_message' in IChatRepository.__abstractmethods__

    def test_get_recent_messages_is_abstract(self):
        """Test get_recent_messages is an abstract method."""
        assert 'get_recent_messages' in IChatRepository.__abstractmethods__

    def test_get_paged_messages_is_abstract(self):
        """Test get_paged_messages is an abstract method."""
        assert 'get_paged_messages' in IChatRepository.__abstractmethods__

    def test_i_chat_repository_cannot_be_instantiated(self):
        """Test IChatRepository cannot be instantiated directly."""
        with pytest.raises(TypeError):
            IChatRepository()

    def test_i_chat_repository_has_3_abstract_methods(self):
        """Test IChatRepository has 3 abstract methods."""
        assert len(IChatRepository.__abstractmethods__) == 3

    @pytest.mark.asyncio
    async def test_concrete_implementation_save_message_works(self):
        """Test concrete implementation save_message method works."""
        class ConcreteChatRepository(IChatRepository):
            async def save_message(self, session_id, role, content):
                return MagicMock(id=1, session_id=session_id, role=role, content=content)

            async def get_recent_messages(self, session_id, limit=10):
                return []

            async def get_paged_messages(self, session_id, last_id, limit):
                return ([], False)

        repo = ConcreteChatRepository()
        result = await repo.save_message(1, "user", "Hello")
        assert result.session_id == 1

    @pytest.mark.asyncio
    async def test_concrete_implementation_get_recent_messages_works(self):
        """Test concrete implementation get_recent_messages method works."""
        class ConcreteChatRepository(IChatRepository):
            async def save_message(self, session_id, role, content):
                return MagicMock()

            async def get_recent_messages(self, session_id, limit=10):
                return [MagicMock(id=1, role="user", content="Test")]

            async def get_paged_messages(self, session_id, last_id, limit):
                return ([], False)

        repo = ConcreteChatRepository()
        result = await repo.get_recent_messages(1, limit=5)
        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_concrete_implementation_get_paged_messages_works(self):
        """Test concrete implementation get_paged_messages method works."""
        class ConcreteChatRepository(IChatRepository):
            async def save_message(self, session_id, role, content):
                return MagicMock()

            async def get_recent_messages(self, session_id, limit=10):
                return []

            async def get_paged_messages(self, session_id, last_id, limit):
                messages = [MagicMock(id=i) for i in range(1, 11)]
                return (messages[:limit], True)

        repo = ConcreteChatRepository()
        result, has_more = await repo.get_paged_messages(1, None, 10)
        assert len(result) == 10
        assert has_more is True

    def test_concrete_implementation_can_be_created(self):
        """Test a concrete implementation can be created."""
        class ConcreteChatRepository(IChatRepository):
            async def save_message(self, session_id, role, content):
                return MagicMock()

            async def get_recent_messages(self, session_id, limit=10):
                return []

            async def get_paged_messages(self, session_id, last_id, limit):
                return ([], False)

        repo = ConcreteChatRepository()
        assert repo is not None

    @pytest.mark.asyncio
    async def test_save_message_with_different_roles(self):
        """Test save_message with different roles."""
        class ConcreteChatRepository(IChatRepository):
            async def save_message(self, session_id, role, content):
                return MagicMock(role=role)

            async def get_recent_messages(self, session_id, limit=10):
                return []

            async def get_paged_messages(self, session_id, last_id, limit):
                return ([], False)

        repo = ConcreteChatRepository()
        roles = ["user", "assistant", "system"]
        for role in roles:
            result = await repo.save_message(1, role, "Test")
            assert result.role == role

    @pytest.mark.asyncio
    async def test_get_recent_messages_with_custom_limit(self):
        """Test get_recent_messages with custom limit."""
        class ConcreteChatRepository(IChatRepository):
            async def save_message(self, session_id, role, content):
                return MagicMock()

            async def get_recent_messages(self, session_id, limit=10):
                return [MagicMock() for _ in range(limit)]

            async def get_paged_messages(self, session_id, last_id, limit):
                return ([], False)

        repo = ConcreteChatRepository()
        result = await repo.get_recent_messages(1, limit=50)
        assert len(result) == 50

    @pytest.mark.asyncio
    async def test_get_paged_messages_with_last_id(self):
        """Test get_paged_messages with last_id parameter."""
        class ConcreteChatRepository(IChatRepository):
            async def save_message(self, session_id, role, content):
                return MagicMock()

            async def get_recent_messages(self, session_id, limit=10):
                return []

            async def get_paged_messages(self, session_id, last_id, limit):
                return ([MagicMock(id=last_id)], False)

        repo = ConcreteChatRepository()
        result, _ = await repo.get_paged_messages(1, 100, 10)
        assert result[0].id == 100

    @pytest.mark.asyncio
    async def test_get_paged_messages_without_last_id(self):
        """Test get_paged_messages without last_id parameter."""
        class ConcreteChatRepository(IChatRepository):
            async def save_message(self, session_id, role, content):
                return MagicMock()

            async def get_recent_messages(self, session_id, limit=10):
                return []

            async def get_paged_messages(self, session_id, last_id, limit):
                # When last_id is None, it's the first page, so has_more should indicate more data
                # For this test, we'll return False to indicate no more pages
                return ([], False)

        repo = ConcreteChatRepository()
        _, has_more = await repo.get_paged_messages(1, None, 10)
        assert has_more is False

    @pytest.mark.asyncio
    async def test_get_paged_messages_empty_result(self):
        """Test get_paged_messages returns empty result."""
        class ConcreteChatRepository(IChatRepository):
            async def save_message(self, session_id, role, content):
                return MagicMock()

            async def get_recent_messages(self, session_id, limit=10):
                return []

            async def get_paged_messages(self, session_id, last_id, limit):
                return ([], False)

        repo = ConcreteChatRepository()
        result, has_more = await repo.get_paged_messages(1, None, 10)
        assert len(result) == 0
        assert has_more is False
