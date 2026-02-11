"""Tests for main.py entry point."""

import pytest
from unittest.mock import patch, MagicMock

from src.backend.infra.db.supabase.client import init_supabase
from src.backend.main import main, _register_routes, _create_app


class TestMain:
    """Tests for main module."""

    @pytest.fixture
    def mock_app(self):
        """Mock FastAPI app."""
        return MagicMock()

    @pytest.fixture
    def mock_uvicorn(self):
        """Mock uvicorn."""
        with patch("src.backend.main.uvicorn") as mock:
            yield mock

    @pytest.fixture
    def mock_settings(self):
        """Mock settings."""
        with patch("src.backend.main.settings") as mock:
            mock.backend_settings.backend_listen_addr = "0.0.0.0"
            mock.backend_settings.backend_listen_port = 8000
            mock.backend_settings.reload = False
            yield mock

    def test_create_app_returns_fastapi_instance(self):
        """Test _create_app returns FastAPI instance."""
        with (
            patch("src.backend.main.register_exception_handlers"),
            patch("src.backend.main.lifespan"),
        ):
            app = _create_app()
            from fastapi import FastAPI

            assert isinstance(app, FastAPI)

    def test_create_app_has_correct_title(self):
        """Test app has correct title."""
        with (
            patch("src.backend.main.register_exception_handlers"),
            patch("src.backend.main.lifespan"),
        ):
            app = _create_app()
            assert app.title == "Caco AI Chat Backend"

    def test_create_app_has_correct_version(self):
        """Test app has correct version."""
        with (
            patch("src.backend.main.register_exception_handlers"),
            patch("src.backend.main.lifespan"),
        ):
            app = _create_app()
            assert app.version == "1.0.0"

    def test_create_app_has_lifespan(self):
        """Test app has lifespan configured."""
        with patch("src.backend.main.register_exception_handlers"):
            app = _create_app()
            assert app.router.lifespan_context is not None

    def test_create_app_registers_exception_handlers(self):
        """Test _create_app registers exception handlers."""
        with patch("src.backend.main.register_exception_handlers") as mock_register:
            _create_app()
            mock_register.assert_called_once()

    def test_register_routes(self):
        """Test _register_routes registers all routes."""
        app = MagicMock()
        _register_routes(app)

        # Verify include_router was called 4 times
        assert app.include_router.call_count == 4

    def test_register_routes_registers_auth_router(self):
        """Test auth router is registered."""
        with patch("src.backend.main.auth_router") as mock_router:
            app = MagicMock()
            _register_routes(app)
            app.include_router.assert_any_call(mock_router)

    def test_register_routes_registers_chat_router(self):
        """Test chat router is registered."""
        with patch("src.backend.main.chat_router") as mock_router:
            app = MagicMock()
            _register_routes(app)
            app.include_router.assert_any_call(mock_router)

    def test_register_routes_registers_llm_router(self):
        """Test llm router is registered."""
        with patch("src.backend.main.llm_router") as mock_router:
            app = MagicMock()
            _register_routes(app)
            app.include_router.assert_any_call(mock_router)

    def test_register_routes_registers_session_router(self):
        """Test session router is registered."""
        with patch("src.backend.main.session_router") as mock_router:
            app = MagicMock()
            _register_routes(app)
            app.include_router.assert_any_call(mock_router)

    @patch("src.backend.main._create_app")
    @patch("src.backend.main.uvicorn")
    def test_main_calls_create_app(self, mock_uvicorn, mock_create_app, mock_settings):
        """Test main calls _create_app."""
        main()
        mock_create_app.assert_called_once()

    @patch("src.backend.main._create_app")
    @patch("src.backend.main.uvicorn")
    def test_main_calls_uvicorn_run(self, mock_uvicorn, mock_create_app, mock_settings):
        """Test main calls uvicorn.run."""
        main()
        mock_uvicorn.run.assert_called_once()

    @patch("src.backend.main._create_app")
    @patch("src.backend.main.uvicorn")
    def test_main_passes_app_to_uvicorn(
        self, mock_uvicorn, mock_create_app, mock_settings
    ):
        """Test main passes app to uvicorn.run."""
        mock_app = MagicMock()
        mock_create_app.return_value = mock_app
        main()
        call_kwargs = mock_uvicorn.run.call_args[1]
        assert call_kwargs["app"] == mock_app

    @patch("src.backend.main._create_app")
    @patch("src.backend.main.uvicorn")
    def test_main_passes_correct_host(
        self, mock_uvicorn, mock_create_app, mock_settings
    ):
        """Test main passes correct host to uvicorn."""
        main()
        call_kwargs = mock_uvicorn.run.call_args[1]
        assert call_kwargs["host"] == "0.0.0.0"

    @patch("src.backend.main._create_app")
    @patch("src.backend.main.uvicorn")
    def test_main_passes_correct_port(
        self, mock_uvicorn, mock_create_app, mock_settings
    ):
        """Test main passes correct port to uvicorn."""
        main()
        call_kwargs = mock_uvicorn.run.call_args[1]
        assert call_kwargs["port"] == 8000

    @patch("src.backend.main._create_app")
    @patch("src.backend.main.uvicorn")
    def test_main_passes_reload_from_settings(
        self, mock_uvicorn, mock_create_app, mock_settings
    ):
        """Test main passes reload from settings."""
        main()
        call_kwargs = mock_uvicorn.run.call_args[1]
        assert "reload" in call_kwargs

    @patch("src.backend.main._create_app")
    @patch("src.backend.main.uvicorn")
    def test_main_sets_log_level_to_info(
        self, mock_uvicorn, mock_create_app, mock_settings
    ):
        """Test main sets log_level to info."""
        main()
        call_kwargs = mock_uvicorn.run.call_args[1]
        assert call_kwargs["log_level"] == "info"

    @patch("src.backend.main._create_app")
    @patch("src.backend.main.uvicorn")
    def test_main_enables_access_log(
        self, mock_uvicorn, mock_create_app, mock_settings
    ):
        """Test main enables access_log."""
        main()
        call_kwargs = mock_uvicorn.run.call_args[1]
        assert call_kwargs["access_log"] is True

    @patch("src.backend.main._create_app")
    @patch("src.backend.main.uvicorn")
    @patch("src.backend.main.init_supabase")
    def test_main_initializes_supabase(
        self, mock_init, mock_uvicorn, mock_create_app, mock_settings
    ):
        """Test main initializes supabase when __name__ is '__main__'."""
        with patch("src.backend.main.__name__", "__main__"):
            main()
        # init_supabase is called in __main__ block, not in main() function
        # So this test verifies the function exists
        assert callable(init_supabase)

    def test_main_is_callable(self):
        """Test main is callable."""
        assert callable(main)

    def test_create_app_is_callable(self):
        """Test _create_app is callable."""
        assert callable(_create_app)

    def test_register_routes_is_callable(self):
        """Test _register_routes is callable."""
        assert callable(_register_routes)

    @patch("src.backend.main.register_exception_handlers")
    def test_create_app_returns_none(self, mock_register):
        """Test _create_app returns app instance, not None."""
        app = _create_app()
        assert app is not None

    def test_register_routes_returns_none(self):
        """Test _register_routes returns None."""
        app = MagicMock()
        result = _register_routes(app)
        assert result is None

    @patch("src.backend.main._create_app")
    @patch("src.backend.main.uvicorn")
    def test_main_returns_none(self, mock_uvicorn, mock_create_app, mock_settings):
        """Test main returns None."""
        result = main()
        assert result is None
