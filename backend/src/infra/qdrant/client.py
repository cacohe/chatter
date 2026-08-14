"""统一的 Qdrant 客户端：连接、入库、列举、按文档删除、检索。"""

import json
from typing import Any

from llama_index.core import VectorStoreIndex
from llama_index.core.schema import NodeRelationship, RelatedNodeInfo, TextNode
from llama_index.vector_stores.qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from qdrant_client.http.models import (
    FieldCondition,
    Filter,
    MatchValue,
    PayloadSchemaType,
)

from domain.models.knowledge import DocumentRecord
from infra.config import settings
from infra.logger import logger
from infra.rag.embeddings import configure_embeddings

_instance: "Client | None" = None


class Client:
    def __init__(self) -> None:
        self._raw: QdrantClient | None = None
        self._vector_store: QdrantVectorStore | None = None
        self._index: VectorStoreIndex | None = None
        self._doc_id_indexed = False

    def upsert_chunks(self, chunks: list[TextNode]) -> None:
        if not chunks:
            return
        self._get_index().insert_nodes(chunks)
        self._ensure_doc_id_index()
        by_doc: dict[str, int] = {}
        for chunk in chunks:
            doc_id = str(chunk.metadata.get("doc_name") or "")
            by_doc[doc_id] = by_doc.get(doc_id, 0) + 1
        for doc_id, count in by_doc.items():
            logger.info(f"Ingested RAG doc: {doc_id} ({count} chunks)")

    def delete_document(self, doc_id: str) -> None:
        if not doc_id or not self._collection_ready():
            return
        self._ensure_doc_id_index()
        self._get_raw().delete(
            collection_name=self._collection,
            points_selector=Filter(
                must=[
                    FieldCondition(
                        key="doc_id",
                        match=MatchValue(value=doc_id),
                    )
                ]
            ),
        )

    def list_documents(self) -> list[DocumentRecord]:
        counts: dict[str, int] = {}
        order: list[str] = []
        for _, raw in self._iter_points():
            name = _doc_name(_flatten_payload(raw))
            if not name:
                continue
            if name not in counts:
                order.append(name)
                counts[name] = 0
            counts[name] += 1
        return [DocumentRecord(name=name, chunk_count=counts[name]) for name in order]

    def list_chunks(
        self, *, doc_id: str | None = None, limit: int = 50
    ) -> list[TextNode]:
        records: list[TextNode] = []
        for _, raw in self._iter_points():
            payload = _flatten_payload(raw)
            name = _doc_name(payload)
            if doc_id and name != doc_id:
                continue
            index = _chunk_index(payload)
            node = TextNode(
                text=_text(payload),
                metadata={"doc_name": name, "chunk_index": index},
            )
            node.relationships[NodeRelationship.SOURCE] = RelatedNodeInfo(node_id=name)
            records.append(node)
        records.sort(
            key=lambda item: (
                str(item.metadata.get("doc_name") or ""),
                int(item.metadata.get("chunk_index") or 0),
            )
        )
        if limit < 1:
            return []
        return records[:limit]

    def retrieve(self, query: str, top_k: int) -> list[TextNode]:
        if not self._collection_ready():
            return []
        try:
            results = (
                self._get_index().as_retriever(similarity_top_k=top_k).retrieve(query)
            )
        except Exception:
            logger.exception("LlamaIndex Qdrant retrieve failed")
            return []
        return [result.node for result in results]

    def reset(self) -> None:
        name = self._collection
        if self._raw is not None:
            try:
                if self._raw.collection_exists(name):
                    self._raw.delete_collection(name)
            except Exception:
                pass
        self._raw = None
        self._vector_store = None
        self._index = None
        self._doc_id_indexed = False

    @property
    def _collection(self) -> str:
        return settings.rag_settings.qdrant_collection

    def _get_raw(self) -> QdrantClient:
        if self._raw is None:
            url = settings.rag_settings.qdrant_url
            if _is_memory_url(url):
                self._raw = QdrantClient(":memory:")
            else:
                if not url:
                    raise ValueError("请配置 QDRANT_URL（Qdrant Cloud 集群地址）")
                api_key = settings.rag_settings.qdrant_api_key or None
                if not api_key:
                    raise ValueError("请配置 QDRANT_API_KEY（Qdrant Cloud API Key）")
                self._raw = QdrantClient(url=url, api_key=api_key)
        return self._raw

    def _get_index(self) -> VectorStoreIndex:
        if self._index is None:
            if self._vector_store is None:
                self._vector_store = QdrantVectorStore(
                    client=self._get_raw(),
                    collection_name=self._collection,
                    index_doc_id=True,
                )
            embed_model = configure_embeddings()
            self._index = VectorStoreIndex.from_vector_store(
                self._vector_store,
                embed_model=embed_model,
            )
        return self._index

    def _collection_ready(self) -> bool:
        try:
            return self._get_raw().collection_exists(self._collection)
        except Exception:
            logger.exception("Qdrant collection_exists failed")
            return False

    def _iter_points(self):
        if not self._collection_ready():
            return
        offset = None
        while True:
            points, offset = self._get_raw().scroll(
                collection_name=self._collection,
                limit=128,
                offset=offset,
                with_payload=True,
                with_vectors=False,
            )
            for point in points:
                yield point.id, dict(point.payload or {})
            if offset is None:
                break

    def _ensure_doc_id_index(self) -> None:
        """云端按 doc_id 过滤删除需要 keyword 索引；已有 collection 不会自动补建。"""
        if self._doc_id_indexed or _is_memory_url(settings.rag_settings.qdrant_url):
            return
        if not self._collection_ready():
            return
        try:
            self._get_raw().create_payload_index(
                collection_name=self._collection,
                field_name="doc_id",
                field_schema=PayloadSchemaType.KEYWORD,
            )
        except Exception as exc:
            message = str(exc).lower()
            if "already" not in message and "exists" not in message:
                raise
        self._doc_id_indexed = True


def get_qdrant_client() -> Client:
    global _instance
    if _instance is None:
        _instance = Client()
    return _instance


def reset_client() -> None:
    global _instance
    if _instance is not None:
        _instance.reset()
    _instance = None


def _is_memory_url(url: str) -> bool:
    return url.strip().lower() in {"", ":memory:", "memory"}


def _flatten_payload(payload: dict[str, Any]) -> dict[str, Any]:
    data = dict(payload)
    raw = data.get("_node_content")
    if not isinstance(raw, str):
        return data
    try:
        node = json.loads(raw)
    except json.JSONDecodeError:
        return data
    if not isinstance(node, dict):
        return data
    meta = node.get("metadata")
    if isinstance(meta, dict):
        for key, value in meta.items():
            data.setdefault(key, value)
    if node.get("text") and not data.get("text"):
        data["text"] = node["text"]
    return data


def _doc_name(payload: dict[str, Any]) -> str:
    for key in ("doc_name", "doc_id", "ref_doc_id", "document_id"):
        value = payload.get(key)
        if value:
            return str(value)
    return ""


def _chunk_index(payload: dict[str, Any]) -> int:
    try:
        return int(payload.get("chunk_index") or 0)
    except (TypeError, ValueError):
        return 0


def _text(payload: dict[str, Any]) -> str:
    value = payload.get("text")
    return str(value) if value is not None else ""
