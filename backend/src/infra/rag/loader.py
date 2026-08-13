"""LlamaIndex 文档加载与句子分块，写入进程内 KnowledgeStore。"""

from pathlib import Path

from fsspec.implementations.memory import MemoryFileSystem
from llama_index.core import Document, Settings, SimpleDirectoryReader
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.node_parser.text.sentence import CHUNKING_REGEX
from llama_index.core.node_parser.text.utils import split_by_regex

from infra.config import settings
from infra.logger import logger
from infra.rag.store import KnowledgeStore, get_knowledge_store, set_knowledge_store

SUPPORTED_SUFFIXES = {".txt", ".md", ".markdown", ".pdf"}

# 本项目检索用 BM25，关闭 LlamaIndex 默认 LLM / embedding，避免隐式联网
Settings.llm = None
Settings.embed_model = None


def _splitter(chunk_size: int, overlap: int) -> SentenceSplitter:
    """
    用官方 SentenceSplitter
    """
    return SentenceSplitter(
        chunk_size=chunk_size,
        chunk_overlap=overlap,
        chunking_tokenizer_fn=split_by_regex(CHUNKING_REGEX),
    )


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


def _doc_name_from(document: Document, default_name: str) -> str:
    if document.metadata.get("doc_name"):
        return str(document.metadata["doc_name"])
    file_path = document.metadata.get("file_path") or document.metadata.get("file_name")
    if file_path:
        return Path(str(file_path)).name
    return default_name


def ingest_llama_documents(
    store: KnowledgeStore,
    documents: list[Document],
    *,
    chunk_size: int,
    overlap: int,
    default_name: str = "document",
) -> int:
    """
    将 LlamaIndex Document 切成 nodes 写入 store；同名文档先删后写。
    """
    splitter = _splitter(chunk_size, overlap)
    total = 0
    for document in documents:
        text = document.get_content().strip()
        if not text:
            continue
        doc_name = _doc_name_from(document, default_name)
        store.remove_document(doc_name)
        nodes = splitter.get_nodes_from_documents([document])
        for idx, node in enumerate(nodes):
            node.metadata["doc_name"] = doc_name
            node.metadata["chunk_index"] = idx
            store.nodes.append(node)
        store.document_names.append(doc_name)
        store.sources[doc_name] = text
        total += len(nodes)
        logger.info(f"Ingested RAG doc: {doc_name} ({len(nodes)} chunks)")
    return total


def documents_from_upload(filename: str, content: bytes) -> list[Document]:
    """
    用内存文件系统喂给 SimpleDirectoryReader，上传文件不落盘。
    """
    suffix = Path(filename).suffix.lower()
    if suffix not in SUPPORTED_SUFFIXES:
        raise ValueError(f"不支持的文件类型: {suffix or '(无扩展名)'}")
    safe_name = Path(filename).name
    if not safe_name or safe_name in {".", ".."}:
        raise ValueError("无效的文件名")

    fs = MemoryFileSystem()
    virtual_path = f"/{safe_name}"
    fs.pipe(virtual_path, content)
    documents = SimpleDirectoryReader(
        input_files=[virtual_path],
        required_exts=sorted(SUPPORTED_SUFFIXES),
        filename_as_id=True,
        fs=fs,
    ).load_data()
    named: list[Document] = []
    for document in documents:
        if not (document.get_content() or "").strip():
            continue
        document.metadata["doc_name"] = safe_name
        named.append(document)
    return named


def load_docs(
    docs_path: str | None = None,
    *,
    chunk_size: int | None = None,
    overlap: int | None = None,
) -> KnowledgeStore:
    """从磁盘种子目录加载 PDF / Markdown，并整体替换当前知识库。"""
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
        document.metadata["doc_name"] = doc_name

    ingest_llama_documents(
        store, documents, chunk_size=size, overlap=ov, default_name="document"
    )
    logger.info(
        f"RAG knowledge loaded: {store.document_count} docs, "
        f"{len(store.nodes)} chunks from {path} "
        f"(chunk_size={size}, overlap={ov})"
    )
    return get_knowledge_store()


def reload_docs(
    *,
    chunk_size: int | None = None,
    overlap: int | None = None,
    docs_path: str | None = None,
) -> KnowledgeStore:
    """
    先重载磁盘文件，再把未落盘的内存文档按新参数切回去。"""
    store = get_knowledge_store()
    path = docs_path or store.docs_path or settings.rag_settings.docs_path
    root = Path(path).expanduser().resolve()
    memory_docs = [
        Document(text=text, metadata={"doc_name": name})
        for name, text in store.sources.items()
        if not (root / name).is_file()
    ]
    loaded = load_docs(str(root), chunk_size=chunk_size, overlap=overlap)
    if memory_docs:
        size, ov = _resolve_chunk_params(chunk_size, overlap)
        ingest_llama_documents(
            loaded, memory_docs, chunk_size=size, overlap=ov, default_name="upload"
        )
    return get_knowledge_store()


def delete_stored_document(docs_path: str, doc_name: str) -> bool:
    """删除种子目录中的文件；拒绝路径逃逸，并清理空的中间目录。"""
    root = Path(docs_path).expanduser().resolve()
    target = (root / doc_name).expanduser().resolve()
    if target == root or not target.is_relative_to(root):
        raise ValueError("无效的文档路径")
    if not target.is_file():
        return False
    target.unlink()
    parent = target.parent
    while parent != root and parent.is_dir() and not any(parent.iterdir()):
        parent.rmdir()
        parent = parent.parent
    return True
