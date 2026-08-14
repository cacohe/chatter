"""Tests for StreamChat use case and backend chat memory."""

from unittest.mock import MagicMock, patch

import pytest
from llama_index.core.schema import TextNode

from app.services.chat.get_history import GetChatHistory
from app.services.chat.start_new_chat import StartNewChat
from app.services.chat.stream import StreamChat, format_context
from domain.models.chat import ChatMessage, MessageRole
from infra.chat import history, memory


def _fake_retriever(chunks=None):
    retriever = MagicMock()
    retriever.retrieve.return_value = chunks or []
    return retriever


class TestStreamChat:
    @pytest.fixture
    def usecase(self):
        return StreamChat()

    @pytest.mark.asyncio
    async def test_stream_chat(self, usecase):
        async def _stream(messages):
            for part in ("你好", "，世界"):
                yield part

        with (
            patch("app.services.chat.stream.stream_chat", _stream),
            patch(
                "app.services.chat.stream.get_retriever", return_value=_fake_retriever()
            ),
        ):
            chunks = [c async for c in usecase.execute("sess-1", "年假有几天？")]

        assert "".join(chunks) == "你好，世界"
        stored = memory.get_messages("sess-1")
        assert [m.role.value for m in stored] == ["user", "assistant"]
        assert stored[0].content == "年假有几天？"
        assert stored[1].content == "你好，世界"
        displayed = history.get_history("sess-1")
        assert [m.content for m in displayed] == ["年假有几天？", "你好，世界"]

    @pytest.mark.asyncio
    async def test_stream_uses_backend_history_not_request_body(self, usecase):
        memory.append_messages(
            "sess-2",
            [
                ChatMessage(role=MessageRole.USER, content="你好"),
                ChatMessage(role=MessageRole.ASSISTANT, content="你好"),
            ],
        )
        captured_messages = []

        async def _stream(messages):
            captured_messages.extend(messages)
            yield "10 天"

        with (
            patch("app.services.chat.stream.stream_chat", _stream),
            patch(
                "app.services.chat.stream.get_retriever", return_value=_fake_retriever()
            ),
        ):
            chunks = [c async for c in usecase.execute("sess-2", "年假几天")]

        assert chunks == ["10 天"]
        assert {"role": "user", "content": "你好"} in captured_messages
        assert {"role": "assistant", "content": "你好"} in captured_messages

    @pytest.mark.asyncio
    async def test_stream_does_not_use_display_history_as_llm_context(self, usecase):
        history.append_history(
            "sess-6",
            [
                ChatMessage(role=MessageRole.USER, content="只在展示历史"),
                ChatMessage(role=MessageRole.ASSISTANT, content="展示回复"),
            ],
        )
        captured_messages = []

        async def _stream(messages):
            captured_messages.extend(messages)
            yield "ok"

        with (
            patch("app.services.chat.stream.stream_chat", _stream),
            patch(
                "app.services.chat.stream.get_retriever", return_value=_fake_retriever()
            ),
        ):
            [c async for c in usecase.execute("sess-6", "新问题")]

        assert not any(m.get("content") == "只在展示历史" for m in captured_messages)

    @pytest.mark.asyncio
    async def test_stream_chat_with_rag_context(self, usecase):
        captured_messages = []

        async def _stream(messages):
            captured_messages.extend(messages)
            yield "10 天"

        with (
            patch("app.services.chat.stream.stream_chat", _stream),
            patch(
                "app.services.chat.stream.get_retriever",
                return_value=_fake_retriever(
                    [
                        TextNode(
                            text="年假 10 天",
                            metadata={"doc_name": "leave.md", "chunk_index": 0},
                        )
                    ]
                ),
            ),
        ):
            chunks = [c async for c in usecase.execute("sess-1", "年假有几天？")]

        assert chunks == ["10 天"]
        assert any(
            m["role"] == "system" and "参考文档" in m["content"]
            for m in captured_messages
        )

    @pytest.mark.asyncio
    async def test_failed_stream_does_not_append_memory(self, usecase):
        async def _stream(_messages):
            raise RuntimeError("boom")
            yield ""  # pragma: no cover

        with (
            patch("app.services.chat.stream.stream_chat", _stream),
            patch(
                "app.services.chat.stream.get_retriever", return_value=_fake_retriever()
            ),
        ):
            chunks = [c async for c in usecase.execute("sess-1", "年假有几天？")]

        assert chunks[0].startswith("Error:")
        assert memory.get_messages("sess-1") == []
        assert history.get_history("sess-1") == []


class TestChatUseCases:
    def test_start_new_chat_clears_display_and_llm_memory(self):
        turn = [ChatMessage(role=MessageRole.USER, content="hi")]
        memory.append_messages("sess-3", turn)
        history.append_history("sess-3", turn)
        StartNewChat().execute("sess-3")
        assert memory.get_messages("sess-3") == []
        assert history.get_history("sess-3") == []

    def test_display_history_is_not_trimmed_with_llm_memory(self, monkeypatch):
        from infra.config import settings

        monkeypatch.setattr(
            settings,
            "llm_settings",
            settings.llm_settings.model_copy(update={"max_history_messages": 2}),
        )
        for index in range(3):
            turn = [
                ChatMessage(role=MessageRole.USER, content=f"q{index}"),
                ChatMessage(role=MessageRole.ASSISTANT, content=f"a{index}"),
            ]
            history.append_history("sess-4", turn)
            memory.append_messages("sess-4", turn)

        assert [m.content for m in memory.get_messages("sess-4")] == ["q2", "a2"]
        assert [m.content for m in history.get_history("sess-4")] == [
            "q0",
            "a0",
            "q1",
            "a1",
            "q2",
            "a2",
        ]

    def test_get_chat_history(self):
        history.append_history(
            "sess-5",
            [
                ChatMessage(role=MessageRole.USER, content="问题"),
                ChatMessage(role=MessageRole.ASSISTANT, content="回答"),
            ],
        )
        messages = GetChatHistory().execute("sess-5")
        assert [m.content for m in messages] == ["问题", "回答"]


def test_format_context():
    text = format_context(
        [TextNode(text="hello", metadata={"doc_name": "a.md", "chunk_index": 0})]
    )
    assert "a.md" in text
    assert "hello" in text
