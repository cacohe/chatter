"""统一的 Qdrant 客户端：连接、入库、列举、按文档删除、检索。"""

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
        """
        将切分后的文档块写入 Qdrant 向量库
        """
        if not chunks:
            return
        self._get_index().insert_nodes(chunks)
        self._ensure_doc_id_index()
        by_doc: dict[str, int] = {}
        for chunk in chunks:
            doc_id = _node_doc_id(chunk)
            by_doc[doc_id] = by_doc.get(doc_id, 0) + 1
        for doc_id, count in by_doc.items():
            logger.info(f"Ingested RAG doc: {doc_id} ({count} chunks)")

    def delete_document(self, doc_id: str) -> None:
        """
        按 doc_id 批量删除 Qdrant 向量库中 对应文档的所有文档块
        """
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
        """
        列出 Qdrant 向量库中 所有文档的文档块
        """
        counts: dict[str, int] = {}
        order: list[str] = []
        for _, payload in self._iter_points():
            doc_id = _payload_doc_id(payload)
            if not doc_id:
                continue
            if doc_id not in counts:
                order.append(doc_id)
                counts[doc_id] = 0
            counts[doc_id] += 1
        return [DocumentRecord(name=name, chunk_count=counts[name]) for name in order]

    def list_chunks(
        self, *, doc_id: str | None = None, limit: int = 50
    ) -> list[TextNode]:
        """
        列出 Qdrant 向量库中 指定文档的文档块
        """
        records: list[TextNode] = []
        for _, payload in self._iter_points():
            current_doc_id = _payload_doc_id(payload)
            if not current_doc_id:
                continue
            if doc_id and current_doc_id != doc_id:
                continue
            index = _payload_chunk_index(payload)
            node = TextNode(
                text=_payload_text(payload),
                metadata=_node_metadata(payload, current_doc_id, index),
            )
            node.relationships[NodeRelationship.SOURCE] = RelatedNodeInfo(
                node_id=current_doc_id
            )
            records.append(node)
        records.sort(
            key=lambda item: (
                str(item.metadata.get("doc_id") or ""),
                int(item.metadata.get("chunk_index") or 0),
            )
        )
        if limit < 1:
            return []
        return records[:limit]

    def retrieve(self, query: str, top_k: int) -> list[TextNode]:
        """
        检索 Qdrant 向量库中 与查询最相似的文档块，返回前 top_k 个
        """
        if not self._collection_ready():
            return []
        try:
            results = (
                self._get_index().as_retriever(similarity_top_k=top_k).retrieve(query)
            )
        except Exception:
            logger.exception("LlamaIndex Qdrant retrieve failed")
            return []
        nodes: list[TextNode] = []
        for result in results:
            node = result.node
            # 评分在系统侧保存一份，后续可用于来源排序与阈值过滤。
            if result.score is not None:
                node.metadata["score"] = float(result.score)
            nodes.append(node)
        return nodes

    def reset(self) -> None:
        """
        重置 Qdrant 向量库
        """
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
            if _use_in_memory_qdrant():
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
        if self._doc_id_indexed or _use_in_memory_qdrant():
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


def _use_in_memory_qdrant() -> bool:
    mode = settings.rag_settings.qdrant_mode.strip().lower()
    if mode:
        if mode not in {"memory", "cloud"}:
            raise ValueError("QDRANT_MODE 仅支持 memory 或 cloud")
        return mode == "memory"
    return _is_memory_url(settings.rag_settings.qdrant_url)


def _payload_doc_id(payload: dict[str, Any]) -> str:
    value = payload.get("doc_id")
    return str(value) if value else ""


def _payload_chunk_index(payload: dict[str, Any]) -> int:
    try:
        return int(payload.get("chunk_index") or 0)
    except (TypeError, ValueError):
        return 0


def _payload_text(payload: dict[str, Any]) -> str:
    value = payload.get("text")
    return str(value) if value is not None else ""


def _node_doc_id(node: TextNode) -> str:
    value = node.metadata.get("doc_id")
    return str(value) if value else ""


def _node_metadata(payload: dict[str, Any], doc_id: str, chunk_index: int) -> dict[str, Any]:
    metadata: dict[str, Any] = {
        "doc_id": doc_id,
        "doc_name": str(payload.get("doc_name") or doc_id),
        "chunk_index": chunk_index,
    }
    for key in ("source_id", "source_type", "source_uri"):
        value = payload.get(key)
        if value is not None:
            metadata[key] = value
    score = payload.get("score")
    if score is not None:
        metadata["score"] = score
    return metadata
