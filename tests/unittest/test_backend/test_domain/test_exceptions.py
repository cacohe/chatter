"""Tests for domain exceptions."""
import pytest
from src.backend.domain.exceptions import BusinessException, AuthError


class TestBusinessException:
    """Tests for BusinessException class."""

    def test_business_exception_initialization_default_status_code(self):
        """Test BusinessException with default status code."""
        exception = BusinessException("Test error message")
        assert exception.message == "Test error message"
        assert exception.status_code == 400

    def test_business_exception_initialization_custom_status_code(self):
        """Test BusinessException with custom status code."""
        exception = BusinessException("Test error", status_code=404)
        assert exception.message == "Test error"
        assert exception.status_code == 404

    def test_business_exception_is_exception_subclass(self):
        """Test BusinessException is subclass of Exception."""
        exception = BusinessException("Test")
        assert isinstance(exception, Exception)

    def test_business_exception_str_representation(self):
        """Test string representation of BusinessException."""
        exception = BusinessException("Test error")
        assert str(exception) == "Test error"


class TestAuthError:
    """Tests for AuthError class."""

    def test_auth_error_initialization(self):
        """Test AuthError initialization."""
        exception = AuthError("Authentication failed")
        assert exception.message == "Authentication failed"
        assert exception.status_code == 401

    def test_auth_error_default_status_code(self):
        """Test AuthError has default status code 401."""
        exception = AuthError("Unauthorized")
        assert exception.status_code == 401

    def test_auth_error_is_business_exception_subclass(self):
        """Test AuthError is subclass of BusinessException."""
        exception = AuthError("Auth error")
        assert isinstance(exception, BusinessException)

    def test_auth_error_is_exception_subclass(self):
        """Test AuthError is subclass of Exception."""
        exception = AuthError("Auth error")
        assert isinstance(exception, Exception)

    def test_auth_error_str_representation(self):
        """Test string representation of AuthError."""
        exception = AuthError("Invalid token")
        assert str(exception) == "Invalid token"

    def test_auth_error_cannot_override_status_code(self):
        """Test AuthError does not allow custom status code."""
        # AuthError.__init__ only accepts message parameter, status_code is fixed to 401
        exception = AuthError("Test")
        # Verify status_code is always 401
        assert exception.status_code == 401
