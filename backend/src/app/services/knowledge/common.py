"""知识库用例共享逻辑：摘要组装、分块参数落地、按来源前缀入库。"""

from pathlib import Path

from llama_index.core import Document

from domain.exceptions import BusinessException
from domain.schemas import knowledge as knowledge_schema
from infra.config import settings
from infra.rag.loader import ingest_llama_documents, validate_chunk_params
from infra.rag.store import KnowledgeStore, get_knowledge_store


def build_summary() -> knowledge_schema.KnowledgeSummary:
    """从当前 KnowledgeStore 汇总文档数与每篇分块数。"""
    store = get_knowledge_store()
    doc_chunk_counts: dict[str, int] = {}
    for node in store.nodes:
        name = str(node.metadata.get("doc_name") or "")
        doc_chunk_counts[name] = doc_chunk_counts.get(name, 0) + 1

    documents = [
        knowledge_schema.DocumentInfo(
            name=name, chunk_count=doc_chunk_counts.get(name, 0)
        )
        for name in store.document_names
    ]
    return knowledge_schema.KnowledgeSummary(
        document_count=store.document_count,
        chunk_count=len(store.nodes),
        chunk_size=store.chunk_size,
        chunk_overlap=store.chunk_overlap,
        documents=documents,
    )


def prepare_store(
    *,
    chunk_size: int | None,
    overlap: int | None,
) -> tuple[KnowledgeStore, int, int]:
    """解析分块参数并确保种子目录存在（上传本身不写该目录）。"""
    store = get_knowledge_store()
    size = chunk_size if chunk_size is not None else store.chunk_size
    ov = overlap if overlap is not None else store.chunk_overlap
    if size < 50:
        size = settings.rag_settings.chunk_size
    validate_chunk_params(size, ov)
    docs_path = (
        Path(store.docs_path or settings.rag_settings.docs_path).expanduser().resolve()
    )
    store.docs_path = str(docs_path)
    store.chunk_size = size
    store.chunk_overlap = ov
    docs_path.mkdir(parents=True, exist_ok=True)
    return store, size, ov


def ingest_source(
    documents: list[Document],
    *,
    prefix: str,
    chunk_size: int | None,
    overlap: int | None,
) -> knowledge_schema.KnowledgeSummary:
    """将一批 LlamaIndex Document 写入知识库，并替换同前缀的旧文档。"""
    usable = [
        document for document in documents if (document.get_content() or "").strip()
    ]
    if not usable:
        raise BusinessException("没有可导入的知识内容")
    store, size, ov = prepare_store(chunk_size=chunk_size, overlap=overlap)
    # 同一来源再次导入时覆盖旧文档，避免 web/db 前缀下堆积重复条目
    store.remove_documents_with_prefix(prefix)
    ingested = ingest_llama_documents(
        store, usable, chunk_size=size, overlap=ov, default_name=prefix
    )
    if ingested == 0:
        raise BusinessException("没有可导入的知识内容")
    return build_summary()
