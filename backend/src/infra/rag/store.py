"""Qdrant + LlamaIndex：分块的写入、删除与列举。"""

import json
from typing import Any

from llama_index.core.schema import NodeRelationship, RelatedNodeInfo, TextNode

from domain.models.knowledge import DocumentRecord
from infra.logger import logger
from infra.rag.vectorstore import (
    delete_points,
    iter_point_payloads,
    iter_points,
    upsert_nodes,
)


class QdrantKnowledgeStore:
    def upsert_chunks(self, chunks: list[TextNode]) -> None:
        if not chunks:
            return
        upsert_nodes(chunks)
        by_doc: dict[str, int] = {}
        for chunk in chunks:
            doc_id = str(chunk.metadata.get("doc_name") or "")
            by_doc[doc_id] = by_doc.get(doc_id, 0) + 1
        for doc_id, count in by_doc.items():
            logger.info(f"Ingested RAG doc: {doc_id} ({count} chunks)")

    def delete_document(self, doc_id: str) -> None:
        point_ids = [
            point_id
            for point_id, raw in iter_points()
            if _doc_name(_flatten_payload(raw)) == doc_id
        ]
        delete_points(point_ids)

    def list_documents(self) -> list[DocumentRecord]:
        counts: dict[str, int] = {}
        order: list[str] = []
        for raw in iter_point_payloads():
            payload = _flatten_payload(raw)
            name = _doc_name(payload)
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
        for raw in iter_point_payloads():
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
