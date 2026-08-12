"""Tests for domain exceptions."""

from src.backend.domain.exceptions import BusinessException


class TestBusinessException:
    def test_default_status_code(self):
        exc = BusinessException("Test error message")
        assert exc.message == "Test error message"
        assert exc.status_code == 400

    def test_custom_status_code(self):
        exc = BusinessException("Test error", status_code=404)
        assert exc.status_code == 404

    def test_is_exception(self):
        assert isinstance(BusinessException("x"), Exception)
