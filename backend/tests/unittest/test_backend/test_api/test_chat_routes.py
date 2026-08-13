"""Tests for chat routes."""

from unittest.mock import Mock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.deps import get_stream_chat
from api.routes.chat import chat_router


class TestChatRoutes:
    @pytest.fixture
    def mock_stream_chat(self):
        usecase = Mock()

        async def _stream(_request):
            yield "hello"
            yield " world"

        usecase.execute = _stream
        return usecase

    @pytest.fixture
    def client(self, mock_stream_chat):
        app = FastAPI()
        app.include_router(chat_router)
        app.dependency_overrides[get_stream_chat] = lambda: mock_stream_chat
        return TestClient(app)

    def test_chat_stream_returns_sse(self, client):
        with client.stream(
            "POST",
            "/api/v1.0/chat/stream",
            json={"content": "Hello", "history": []},
        ) as response:
            assert response.status_code == 200
            body = b"".join(response.iter_bytes()).decode("utf-8")
        assert "data: hello" in body
        assert "data:  world" in body

    def test_chat_stream_requires_content(self, client):
        response = client.post("/api/v1.0/chat/stream", json={"history": []})
        assert response.status_code == 422

    def test_non_stream_route_removed(self, client):
        response = client.post(
            "/api/v1.0/chat", json={"content": "Hello", "history": []}
        )
        assert response.status_code == 404
