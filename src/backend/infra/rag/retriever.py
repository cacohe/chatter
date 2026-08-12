from llama_index.retrievers.bm25 import BM25Retriever

from src.backend.infra.rag.store import DocumentChunk, get_knowledge_store
from src.shared.config import settings
from src.shared.logger import logger

_BM25_TOKEN_PATTERN = r"(?u)[\u4e00-\u9fff]|[a-zA-Z0-9]+"


def retrieve(query: str, top_k: int | None = None) -> list[DocumentChunk]:
    store = get_knowledge_store()
    if not store.nodes:
        return []

    k = top_k if top_k is not None else settings.rag_settings.top_k
    try:
        retriever = BM25Retriever.from_defaults(
            nodes=store.nodes,
            similarity_top_k=k,
            skip_stemming=True,
            language="zh",
            token_pattern=_BM25_TOKEN_PATTERN,
        )
        results = retriever.retrieve(query)
    except Exception:
        logger.exception("LlamaIndex BM25 retrieve failed")
        return []

    chunks: list[DocumentChunk] = []
    for result in results:
        node = result.node
        chunks.append(
            DocumentChunk(
                doc_id=node.node_id,
                doc_name=str(node.metadata.get("doc_name") or ""),
                content=node.get_content(),
                chunk_index=int(node.metadata.get("chunk_index") or 0),
            )
        )
    return chunks


def format_context(chunks: list[DocumentChunk]) -> str:
    if not chunks:
        return ""
    parts = []
    for i, chunk in enumerate(chunks, start=1):
        parts.append(f"[{i}] 来源: {chunk.doc_name}\n{chunk.content}")
    return "\n\n".join(parts)
