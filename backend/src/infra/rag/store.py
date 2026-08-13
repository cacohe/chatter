"""进程内知识库：LlamaIndex nodes 即分块，无独立向量库。"""

from dataclasses import dataclass, field

from llama_index.core.schema import BaseNode


@dataclass
class KnowledgeStore:
    """单进程单例知识库。

    sources 保留原文，供「重新分块」时把未落盘的上传/网页/库表再切一遍。
    """

    docs_path: str = ""
    chunk_size: int = 500
    chunk_overlap: int = 50
    document_names: list[str] = field(default_factory=list)
    nodes: list[BaseNode] = field(default_factory=list)
    sources: dict[str, str] = field(default_factory=dict)

    @property
    def document_count(self) -> int:
        return len(self.document_names)

    def clear(self) -> None:
        self.document_names = []
        self.nodes = []
        self.sources = {}

    def remove_document(self, doc_name: str) -> None:
        if doc_name in self.document_names:
            self.document_names.remove(doc_name)
        self.nodes = [
            node for node in self.nodes if node.metadata.get("doc_name") != doc_name
        ]
        self.sources.pop(doc_name, None)

    def remove_documents_with_prefix(self, prefix: str) -> None:
        """删除同一来源前缀下的全部文档（如再次同步 db/hr）。"""
        for name in list(self.document_names):
            if name.startswith(prefix):
                self.remove_document(name)


_store: KnowledgeStore | None = None


def get_knowledge_store() -> KnowledgeStore:
    """懒创建全局知识库；启动 lifespan 会再被 load_docs 替换。"""
    global _store
    if _store is None:
        _store = KnowledgeStore()
    return _store


def set_knowledge_store(store: KnowledgeStore) -> None:
    global _store
    _store = store
