"""Tests for ChatService."""

from unittest.mock import patch

import pytest

from app.services.chat import ChatService
from domain.schemas import chat as chat_schema


class TestChatService:
    @pytest.fixture
    def chat_service(self):
        return ChatService()

    @pytest.fixture
    def chat_request(self):
        return chat_schema.ChatRequest(
            content="年假有几天？",
            history=[
                chat_schema.ChatMessage(
                    role=chat_schema.MessageRole.USER, content="你好"
                ),
                chat_schema.ChatMessage(
                    role=chat_schema.MessageRole.ASSISTANT, content="你好"
                ),
            ],
        )

    @pytest.mark.asyncio
    async def test_handle_chat_stream(self, chat_service, chat_request):
        async def _stream(messages):
            for part in ("你好", "，世界"):
                yield part

        with (
            patch("app.services.chat.stream_chat", _stream),
            patch("app.services.chat.retrieve", return_value=[]),
            patch("app.services.chat.format_context", return_value=""),
        ):
            chunks = [c async for c in chat_service.handle_chat_stream(chat_request)]

        assert "".join(chunks) == "你好，世界"

    @pytest.mark.asyncio
    async def test_handle_chat_stream_with_rag_context(
        self, chat_service, chat_request
    ):
        captured_messages = []

        async def _stream(messages):
            captured_messages.extend(messages)
            yield "10 天"

        with (
            patch("app.services.chat.stream_chat", _stream),
            patch(
                "app.services.chat.retrieve",
                return_value=[object()],
            ),
            patch(
                "app.services.chat.format_context",
                return_value="[1] 来源: leave.md\n年假 10 天",
            ),
        ):
            chunks = [c async for c in chat_service.handle_chat_stream(chat_request)]

        assert chunks == ["10 天"]
        assert any(
            m["role"] == "system" and "参考文档" in m["content"]
            for m in captured_messages
        )
