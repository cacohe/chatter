"""Tests for StreamChat use case."""

from unittest.mock import patch

import pytest

from app.services.chat.stream import StreamChat
from domain.schemas import chat as chat_schema


class TestStreamChat:
    @pytest.fixture
    def usecase(self):
        return StreamChat()

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
    async def test_stream_chat(self, usecase, chat_request):
        async def _stream(messages):
            for part in ("你好", "，世界"):
                yield part

        with (
            patch("app.services.chat.stream.stream_chat", _stream),
            patch("app.services.chat.stream.retrieve", return_value=[]),
            patch("app.services.chat.stream.format_context", return_value=""),
        ):
            chunks = [c async for c in usecase.execute(chat_request)]

        assert "".join(chunks) == "你好，世界"

    @pytest.mark.asyncio
    async def test_stream_chat_with_rag_context(self, usecase, chat_request):
        captured_messages = []

        async def _stream(messages):
            captured_messages.extend(messages)
            yield "10 天"

        with (
            patch("app.services.chat.stream.stream_chat", _stream),
            patch(
                "app.services.chat.stream.retrieve",
                return_value=[object()],
            ),
            patch(
                "app.services.chat.stream.format_context",
                return_value="[1] 来源: leave.md\n年假 10 天",
            ),
        ):
            chunks = [c async for c in usecase.execute(chat_request)]

        assert chunks == ["10 天"]
        assert any(
            m["role"] == "system" and "参考文档" in m["content"]
            for m in captured_messages
        )
