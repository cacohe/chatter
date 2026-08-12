"""Tests for main entry."""

from unittest.mock import MagicMock, patch

from src.backend.main import _create_app, _register_routes, main


class TestMain:
    def test_create_app_title(self):
        with patch("src.backend.main.register_exception_handlers"):
            app = _create_app()
        assert app.title == "RAG Knowledge Q&A"
        assert app.version == "1.0.0"

    def test_register_routes_count(self):
        app = MagicMock()
        _register_routes(app)
        assert app.include_router.call_count == 2

    @patch("src.backend.main.uvicorn")
    def test_main_runs_uvicorn(self, mock_uvicorn):
        with patch("src.backend.main.settings") as mock_settings:
            mock_settings.backend_settings.backend_listen_addr = "0.0.0.0"
            mock_settings.backend_settings.backend_listen_port = 8000
            mock_settings.backend_settings.reload = False
            main()
        mock_uvicorn.run.assert_called_once()
        kwargs = mock_uvicorn.run.call_args.kwargs
        assert kwargs["app"] == "src.backend.main:app"
        assert kwargs["host"] == "0.0.0.0"
        assert kwargs["port"] == 8000
