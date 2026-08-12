from pathlib import Path

from llama_index.core import Document, Settings, SimpleDirectoryReader
from llama_index.core.node_parser import SentenceSplitter

from src.backend.infra.rag.store import (
    DocumentChunk,
    KnowledgeStore,
    get_knowledge_store,
    set_knowledge_store,
)
from src.shared.config import settings
from src.shared.logger import logger

SUPPORTED_SUFFIXES = {".txt", ".md", ".markdown"}

Settings.llm = None
Settings.embed_model = None


def _splitter(chunk_size: int, overlap: int) -> SentenceSplitter:
    return SentenceSplitter(chunk_size=chunk_size, chunk_overlap=overlap)


def chunk_text(text: str, chunk_size: int, overlap: int) -> list[str]:
    text = text.strip()
    if not text:
        return []
    nodes = _splitter(chunk_size, overlap).get_nodes_from_documents(
        [Document(text=text)]
    )
    return [node.get_content() for node in nodes]


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
    nodes = _splitter(chunk_size, overlap).get_nodes_from_documents(
        [Document(text=content.strip())]
    )
    for idx, node in enumerate(nodes):
        node.metadata["doc_name"] = doc_name
        node.metadata["chunk_index"] = idx
        store.nodes.append(node)
        store.chunks.append(
            DocumentChunk(
                doc_id=node.node_id,
                doc_name=doc_name,
                content=node.get_content(),
                chunk_index=idx,
            )
        )
    store.document_names.append(doc_name)
    store.document_count += 1
    logger.info(f"Ingested RAG doc: {doc_name} ({len(nodes)} chunks)")
    return len(nodes)


def load_docs(
    docs_path: str | None = None,
    *,
    chunk_size: int | None = None,
    overlap: int | None = None,
) -> KnowledgeStore:
    """用 LlamaIndex 从目录加载文档并分块。"""
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

    try:
        documents = SimpleDirectoryReader(
            input_dir=str(path),
            required_exts=sorted(SUPPORTED_SUFFIXES),
            recursive=True,
            filename_as_id=True,
        ).load_data()
    except ValueError:
        logger.warning(f"No supported documents found in: {path}")
        return store

    for document in documents:
        file_path = Path(
            document.metadata.get("file_path")
            or document.metadata.get("file_name")
            or ""
        )
        try:
            doc_name = str(file_path.relative_to(path))
        except ValueError:
            doc_name = file_path.name or "document"
        ingest_text(
            store,
            doc_name,
            document.get_content(),
            chunk_size=size,
            overlap=ov,
        )

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


def save_uploaded_file(
    filename: str, content: bytes, docs_path: str | None = None
) -> Path:
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
