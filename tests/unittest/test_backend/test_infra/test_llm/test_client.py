"""Tests for LiteLLM client."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.backend.domain.exceptions import BusinessException
from src.backend.infra.llm.client import resolve_model, stream_chat


class TestResolveModel:
    def test_resolve_known_model(self):
        assert resolve_model("qwen3.7-max") == "dashscope/qwen3.7-max"

    def test_resolve_unknown_raises(self):
        with pytest.raises(BusinessException, match="默认模型未注册"):
            resolve_model("unknown-model")


class TestStreamChat:
    @pytest.mark.asyncio
    async def test_stream_chat_yields_chunks(self):
        chunk1 = MagicMock()
        chunk1.choices = [MagicMock(delta=MagicMock(content="Hel"))]
        chunk2 = MagicMock()
        chunk2.choices = [MagicMock(delta=MagicMock(content="lo"))]

        async def mock_stream():
            for chunk in (chunk1, chunk2):
                yield chunk

        with patch(
            "src.backend.infra.llm.client.litellm.acompletion",
            new_callable=AsyncMock,
            return_value=mock_stream(),
        ) as mock_completion:
            chunks = [
                chunk
                async for chunk in stream_chat(
                    [{"role": "user", "content": "Hi"}],
                    model_id="qwen3.7-max",
                )
            ]

            assert chunks == ["Hel", "lo"]
            mock_completion.assert_awaited_once()
            assert mock_completion.await_args.kwargs["model"] == "dashscope/qwen3.7-max"
            assert mock_completion.await_args.kwargs["stream"] is True

    @pytest.mark.asyncio
    async def test_stream_chat_raises_business_exception_on_error(self):
        with patch(
            "src.backend.infra.llm.client.litellm.acompletion",
            new_callable=AsyncMock,
            side_effect=RuntimeError("api error"),
        ):
            with pytest.raises(BusinessException, match="LLM 流式调用失败"):
                async for _ in stream_chat(
                    [{"role": "user", "content": "Hi"}],
                    model_id="qwen3.7-max",
                ):
                    pass
