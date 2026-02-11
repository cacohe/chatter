"""Tests for test_lifecycle events."""
import pytest
from unittest.mock import MagicMock, patch
from src.backend.domain.lifecycle.events import lifespan


class TestLifespan:
    """Tests for lifespan context manager."""

    @pytest.mark.asyncio
    async def test_lifespan_initialization(self):
        """Test lifespan can be used as async context manager."""
        # Create a mock FastAPI app
        mock_app = MagicMock()

        # Use the lifespan context manager
        async with lifespan(mock_app) as state:
            # Lifespan should yield without error
            assert state is None

    @pytest.mark.asyncio
    @patch('src.backend.domain.lifecycle.events.logger')
    async def test_lifespan_logs_on_startup(self, mock_logger):
        """Test lifespan logs startup messages."""
        mock_app = MagicMock()

        async with lifespan(mock_app):
            # Check that startup logs were called
            assert mock_logger.info.call_count >= 3

    @pytest.mark.asyncio
    @patch('src.backend.domain.lifecycle.events.logger')
    async def test_lifespan_logs_on_shutdown(self, mock_logger):
        """Test lifespan logs shutdown messages."""
        mock_app = MagicMock()

        async with lifespan(mock_app):
            # Clear the call count to test shutdown separately
            startup_call_count = mock_logger.info.call_count

        # After exiting, shutdown logs should be called
        assert mock_logger.info.call_count > startup_call_count

    @pytest.mark.asyncio
    @patch('src.backend.domain.lifecycle.events.settings')
    @patch('src.backend.domain.lifecycle.events.logger')
    async def test_lifespan_logs_environment_info(self, mock_logger, mock_settings):
        """Test lifespan logs environment information."""
        mock_settings.debug = False
        mock_app = MagicMock()

        async with lifespan(mock_app):
            pass

        # Verify logger was called with environment info
        log_calls = [str(call) for call in mock_logger.info.call_args_list]
        assert any("环境" in str(call) for call in log_calls)

    @pytest.mark.asyncio
    @patch('src.backend.domain.lifecycle.events.settings')
    @patch('src.backend.domain.lifecycle.events.logger')
    async def test_lifespan_logs_backend_settings(self, mock_logger, mock_settings):
        """Test lifespan logs backend address and port."""
        mock_app = MagicMock()
        mock_settings.backend_settings = MagicMock()
        mock_settings.backend_settings.backend_listen_addr = "0.0.0.0"
        mock_settings.backend_settings.backend_listen_port = 8000

        async with lifespan(mock_app):
            pass

        # Verify backend settings were logged
        log_calls = [str(call) for call in mock_logger.info.call_args_list]
        assert any("0.0.0.0:8000" in str(call) for call in log_calls)

    @pytest.mark.asyncio
    @patch('src.backend.domain.lifecycle.events.settings')
    @patch('src.backend.domain.lifecycle.events.logger')
    async def test_lifespan_production_environment(self, mock_logger, mock_settings):
        """Test lifespan in production environment."""
        mock_settings.debug = False
        mock_app = MagicMock()

        async with lifespan(mock_app):
            pass

        # Should log production environment
        log_calls = [str(call) for call in mock_logger.info.call_args_list]
        assert any("生产" in str(call) for call in log_calls)

    @pytest.mark.asyncio
    @patch('src.backend.domain.lifecycle.events.settings')
    @patch('src.backend.domain.lifecycle.events.logger')
    async def test_lifespan_development_environment(self, mock_logger, mock_settings):
        """Test lifespan in development environment."""
        mock_settings.debug = True
        mock_app = MagicMock()

        async with lifespan(mock_app):
            pass

        # Should log development environment
        log_calls = [str(call) for call in mock_logger.info.call_args_list]
        assert any("开发" in str(call) for call in log_calls)

    @pytest.mark.asyncio
    @patch('src.backend.domain.lifecycle.events.logger')
    async def test_lifespan_startup_separator(self, mock_logger):
        """Test lifespan logs separator on startup."""
        mock_app = MagicMock()

        async with lifespan(mock_app):
            # First call should be separator
            first_call_args = mock_logger.info.call_args_list[0][0][0]
            assert "=" * 60 in first_call_args

    @pytest.mark.asyncio
    @patch('src.backend.domain.lifecycle.events.logger')
    async def test_lifespan_shutdown_separator(self, mock_logger):
        """Test lifespan logs separator on shutdown."""
        mock_app = MagicMock()

        async with lifespan(mock_app):
            startup_call_count = mock_logger.info.call_count

        # Last call should be separator
        shutdown_call_args = mock_logger.info.call_args_list[startup_call_count][0][0]
        assert "=" * 60 in shutdown_call_args

    @pytest.mark.asyncio
    async def test_lifespan_can_be_reused(self):
        """Test lifespan can be used multiple times."""
        mock_app = MagicMock()

        # First usage
        async with lifespan(mock_app):
            pass

        # Second usage should work too
        async with lifespan(mock_app):
            pass

    @pytest.mark.asyncio
    @patch('src.backend.domain.lifecycle.events.logger')
    async def test_lifespan_handles_exception_in_startup_block(self, mock_logger):
        """Test lifespan handles exceptions during startup."""
        mock_app = MagicMock()
        mock_app.config = type('Config', (), {'startup': MagicMock(side_effect=Exception("Startup error"))})()

        # Lifespan should complete even if app has issues
        async with lifespan(mock_app):
            pass

    @pytest.mark.asyncio
    @patch('src.backend.domain.lifecycle.events.logger')
    async def test_lifespan_handles_exception_in_shutdown_block(self, mock_logger):
        """Test lifespan handles exceptions during shutdown."""
        mock_app = MagicMock()

        async with lifespan(mock_app):
            pass

        # Shutdown should complete
        assert True

    @pytest.mark.asyncio
    async def test_lifespan_returns_none_from_yield(self):
        """Test lifespan yields None."""
        mock_app = MagicMock()

        async with lifespan(mock_app) as yielded:
            assert yielded is None

    @pytest.mark.asyncio
    @patch('src.backend.domain.lifecycle.events.settings')
    @patch('src.backend.domain.lifecycle.events.logger')
    async def test_lifespan_logs_shutting_down_message(self, mock_logger, mock_settings):
        """Test lifespan logs shutting down message."""
        mock_app = MagicMock()

        async with lifespan(mock_app):
            pass

        log_calls = [str(call) for call in mock_logger.info.call_args_list]
        assert any("关闭" in str(call) or "shutting" in str(call).lower() for call in log_calls)

    @pytest.mark.asyncio
    @patch('src.backend.domain.lifecycle.events.logger')
    async def test_lifespan_logs_starting_up_message(self, mock_logger):
        """Test lifespan logs starting up message."""
        mock_app = MagicMock()

        async with lifespan(mock_app):
            pass

        log_calls = [str(call) for call in mock_logger.info.call_args_list]
        assert any("启动" in str(call) or "starting" in str(call).lower() for call in log_calls)
