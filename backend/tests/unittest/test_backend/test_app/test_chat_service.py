"""Tests for StreamChat use case and backend chat memory."""

from unittest.mock import MagicMock, patch

import pytest
from llama_index.core.schema import TextNode

from app.services.chat.get_history import GetChatHistory
from app.services.chat.start_new_chat import StartNewChat
from app.services.chat.stream import (
    StreamChat,
    _citable_chunks,
    build_citations,
    format_context,
    validate_citations,
)
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
        assert displayed[1].citations == []

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
        displayed = history.get_history("sess-1")
        assert displayed[1].citations[0].doc_name == "leave.md"
        # 回答 "10 天" 不含 [1]，所以该来源应标记为未引用
        assert displayed[1].citations[0].used is False

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


def test_build_citations():
    citations = build_citations(
        [
            TextNode(
                text="hello\nworld",
                metadata={
                    "doc_name": "a.md",
                    "chunk_index": "1",
                    "source_uri": "file://a.md",
                    "score": "0.42",
                },
            )
        ]
    )
    assert len(citations) == 1
    assert citations[0].index == 1
    assert citations[0].doc_name == "a.md"
    assert citations[0].chunk_index == 1
    assert "hello world" in citations[0].snippet
    assert citations[0].source_uri == "file://a.md"
    assert citations[0].score == 0.42


def _make_citation(index: int, doc_name: str = "doc.md"):
    from domain.models.chat import Citation

    return Citation(
        index=index,
        doc_name=doc_name,
        chunk_index=0,
        snippet="...",
    )


class TestValidateCitations:
    """validate_citations：校验回答正文中 [n] 与 citations 的对应关系。"""

    def test_marks_used_and_unused(self):
        """回答引用了 [1] 但未引用 [2]，两者应分别标记。"""
        citations = [_make_citation(1), _make_citation(2)]
        result = validate_citations("根据文档 [1]，年假 10 天。", citations)
        assert result[0].used is True
        assert result[1].used is False

    def test_all_cited(self):
        """回答同时引用了 [1] 和 [2]，均标记为已引用。"""
        citations = [_make_citation(1), _make_citation(2)]
        result = validate_citations("政策 [1] 规定，详见 [2]。", citations)
        assert all(c.used is True for c in result)

    def test_none_cited(self):
        """回答未引用任何编号，全部标记为未引用。"""
        citations = [_make_citation(1)]
        result = validate_citations("知识库中未找到相关信息。", citations)
        assert result[0].used is False

    def test_invalid_index_ignored(self):
        """回答中出现超出范围的编号 [99]，不影响有效引用的标记。"""
        citations = [_make_citation(1)]
        result = validate_citations("参考 [1] 和 [99]。", citations)
        assert result[0].used is True
        assert len(result) == 1

    def test_empty_citations(self):
        """无检索结果时，校验应返回空列表。"""
        result = validate_citations("没有参考文档。", [])
        assert result == []

    def test_does_not_mutate_original(self):
        """校验不应修改原始 citation 对象。"""
        original = _make_citation(1)
        assert original.used is None
        validate_citations("[1] 引用。", [original])
        assert original.used is None

    def test_fullwidth_brackets(self):
        """全角方括号【n】和［n］也应识别为引用。"""
        citations = [_make_citation(1), _make_citation(2), _make_citation(3)]
        result = validate_citations("参考【1】和［2］。", citations)
        assert result[0].used is True
        assert result[1].used is True
        assert result[2].used is False


class TestCitableChunksAlignment:
    """format_context 与 build_citations 的编号必须一致。"""

    def test_skips_empty_doc_name_and_renumbers(self):
        """无 doc_name 的 chunk 被跳过，后续 chunk 编号连续不跳号。"""
        chunks = [
            TextNode(text="no name", metadata={"doc_name": "", "chunk_index": 0}),
            TextNode(text="has name", metadata={"doc_name": "a.md", "chunk_index": 0}),
            TextNode(
                text="also named", metadata={"doc_name": "b.md", "chunk_index": 1}
            ),
        ]
        numbered = _citable_chunks(chunks)
        assert len(numbered) == 2
        assert numbered[0][0] == 1
        assert numbered[1][0] == 2

    def test_format_and_build_same_indices(self):
        """format_context 中的 [n] 与 build_citations 的 index 一一对应。"""
        chunks = [
            TextNode(text="skip me", metadata={"doc_name": "", "chunk_index": 0}),
            TextNode(text="content A", metadata={"doc_name": "a.md", "chunk_index": 0}),
            TextNode(text="content B", metadata={"doc_name": "b.md", "chunk_index": 1}),
        ]
        context = format_context(chunks)
        citations = build_citations(chunks)
        # context 不应包含 [3]（跳过的 chunk 不应占编号）
        assert "[1] 来源: a.md" in context
        assert "[2] 来源: b.md" in context
        assert "[3]" not in context
        # citations 编号与 context 一致
        assert citations[0].index == 1
        assert citations[0].doc_name == "a.md"
        assert citations[1].index == 2
        assert citations[1].doc_name == "b.md"
