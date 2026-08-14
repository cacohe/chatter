"""知识库目录快照：LlamaIndex 没有对应结构。"""

from dataclasses import dataclass


@dataclass(frozen=True)
class DocumentRecord:
    """知识库目录中的一条文档。"""

    name: str
    chunk_count: int


@dataclass(frozen=True)
class ChunkParams:
    size: int
    overlap: int


@dataclass(frozen=True)
class KnowledgeSnapshot:
    """当前知识库快照。"""

    documents: list[DocumentRecord]
    chunk_params: ChunkParams

    @property
    def document_count(self) -> int:
        return len(self.documents)

    @property
    def chunk_count(self) -> int:
        return sum(item.chunk_count for item in self.documents)


def validate_chunk_params(chunk_size: int, overlap: int) -> None:
    if chunk_size < 0:
        raise ValueError("chunk_size 不能小于 0")
    if overlap < 0:
        raise ValueError("chunk_overlap 不能小于 0")
    if overlap >= chunk_size:
        raise ValueError("chunk_overlap 必须小于 chunk_size")
