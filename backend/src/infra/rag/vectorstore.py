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


def iter_points() -> Iterator[tuple[Any, dict[str, Any]]]:
    """滚动当前 collection 的点 id 与 payload（不含向量）。"""
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
            yield point.id, dict(point.payload or {})
        if offset is None:
            break


def iter_point_payloads() -> Iterator[dict[str, Any]]:
    """滚动当前 collection 的全部 payload（不含向量），供目录与预览使用。"""
    for _, payload in iter_points():
        yield payload


def delete_points(point_ids: list[Any]) -> None:
    """按点 id 删除，不走 payload 过滤（云端过滤需要 keyword 索引）。"""
    if not point_ids or not collection_ready():
        return
    get_qdrant_client().delete(
        collection_name=settings.rag_settings.qdrant_collection,
        points_selector=point_ids,
    )
