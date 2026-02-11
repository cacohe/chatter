"""Tests for IAuthRepository interface."""
import pytest
from abc import ABC, abstractmethod
from unittest.mock import MagicMock
from src.backend.domain.repository_interfaces.auth import IAuthRepository


class TestIAuthRepository:
    """Tests for IAuthRepository interface."""

    def test_i_auth_repository_is_abstract(self):
        """Test IAuthRepository is an abstract class."""
        assert issubclass(IAuthRepository, ABC)

    def test_i_auth_repository_has_create_user_method(self):
        """Test IAuthRepository has create_user method."""
        assert hasattr(IAuthRepository, 'create_user')
        assert callable(IAuthRepository.create_user)

    def test_i_auth_repository_has_authenticate_method(self):
        """Test IAuthRepository has authenticate method."""
        assert hasattr(IAuthRepository, 'authenticate')
        assert callable(IAuthRepository.authenticate)

    def test_i_auth_repository_has_get_user_by_token_method(self):
        """Test IAuthRepository has get_user_by_token method."""
        assert hasattr(IAuthRepository, 'get_user_by_token')
        assert callable(IAuthRepository.get_user_by_token)

    def test_i_auth_repository_has_sign_out_method(self):
        """Test IAuthRepository has sign_out method."""
        assert hasattr(IAuthRepository, 'sign_out')
        assert callable(IAuthRepository.sign_out)

    def test_create_user_is_abstract(self):
        """Test create_user is an abstract method."""
        assert 'create_user' in IAuthRepository.__abstractmethods__

    def test_authenticate_is_abstract(self):
        """Test authenticate is an abstract method."""
        assert 'authenticate' in IAuthRepository.__abstractmethods__

    def test_get_user_by_token_is_abstract(self):
        """Test get_user_by_token is an abstract method."""
        assert 'get_user_by_token' in IAuthRepository.__abstractmethods__

    def test_sign_out_is_abstract(self):
        """Test sign_out is an abstract method."""
        assert 'sign_out' in IAuthRepository.__abstractmethods__

    def test_i_auth_repository_cannot_be_instantiated(self):
        """Test IAuthRepository cannot be instantiated directly."""
        with pytest.raises(TypeError):
            IAuthRepository()

    def test_i_auth_repository_has_4_abstract_methods(self):
        """Test IAuthRepository has 4 abstract methods."""
        assert len(IAuthRepository.__abstractmethods__) == 4

    def test_concrete_implementation_can_be_created(self):
        """Test a concrete implementation can be created."""
        class ConcreteAuthRepository(IAuthRepository):
            def create_user(self, email, password, username):
                return {"id": "123", "email": email}

            def authenticate(self, email, password):
                return MagicMock(access_token="token", refresh_token="refresh")

            def get_user_by_token(self, token):
                return {"id": "123", "email": "test@example.com"}

            def sign_out(self):
                pass

        repo = ConcreteAuthRepository()
        assert repo is not None

    def test_concrete_implementation_create_user_works(self):
        """Test concrete implementation create_user method works."""
        class ConcreteAuthRepository(IAuthRepository):
            def create_user(self, email, password, username):
                return {"id": "123", "email": email, "username": username}

            def authenticate(self, email, password):
                return MagicMock()

            def get_user_by_token(self, token):
                return None

            def sign_out(self):
                pass

        repo = ConcreteAuthRepository()
        result = repo.create_user("test@example.com", "password", "user")
        assert result["email"] == "test@example.com"

    def test_concrete_implementation_authenticate_works(self):
        """Test concrete implementation authenticate method works."""
        class ConcreteAuthRepository(IAuthRepository):
            def create_user(self, email, password, username):
                return {}

            def authenticate(self, email, password):
                session = MagicMock()
                session.access_token = "token"
                session.refresh_token = "refresh"
                return session

            def get_user_by_token(self, token):
                return None

            def sign_out(self):
                pass

        repo = ConcreteAuthRepository()
        result = repo.authenticate("test@example.com", "password")
        assert result.access_token == "token"

    def test_concrete_implementation_get_user_by_token_works(self):
        """Test concrete implementation get_user_by_token method works."""
        class ConcreteAuthRepository(IAuthRepository):
            def create_user(self, email, password, username):
                return {}

            def authenticate(self, email, password):
                return MagicMock()

            def get_user_by_token(self, token):
                return {"id": "123", "email": "test@example.com"}

            def sign_out(self):
                pass

        repo = ConcreteAuthRepository()
        result = repo.get_user_by_token("token")
        assert result["email"] == "test@example.com"

    def test_concrete_implementation_sign_out_works(self):
        """Test concrete implementation sign_out method works."""
        class ConcreteAuthRepository(IAuthRepository):
            def create_user(self, email, password, username):
                return {}

            def authenticate(self, email, password):
                return MagicMock()

            def get_user_by_token(self, token):
                return None

            def sign_out(self):
                pass

        repo = ConcreteAuthRepository()
        repo.sign_out()  # Should not raise error
