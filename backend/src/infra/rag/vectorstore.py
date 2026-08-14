"""LlamaIndex VectorStoreIndex + Qdrant：连接、入库、按文档删除、滚动 payload。"""

from collections.abc import Iterator
from typing import Any

from llama_index.core import VectorStoreIndex
from llama_index.core.schema import BaseNode
from llama_index.vector_stores.qdrant import QdrantVectorStore
from qdrant_client import QdrantClient

from infra.config import settings
from infra.logger import logger
from infra.rag.embeddings import configure_embeddings

_client: QdrantClient | None = None
_vector_store: QdrantVectorStore | None = None
_index: VectorStoreIndex | None = None


def _is_memory_url(url: str) -> bool:
    return url.strip().lower() in {"", ":memory:", "memory"}


def get_qdrant_client() -> QdrantClient:
    """连接 Qdrant Cloud；仅测试传入 :memory: 时使用进程内客户端。"""
    global _client
    if _client is None:
        url = settings.rag_settings.qdrant_url
        if _is_memory_url(url):
            _client = QdrantClient(":memory:")
        else:
            if not url:
                raise ValueError("请配置 QDRANT_URL（Qdrant Cloud 集群地址）")
            api_key = settings.rag_settings.qdrant_api_key or None
            if not api_key:
                raise ValueError("请配置 QDRANT_API_KEY（Qdrant Cloud API Key）")
            _client = QdrantClient(url=url, api_key=api_key)
    return _client


def get_vector_store() -> QdrantVectorStore:
    global _vector_store
    if _vector_store is None:
        _vector_store = QdrantVectorStore(
            client=get_qdrant_client(),
            collection_name=settings.rag_settings.qdrant_collection,
            index_doc_id=not _is_memory_url(settings.rag_settings.qdrant_url),
        )
    return _vector_store


def get_index() -> VectorStoreIndex:
    global _index
    if _index is None:
        embed_model = configure_embeddings()
        _index = VectorStoreIndex.from_vector_store(
            get_vector_store(),
            embed_model=embed_model,
        )
    return _index


def upsert_nodes(nodes: list[BaseNode]) -> None:
    if not nodes:
        return
    get_index().insert_nodes(nodes)


def collection_ready() -> bool:
    """当前 collection 是否已存在（尚未入库时为 False）。"""
    try:
        return get_qdrant_client().collection_exists(
            settings.rag_settings.qdrant_collection
        )
    except Exception:
        logger.exception("Qdrant collection_exists failed")
        return False


def delete_document(doc_name: str) -> None:
    """从 Qdrant 删除指定文档的全部分块。文档不存在或尚未建库时直接返回。"""
    if not doc_name or not collection_ready():
        return
    try:
        get_index().delete_ref_doc(doc_name, delete_from_docstore=False)
    except Exception:
        logger.exception("Failed to delete document from Qdrant: %s", doc_name)


def iter_point_payloads() -> Iterator[dict[str, Any]]:
    """滚动当前 collection 的全部 payload（不含向量），供目录与预览使用。"""
    if not collection_ready():
        return
    client = get_qdrant_client()
    name = settings.rag_settings.qdrant_collection
    offset = None
    while True:
        points, offset = client.scroll(
            collection_name=name,
            limit=128,
            offset=offset,
            with_payload=True,
            with_vectors=False,
        )
        for point in points:
            yield dict(point.payload or {})
        if offset is None:
            break
