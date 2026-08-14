"""组装存储、切分、检索实现。"""

from domain.models.knowledge import ChunkParams
from infra.config import settings
from infra.rag.chunker import SentenceChunker
from infra.rag.retriever import QdrantRetriever
from infra.rag.store import QdrantKnowledgeStore

_store: QdrantKnowledgeStore | None = None
_chunker: SentenceChunker | None = None
_retriever: QdrantRetriever | None = None


def get_store() -> QdrantKnowledgeStore:
    global _store
    if _store is None:
        _store = QdrantKnowledgeStore()
    return _store


def get_chunker() -> SentenceChunker:
    global _chunker
    if _chunker is None:
        _chunker = SentenceChunker()
    return _chunker


def get_retriever() -> QdrantRetriever:
    global _retriever
    if _retriever is None:
        _retriever = QdrantRetriever()
    return _retriever


def default_chunk_params() -> ChunkParams:
    rag = settings.rag_settings
    return ChunkParams(size=rag.chunk_size, overlap=rag.chunk_overlap)
