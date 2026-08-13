"""Tests for main entry."""

import os
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from main import _create_app, _register_routes, app, main


class TestMain:
    def test_create_app_title(self):
        with patch("main.register_exception_handlers"):
            created = _create_app()
        assert created.title == "RAG Knowledge Q&A"
        assert created.version == "1.0.0"

    def test_register_routes_count(self):
        mock_app = MagicMock()
        _register_routes(mock_app)
        assert mock_app.include_router.call_count == 2

    def test_health_endpoint(self):
        client = TestClient(app)
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"

    @patch("main.uvicorn")
    def test_main_runs_uvicorn(self, mock_uvicorn):
        with (
            patch("main.settings") as mock_settings,
            patch.dict(os.environ, {}, clear=False),
        ):
            os.environ.pop("PORT", None)
            mock_settings.backend_settings.backend_listen_addr = "0.0.0.0"
            mock_settings.backend_settings.backend_listen_port = 8000
            mock_settings.backend_settings.reload = False
            main()
        mock_uvicorn.run.assert_called_once()
        kwargs = mock_uvicorn.run.call_args.kwargs
        assert kwargs["app"] == "main:app"
        assert kwargs["host"] == "0.0.0.0"
        assert kwargs["port"] == 8000

    @patch("main.uvicorn")
    def test_main_prefers_port_env(self, mock_uvicorn):
        with (
            patch("main.settings") as mock_settings,
            patch.dict(os.environ, {"PORT": "9000"}),
        ):
            mock_settings.backend_settings.backend_listen_addr = "0.0.0.0"
            mock_settings.backend_settings.backend_listen_port = 8000
            mock_settings.backend_settings.reload = False
            main()
        assert mock_uvicorn.run.call_args.kwargs["port"] == 9000
