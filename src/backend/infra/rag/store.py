from dataclasses import dataclass, field


@dataclass
class DocumentChunk:
    doc_id: str
    doc_name: str
    content: str
    chunk_index: int


@dataclass
class KnowledgeStore:
    """进程内知识库"""

    docs_path: str = ""
    chunk_size: int = 500
    chunk_overlap: int = 50
    document_count: int = 0
    document_names: list[str] = field(default_factory=list)
    chunks: list[DocumentChunk] = field(default_factory=list)

    def clear(self) -> None:
        self.document_count = 0
        self.document_names = []
        self.chunks = []

    def remove_document(self, doc_name: str) -> None:
        if doc_name in self.document_names:
            self.document_names.remove(doc_name)
            self.document_count = max(0, self.document_count - 1)
        self.chunks = [chunk for chunk in self.chunks if chunk.doc_name != doc_name]


_store: KnowledgeStore | None = None


def get_knowledge_store() -> KnowledgeStore:
    global _store
    if _store is None:
        _store = KnowledgeStore()
    return _store


def set_knowledge_store(store: KnowledgeStore) -> None:
    global _store
    _store = store
