"""组装切分器与 Qdrant 客户端。"""

from domain.models.knowledge import ChunkParams
from infra.config import settings
from infra.qdrant.client import get_qdrant_client
from infra.rag.chunker import SentenceChunker

_chunker: SentenceChunker | None = None


def get_store():
    return get_qdrant_client()


def get_chunker() -> SentenceChunker:
    global _chunker
    if _chunker is None:
        _chunker = SentenceChunker()
    return _chunker


def get_retriever():
    return get_qdrant_client()


def default_chunk_params() -> ChunkParams:
    rag = settings.rag_settings
    return ChunkParams(size=rag.chunk_size, overlap=rag.chunk_overlap)
