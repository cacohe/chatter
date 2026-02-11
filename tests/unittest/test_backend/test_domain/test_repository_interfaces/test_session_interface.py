"""Tests for ISessionRepository interface."""
import pytest
from abc import ABC
from unittest.mock import MagicMock
from src.backend.domain.repository_interfaces.session import ISessionRepository


class TestISessionRepository:
    """Tests for ISessionRepository interface."""

    def test_i_session_repository_is_abstract(self):
        """Test ISessionRepository is an abstract class."""
        assert issubclass(ISessionRepository, ABC)

    def test_i_session_repository_has_create_method(self):
        """Test ISessionRepository has create method."""
        assert hasattr(ISessionRepository, 'create')
        assert callable(ISessionRepository.create)

    def test_i_session_repository_has_update_title_method(self):
        """Test ISessionRepository has update_title method."""
        assert hasattr(ISessionRepository, 'update_title')
        assert callable(ISessionRepository.update_title)

    def test_i_session_repository_has_update_session_model_method(self):
        """Test ISessionRepository has update_session_model method."""
        assert hasattr(ISessionRepository, 'update_session_model')
        assert callable(ISessionRepository.update_session_model)

    def test_i_session_repository_has_get_sessions_by_user_method(self):
        """Test ISessionRepository has get_sessions_by_user method."""
        assert hasattr(ISessionRepository, 'get_sessions_by_user')
        assert callable(ISessionRepository.get_sessions_by_user)

    def test_i_session_repository_has_delete_by_user_method(self):
        """Test ISessionRepository has delete_by_user method."""
        assert hasattr(ISessionRepository, 'delete_by_user')
        assert callable(ISessionRepository.delete_by_user)

    def test_i_session_repository_has_get_session_by_id_method(self):
        """Test ISessionRepository has get_session_by_id method."""
        assert hasattr(ISessionRepository, 'get_session_by_id')
        assert callable(ISessionRepository.get_session_by_id)

    def test_create_is_abstract(self):
        """Test create is an abstract method."""
        assert 'create' in ISessionRepository.__abstractmethods__

    def test_update_title_is_abstract(self):
        """Test update_title is an abstract method."""
        assert 'update_title' in ISessionRepository.__abstractmethods__

    def test_update_session_model_is_abstract(self):
        """Test update_session_model is an abstract method."""
        assert 'update_session_model' in ISessionRepository.__abstractmethods__

    def test_get_sessions_by_user_is_abstract(self):
        """Test get_sessions_by_user is an abstract method."""
        assert 'get_sessions_by_user' in ISessionRepository.__abstractmethods__

    def test_delete_by_user_is_abstract(self):
        """Test delete_by_user is an abstract method."""
        assert 'delete_by_user' in ISessionRepository.__abstractmethods__

    def test_get_session_by_id_is_abstract(self):
        """Test get_session_by_id is an abstract method."""
        assert 'get_session_by_id' in ISessionRepository.__abstractmethods__

    def test_i_session_repository_cannot_be_instantiated(self):
        """Test ISessionRepository cannot be instantiated directly."""
        with pytest.raises(TypeError):
            ISessionRepository()

    def test_i_session_repository_has_6_abstract_methods(self):
        """Test ISessionRepository has 6 abstract methods."""
        assert len(ISessionRepository.__abstractmethods__) == 6

    @pytest.mark.asyncio
    async def test_concrete_implementation_create_works(self):
        """Test concrete implementation create method works."""
        class ConcreteSessionRepository(ISessionRepository):
            async def create(self, user_id, title):
                return MagicMock(id=1, user_id=user_id, title=title)

            async def update_title(self, session_id, new_title):
                return True

            async def update_session_model(self, session_id, model_id):
                return True

            async def get_sessions_by_user(self, user_id):
                return []

            async def delete_by_user(self, session_id, user_id):
                return True

            async def get_session_by_id(self, session_id):
                return MagicMock()

        repo = ConcreteSessionRepository()
        result = await repo.create("user-123", "Test Session")
        assert result.user_id == "user-123"

    @pytest.mark.asyncio
    async def test_concrete_implementation_update_title_works(self):
        """Test concrete implementation update_title method works."""
        class ConcreteSessionRepository(ISessionRepository):
            async def create(self, user_id, title):
                return MagicMock()

            async def update_title(self, session_id, new_title):
                return new_title == "New Title"

            async def update_session_model(self, session_id, model_id):
                return True

            async def get_sessions_by_user(self, user_id):
                return []

            async def delete_by_user(self, session_id, user_id):
                return True

            async def get_session_by_id(self, session_id):
                return MagicMock()

        repo = ConcreteSessionRepository()
        result = await repo.update_title(1, "New Title")
        assert result is True

    @pytest.mark.asyncio
    async def test_concrete_implementation_update_session_model_works(self):
        """Test concrete implementation update_session_model method works."""
        class ConcreteSessionRepository(ISessionRepository):
            async def create(self, user_id, title):
                return MagicMock()

            async def update_title(self, session_id, new_title):
                return True

            async def update_session_model(self, session_id, model_id):
                return model_id == "gpt-4o"

            async def get_sessions_by_user(self, user_id):
                return []

            async def delete_by_user(self, session_id, user_id):
                return True

            async def get_session_by_id(self, session_id):
                return MagicMock()

        repo = ConcreteSessionRepository()
        result = await repo.update_session_model(1, "gpt-4o")
        assert result is True

    @pytest.mark.asyncio
    async def test_concrete_implementation_get_sessions_by_user_works(self):
        """Test concrete implementation get_sessions_by_user method works."""
        class ConcreteSessionRepository(ISessionRepository):
            async def create(self, user_id, title):
                return MagicMock()

            async def update_title(self, session_id, new_title):
                return True

            async def update_session_model(self, session_id, model_id):
                return True

            async def get_sessions_by_user(self, user_id):
                return [MagicMock(id=i, user_id=user_id) for i in range(3)]

            async def delete_by_user(self, session_id, user_id):
                return True

            async def get_session_by_id(self, session_id):
                return MagicMock()

        repo = ConcreteSessionRepository()
        result = await repo.get_sessions_by_user("user-123")
        assert len(result) == 3

    @pytest.mark.asyncio
    async def test_concrete_implementation_delete_by_user_works(self):
        """Test concrete implementation delete_by_user method works."""
        class ConcreteSessionRepository(ISessionRepository):
            async def create(self, user_id, title):
                return MagicMock()

            async def update_title(self, session_id, new_title):
                return True

            async def update_session_model(self, session_id, model_id):
                return True

            async def get_sessions_by_user(self, user_id):
                return []

            async def delete_by_user(self, session_id, user_id):
                return session_id == 1 and user_id == "user-123"

            async def get_session_by_id(self, session_id):
                return MagicMock()

        repo = ConcreteSessionRepository()
        result = await repo.delete_by_user(1, "user-123")
        assert result is True

    @pytest.mark.asyncio
    async def test_concrete_implementation_get_session_by_id_works(self):
        """Test concrete implementation get_session_by_id method works."""
        class ConcreteSessionRepository(ISessionRepository):
            async def create(self, user_id, title):
                return MagicMock()

            async def update_title(self, session_id, new_title):
                return True

            async def update_session_model(self, session_id, model_id):
                return True

            async def get_sessions_by_user(self, user_id):
                return []

            async def delete_by_user(self, session_id, user_id):
                return True

            async def get_session_by_id(self, session_id):
                if session_id == 1:
                    return MagicMock(id=1, title="Test")
                return None

        repo = ConcreteSessionRepository()
        result = await repo.get_session_by_id(1)
        assert result.id == 1

    def test_concrete_implementation_can_be_created(self):
        """Test a concrete implementation can be created."""
        class ConcreteSessionRepository(ISessionRepository):
            async def create(self, user_id, title):
                return MagicMock()

            async def update_title(self, session_id, new_title):
                return True

            async def update_session_model(self, session_id, model_id):
                return True

            async def get_sessions_by_user(self, user_id):
                return []

            async def delete_by_user(self, session_id, user_id):
                return True

            async def get_session_by_id(self, session_id):
                return MagicMock()

        repo = ConcreteSessionRepository()
        assert repo is not None

    @pytest.mark.asyncio
    async def test_get_sessions_by_user_empty_result(self):
        """Test get_sessions_by_user returns empty list."""
        class ConcreteSessionRepository(ISessionRepository):
            async def create(self, user_id, title):
                return MagicMock()

            async def update_title(self, session_id, new_title):
                return True

            async def update_session_model(self, session_id, model_id):
                return True

            async def get_sessions_by_user(self, user_id):
                return []

            async def delete_by_user(self, session_id, user_id):
                return True

            async def get_session_by_id(self, session_id):
                return MagicMock()

        repo = ConcreteSessionRepository()
        result = await repo.get_sessions_by_user("nonexistent-user")
        assert len(result) == 0

    @pytest.mark.asyncio
    async def test_get_session_by_id_not_found(self):
        """Test get_session_by_id returns None for non-existent session."""
        class ConcreteSessionRepository(ISessionRepository):
            async def create(self, user_id, title):
                return MagicMock()

            async def update_title(self, session_id, new_title):
                return True

            async def update_session_model(self, session_id, model_id):
                return True

            async def get_sessions_by_user(self, user_id):
                return []

            async def delete_by_user(self, session_id, user_id):
                return True

            async def get_session_by_id(self, session_id):
                return None

        repo = ConcreteSessionRepository()
        result = await repo.get_session_by_id(999)
        assert result is None

    @pytest.mark.asyncio
    async def test_delete_by_user_wrong_user(self):
        """Test delete_by_user returns False when user doesn't own session."""
        class ConcreteSessionRepository(ISessionRepository):
            async def create(self, user_id, title):
                return MagicMock()

            async def update_title(self, session_id, new_title):
                return True

            async def update_session_model(self, session_id, model_id):
                return True

            async def get_sessions_by_user(self, user_id):
                return []

            async def delete_by_user(self, session_id, user_id):
                return False

            async def get_session_by_id(self, session_id):
                return MagicMock()

        repo = ConcreteSessionRepository()
        result = await repo.delete_by_user(1, "wrong-user")
        assert result is False

    @pytest.mark.asyncio
    async def test_update_title_nonexistent_session(self):
        """Test update_title returns False for non-existent session."""
        class ConcreteSessionRepository(ISessionRepository):
            async def create(self, user_id, title):
                return MagicMock()

            async def update_title(self, session_id, new_title):
                return False

            async def update_session_model(self, session_id, model_id):
                return True

            async def get_sessions_by_user(self, user_id):
                return []

            async def delete_by_user(self, session_id, user_id):
                return True

            async def get_session_by_id(self, session_id):
                return MagicMock()

        repo = ConcreteSessionRepository()
        result = await repo.update_title(999, "New Title")
        assert result is False
