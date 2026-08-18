"""Tests for chat routes."""

from unittest.mock import Mock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.deps import get_chat_history, get_start_new_chat, get_stream_chat
from api.routes.chat import chat_router


class TestChatRoutes:
    @pytest.fixture
    def mock_stream_chat(self):
        usecase = Mock()

        async def _stream(_session_id, _content):
            yield "hello"
            yield " world"

        usecase.execute = _stream
        return usecase

    @pytest.fixture
    def client(self, mock_stream_chat):
        app = FastAPI()
        app.include_router(chat_router)
        app.dependency_overrides[get_stream_chat] = lambda: mock_stream_chat
        app.dependency_overrides[get_start_new_chat] = lambda: Mock(
            execute=lambda _session_id: None
        )
        app.dependency_overrides[get_chat_history] = lambda: Mock(
            execute=lambda _session_id: [{"role": "user", "content": "已保存的问题"}]
        )
        return TestClient(app)

    def test_chat_stream_returns_sse(self, client):
        with client.stream(
            "POST",
            "/api/v1.0/chat/stream",
            json={"session_id": "s1", "content": "Hello"},
        ) as response:
            assert response.status_code == 200
            body = b"".join(response.iter_bytes()).decode("utf-8")
        assert "data: hello" in body
        assert "data:  world" in body

    def test_chat_stream_requires_content(self, client):
        response = client.post("/api/v1.0/chat/stream", json={"session_id": "s1"})
        assert response.status_code == 422

    def test_chat_stream_requires_session_id(self, client):
        response = client.post("/api/v1.0/chat/stream", json={"content": "Hello"})
        assert response.status_code == 422

    def test_start_new_chat(self, client):
        response = client.post("/api/v1.0/chat/new", json={"session_id": "s1"})
        assert response.status_code == 200
        assert response.json() == {"ok": True}

    def test_old_clear_session_endpoint_removed(self, client):
        response = client.delete("/api/v1.0/chat/session", params={"session_id": "s1"})
        assert response.status_code == 404

    def test_get_messages(self, client):
        response = client.get("/api/v1.0/chat/messages", params={"session_id": "s1"})
        assert response.status_code == 200
        assert response.json() == {
            "session_id": "s1",
            "messages": [{"role": "user", "content": "已保存的问题", "citations": []}],
        }

    def test_get_messages_requires_session_id(self, client):
        response = client.get("/api/v1.0/chat/messages")
        assert response.status_code == 422

    def test_non_stream_route_removed(self, client):
        response = client.post("/api/v1.0/chat", json={"content": "Hello"})
        assert response.status_code == 404
