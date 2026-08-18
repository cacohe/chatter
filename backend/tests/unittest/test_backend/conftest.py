"""单元测试使用进程内 Qdrant 与 MockEmbedding，不依赖外部服务。"""

import pytest
from llama_index.core.embeddings.mock_embed_model import MockEmbedding

import app.services.knowledge.shared as kb_ops
import infra.rag.runtime as rag_runtime
from infra.chat.history import reset_histories
from infra.chat.memory import reset_memory
from infra.config import settings
from infra.qdrant.client import reset_client


def _reset_rag() -> None:
    kb_ops._current_params = None
    rag_runtime._chunker = None
    reset_client()


@pytest.fixture(autouse=True)
def qdrant_in_memory(monkeypatch):
    monkeypatch.setattr(
        settings,
        "rag_settings",
        settings.rag_settings.model_copy(update={"qdrant_url": ":memory:"}),
    )
    monkeypatch.setattr(
        "infra.rag.embeddings.get_embed_model",
        lambda: MockEmbedding(embed_dim=settings.rag_settings.embed_dim),
    )
    _reset_rag()
    reset_memory()
    reset_histories()
    yield
    _reset_rag()
    reset_memory()
    reset_histories()
