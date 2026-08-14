"""Tests for frontend settings."""

from unittest.mock import patch

from config import _init_settings


class TestInitSettings:
    def test_defaults_when_env_missing(self, monkeypatch):
        monkeypatch.delenv("BACKEND_API_URL", raising=False)
        with patch("config.load_env"):
            settings = _init_settings()

        assert settings.backend_api_url == "http://localhost:8000/api/v1.0"

    def test_reads_env_and_strips_trailing_slash(self, monkeypatch):
        monkeypatch.setenv("BACKEND_API_URL", "https://api.example.com/api/v1.0/")
        with patch("config.load_env"):
            settings = _init_settings()

        assert settings.backend_api_url == "https://api.example.com/api/v1.0"
