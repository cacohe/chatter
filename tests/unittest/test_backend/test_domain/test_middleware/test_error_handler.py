"""Tests for error handler test_middleware."""
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from src.backend.domain.middleware.error_handler import register_exception_handlers
from src.backend.domain.exceptions import AuthError, BusinessException


class TestRegisterExceptionHandlers:
    """Tests for register_exception_handlers function."""

    @pytest.fixture
    def app(self):
        """Create a FastAPI app for testing."""
        return FastAPI()

    def test_register_exception_handlers_modifies_app(self, app):
        """Test register_exception_handlers modifies the app."""
        register_exception_handlers(app)
        # App should be modified without error
        assert app is not None

    def test_register_exception_handlers_returns_none(self, app):
        """Test register_exception_handlers returns None."""
        result = register_exception_handlers(app)
        assert result is None

    @pytest.mark.asyncio
    async def test_global_exception_handler(self, app):
        """Test global exception handler."""
        register_exception_handlers(app)

        # Create a mock request and exception
        request = Request(
            scope={
                "type": "http",
                "method": "GET",
                "url": "http://test.com/test",
                "headers": [],
                "query_string": b"",
                "path": "/test"
            },
            receive=AsyncMock()
        )
        exc = Exception("Test error")

        # Get the exception handler for Exception
        handler = app.exception_handlers.get(Exception)
        assert handler is not None

        # Call the handler
        response = await handler(request, exc)

        # Verify response
        assert isinstance(response, JSONResponse)
        assert response.status_code == 500

    @pytest.mark.asyncio
    async def test_value_error_handler(self, app):
        """Test value error handler."""
        register_exception_handlers(app)

        # Create a mock request and exception
        request = Request(
            scope={
                "type": "http",
                "method": "GET",
                "url": "http://test.com/test",
                "headers": [],
                "query_string": b"",
                "path": "/test"
            },
            receive=AsyncMock()
        )
        exc = ValueError("Invalid value")

        # Get the exception handler for ValueError
        handler = app.exception_handlers.get(ValueError)
        assert handler is not None

        # Call the handler
        response = await handler(request, exc)

        # Verify response
        assert isinstance(response, JSONResponse)
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_business_exception_uses_global_handler(self, app):
        """Test BusinessException uses global handler."""
        register_exception_handlers(app)

        request = Request(
            scope={
                "type": "http",
                "method": "GET",
                "url": "http://test.com/test",
                "headers": [],
                "query_string": b"",
                "path": "/test"
            },
            receive=AsyncMock()
        )
        exc = BusinessException("Business error", status_code=422)

        # Get the exception handler
        handler = app.exception_handlers.get(Exception)
        response = await handler(request, exc)

        # Verify it's handled (as global exception)
        assert isinstance(response, JSONResponse)

    @pytest.mark.asyncio
    async def test_auth_exception_uses_global_handler(self, app):
        """Test AuthError uses global handler."""
        register_exception_handlers(app)

        request = Request(
            scope={
                "type": "http",
                "method": "GET",
                "url": "http://test.com/test",
                "headers": [],
                "query_string": b"",
                "path": "/test"
            },
            receive=AsyncMock()
        )
        exc = AuthError("Authentication failed")

        # Get the exception handler
        handler = app.exception_handlers.get(Exception)
        response = await handler(request, exc)

        # Verify it's handled
        assert isinstance(response, JSONResponse)

    @pytest.mark.asyncio
    @patch('src.backend.domain.middleware.error_handler.logger')
    async def test_global_exception_handler_logs_error(self, mock_logger, app):
        """Test global exception handler logs error."""
        register_exception_handlers(app)

        request = Request(
            scope={
                "type": "http",
                "method": "GET",
                "url": "http://test.com/test",
                "headers": [],
                "query_string": b"",
                "path": "/test"
            },
            receive=AsyncMock()
        )
        exc = Exception("Test error")

        handler = app.exception_handlers.get(Exception)
        await handler(request, exc)

        # Verify logger was called
        assert mock_logger.error.called

    @pytest.mark.asyncio
    @patch('src.backend.domain.middleware.error_handler.logger')
    async def test_value_error_handler_logs_warning(self, mock_logger, app):
        """Test value error handler logs warning."""
        register_exception_handlers(app)

        request = Request(
            scope={
                "type": "http",
                "method": "GET",
                "url": "http://test.com/test",
                "headers": [],
                "query_string": b"",
                "path": "/test"
            },
            receive=AsyncMock()
        )
        exc = ValueError("Invalid value")

        handler = app.exception_handlers.get(ValueError)
        await handler(request, exc)

        # Verify logger was called with warning
        assert mock_logger.warning.called

    @pytest.mark.asyncio
    async def test_global_exception_handler_includes_path(self, app):
        """Test global exception handler includes path in response."""
        register_exception_handlers(app)

        request = Request(
            scope={
                "type": "http",
                "method": "GET",
                "url": "http://test.com/api/test",
                "headers": [],
                "query_string": b"",
                "path": "/api/test"
            },
            receive=AsyncMock()
        )
        exc = Exception("Test error")

        handler = app.exception_handlers.get(Exception)
        response = await handler(request, exc)

        # Parse response body
        import json
        body = json.loads(response.body.decode())

        # Verify path is included
        assert "path" in body
        assert body["path"] == "/api/test"

    @pytest.mark.asyncio
    async def test_value_error_handler_includes_path(self, app):
        """Test value error handler includes path in response."""
        register_exception_handlers(app)

        request = Request(
            scope={
                "type": "http",
                "method": "GET",
                "url": "http://test.com/api/test",
                "headers": [],
                "query_string": b"",
                "path": "/api/test"
            },
            receive=AsyncMock()
        )
        exc = ValueError("Invalid value")

        handler = app.exception_handlers.get(ValueError)
        response = await handler(request, exc)

        # Parse response body
        import json
        body = json.loads(response.body.decode())

        # Verify path is included
        assert "path" in body
        assert body["path"] == "/api/test"

    @pytest.mark.asyncio
    async def test_global_exception_handler_response_body(self, app):
        """Test global exception handler response body structure."""
        register_exception_handlers(app)

        request = Request(
            scope={
                "type": "http",
                "method": "GET",
                "url": "http://test.com/test",
                "headers": [],
                "query_string": b"",
                "path": "/test"
            },
            receive=AsyncMock()
        )
        exc = Exception("Test error")

        handler = app.exception_handlers.get(Exception)
        response = await handler(request, exc)

        import json
        body = json.loads(response.body.decode())

        # Verify body structure
        assert "detail" in body
        assert "path" in body

    @pytest.mark.asyncio
    async def test_value_error_handler_response_body(self, app):
        """Test value error handler response body structure."""
        register_exception_handlers(app)

        request = Request(
            scope={
                "type": "http",
                "method": "GET",
                "url": "http://test.com/test",
                "headers": [],
                "query_string": b"",
                "path": "/test"
            },
            receive=AsyncMock()
        )
        exc = ValueError("Invalid value")

        handler = app.exception_handlers.get(ValueError)
        response = await handler(request, exc)

        import json
        body = json.loads(response.body.decode())

        # Verify body structure
        assert "detail" in body
        assert body["detail"] == "Invalid value"
        assert "path" in body

    @pytest.mark.asyncio
    async def test_value_error_handler_with_empty_message(self, app):
        """Test value error handler with empty error message."""
        register_exception_handlers(app)

        request = Request(
            scope={
                "type": "http",
                "method": "GET",
                "url": "http://test.com/test",
                "headers": [],
                "query_string": b"",
                "path": "/test"
            },
            receive=AsyncMock()
        )
        exc = ValueError("")

        handler = app.exception_handlers.get(ValueError)
        response = await handler(request, exc)

        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_global_exception_handler_with_unicode_error(self, app):
        """Test global exception handler with unicode error."""
        register_exception_handlers(app)

        request = Request(
            scope={
                "type": "http",
                "method": "GET",
                "url": "http://test.com/test",
                "headers": [],
                "query_string": b"",
                "path": "/test"
            },
            receive=AsyncMock()
        )
        exc = Exception("错误测试")

        handler = app.exception_handlers.get(Exception)
        response = await handler(request, exc)

        assert response.status_code == 500

    def test_register_handlers_on_multiple_apps(self):
        """Test registering handlers on multiple apps."""
        app1 = FastAPI()
        app2 = FastAPI()

        register_exception_handlers(app1)
        register_exception_handlers(app2)

        # Both apps should have handlers
        assert Exception in app1.exception_handlers
        assert Exception in app2.exception_handlers
        assert ValueError in app1.exception_handlers
        assert ValueError in app2.exception_handlers
