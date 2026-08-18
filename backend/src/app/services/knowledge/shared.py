"""知识库业务流程：同名覆盖入库、按来源替换、删除。"""

from llama_index.core import Document
from llama_index.core.schema import TextNode

from domain.exceptions import BusinessException
from domain.models.knowledge import (
    ChunkParams,
    KnowledgeSnapshot,
    validate_chunk_params,
)
from infra.rag.runtime import default_chunk_params, get_chunker, get_store

MIN_CHUNK_SIZE = 50

_current_params: ChunkParams | None = None


def snapshot() -> KnowledgeSnapshot:
    """
    获取知识库的快照
    """
    return KnowledgeSnapshot(
        documents=get_store().list_documents(),
        chunk_params=_current_params or default_chunk_params(),
    )


def list_chunks(*, doc_id: str | None = None, limit: int = 50) -> list[TextNode]:
    """
    列出 向量数据库中 指定文档的文档块
    """
    return get_store().list_chunks(doc_id=doc_id, limit=limit)


def ingest_documents(
    documents: list[Document],
    *,
    chunk_size: int | None = None,
    overlap: int | None = None,
    replace_source: str | None = None,
    default_id: str = "document",
) -> KnowledgeSnapshot:
    """
    将 Document 列表写入 向量数据库
    """
    usable = [document for document in documents if document.text.strip()]
    if not usable:
        raise BusinessException("没有可导入的知识内容")
    params = _resolve_params(chunk_size, overlap)
    store = get_store()
    chunker = get_chunker()
    if replace_source:
        _delete_source(replace_source)
    ingested = 0
    for document in usable:
        doc_id = (document.doc_id or "").strip() or default_id
        named = Document(
            text=document.text.strip(),
            doc_id=doc_id,
            metadata=dict(document.metadata),
        )
        store.delete_document(named.doc_id)
        chunks = chunker.split(named, params)
        if not chunks:
            continue
        store.upsert_chunks(chunks)
        ingested += len(chunks)
    if ingested == 0:
        raise BusinessException("没有可导入的知识内容")
    return snapshot()


def delete_document(doc_id: str) -> KnowledgeSnapshot:
    """
    删除 向量数据库中 指定文档的所有文档块
    """
    name = (doc_id or "").strip()
    if not name:
        raise BusinessException("请指定要删除的文档")
    store = get_store()
    if not any(item.name == name for item in store.list_documents()):
        raise BusinessException("文档不存在", status_code=404)
    store.delete_document(name)
    return snapshot()


def _resolve_params(size: int | None, overlap: int | None) -> ChunkParams:
    """
    解析 文档块 参数，确保参数在合理范围内
    """
    global _current_params
    current = _current_params or default_chunk_params()
    resolved_size = size if size is not None else current.size
    resolved_overlap = overlap if overlap is not None else current.overlap
    if resolved_size < MIN_CHUNK_SIZE:
        resolved_size = default_chunk_params().size
    validate_chunk_params(resolved_size, resolved_overlap)
    _current_params = ChunkParams(size=resolved_size, overlap=resolved_overlap)
    return _current_params


def _delete_source(source_id: str) -> None:
    """
    删除 向量数据库中 指定来源的所有文档
    """
    if not source_id:
        return
    store = get_store()
    for document in store.list_documents():
        name = document.name
        if name == source_id or name.startswith(source_id + "/"):
            store.delete_document(name)
