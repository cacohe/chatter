"""Tests for embedding dimension wiring."""

from http import HTTPStatus
from types import SimpleNamespace

import dashscope

from infra.config import settings
from infra.rag.embeddings import get_embed_model


def test_dashscope_embedding_requests_configured_dimension(monkeypatch):
    monkeypatch.setattr(
        settings,
        "rag_settings",
        settings.rag_settings.model_copy(
            update={"embed_model": "qwen3.7-text-embedding", "embed_dim": 1536}
        ),
    )
    captured: dict = {}

    def fake_call(**kwargs):
        captured.update(kwargs)
        return SimpleNamespace(
            status_code=HTTPStatus.OK,
            output={
                "embeddings": [{"text_index": 0, "embedding": [0.1] * 1536}],
            },
        )

    monkeypatch.setattr(dashscope.TextEmbedding, "call", fake_call)
    vector = get_embed_model().get_text_embedding("hello")
    assert captured["dimension"] == 1536
    assert captured["model"] == "qwen3.7-text-embedding"
    assert len(vector) == 1536
