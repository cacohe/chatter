import uuid
from pathlib import Path

from src.backend.infra.rag.store import (
    DocumentChunk,
    KnowledgeStore,
    get_knowledge_store,
    set_knowledge_store,
)
from src.shared.config import settings
from src.shared.logger import logger

SUPPORTED_SUFFIXES = {".txt", ".md", ".markdown"}


def chunk_text(text: str, chunk_size: int, overlap: int) -> list[str]:
    text = text.strip()
    if not text:
        return []
    if len(text) <= chunk_size:
        return [text]

    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        if end >= len(text):
            break
        start = max(end - overlap, start + 1)
    return chunks


def validate_chunk_params(chunk_size: int, overlap: int) -> None:
    if chunk_size < 50:
        raise ValueError("chunk_size 不能小于 50")
    if overlap < 0:
        raise ValueError("chunk_overlap 不能小于 0")
    if overlap >= chunk_size:
        raise ValueError("chunk_overlap 必须小于 chunk_size")


def _resolve_chunk_params(
    chunk_size: int | None, overlap: int | None
) -> tuple[int, int]:
    size = chunk_size if chunk_size is not None else settings.rag_settings.chunk_size
    ov = overlap if overlap is not None else settings.rag_settings.chunk_overlap
    validate_chunk_params(size, ov)
    return size, ov


def ingest_text(
    store: KnowledgeStore,
    doc_name: str,
    content: str,
    *,
    chunk_size: int,
    overlap: int,
) -> int:
    store.remove_document(doc_name)
    parts = chunk_text(content, chunk_size, overlap)
    doc_id = str(uuid.uuid4())
    for idx, part in enumerate(parts):
        store.chunks.append(
            DocumentChunk(
                doc_id=doc_id,
                doc_name=doc_name,
                content=part,
                chunk_index=idx,
            )
        )
    store.document_names.append(doc_name)
    store.document_count += 1
    logger.info(f"Ingested RAG doc: {doc_name} ({len(parts)} chunks)")
    return len(parts)


def load_docs(
    docs_path: str | None = None,
    *,
    chunk_size: int | None = None,
    overlap: int | None = None,
) -> KnowledgeStore:
    """从目录加载全部文档到内存知识库。"""
    size, ov = _resolve_chunk_params(chunk_size, overlap)
    path = Path(docs_path or settings.rag_settings.docs_path).expanduser().resolve()
    store = KnowledgeStore(
        docs_path=str(path),
        chunk_size=size,
        chunk_overlap=ov,
    )
    store.clear()
    set_knowledge_store(store)

    if not path.exists():
        logger.warning(f"RAG docs path does not exist: {path}")
        return store

    if not path.is_dir():
        logger.warning(f"RAG docs path is not a directory: {path}")
        return store

    files = sorted(
        p
        for p in path.rglob("*")
        if p.is_file() and p.suffix.lower() in SUPPORTED_SUFFIXES
    )

    for file_path in files:
        try:
            content = file_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
            logger.warning(f"Decoded with errors ignored: {file_path}")
        except Exception as e:
            logger.exception(f"Failed to read {file_path}: {e}")
            continue

        doc_name = str(file_path.relative_to(path))
        ingest_text(store, doc_name, content, chunk_size=size, overlap=ov)

    logger.info(
        f"RAG knowledge loaded: {store.document_count} docs, "
        f"{len(store.chunks)} chunks from {path} "
        f"(chunk_size={size}, overlap={ov})"
    )
    return get_knowledge_store()


def reload_docs(
    *,
    chunk_size: int | None = None,
    overlap: int | None = None,
    docs_path: str | None = None,
) -> KnowledgeStore:
    store = get_knowledge_store()
    path = docs_path or store.docs_path or settings.rag_settings.docs_path
    return load_docs(path, chunk_size=chunk_size, overlap=overlap)


def save_uploaded_file(filename: str, content: bytes, docs_path: str | None = None) -> Path:
    suffix = Path(filename).suffix.lower()
    if suffix not in SUPPORTED_SUFFIXES:
        raise ValueError(f"不支持的文件类型: {suffix or '(无扩展名)'}")

    path = Path(docs_path or settings.rag_settings.docs_path).expanduser().resolve()
    path.mkdir(parents=True, exist_ok=True)
    safe_name = Path(filename).name
    if not safe_name or safe_name in {".", ".."}:
        raise ValueError("无效的文件名")

    file_path = path / safe_name
    file_path.write_bytes(content)
    return file_path
