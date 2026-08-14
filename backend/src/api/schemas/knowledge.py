"""知识库相关的请求/响应模型。"""

from pydantic import BaseModel, Field

from domain.models.knowledge import KnowledgeSnapshot


class DocumentInfo(BaseModel):
    """单个文档在摘要中的条目。"""

    name: str
    chunk_count: int


class ChunkPreview(BaseModel):
    """侧边栏预览用的分块片段。"""

    doc_name: str
    chunk_index: int
    content: str


class KnowledgeSummary(BaseModel):
    """知识库快照。chunk_size / chunk_overlap 是当前生效的入库参数。"""

    document_count: int
    chunk_count: int
    chunk_size: int
    chunk_overlap: int
    documents: list[DocumentInfo]


class SyncDatabaseRequest(BaseModel):
    uri: str = Field(..., min_length=1, description="SQLAlchemy 连接串")
    query: str = Field(..., min_length=1, description="查询语句")
    name: str | None = Field(
        default=None, description="可选备注，不参与覆盖身份（身份为连接串+查询）"
    )
    chunk_size: int | None = Field(default=None, ge=50, le=10000)
    chunk_overlap: int | None = Field(default=None, ge=0)


class IngestWebRequest(BaseModel):
    url: str = Field(..., min_length=1, description="网页链接")
    name: str | None = Field(
        default=None, description="可选备注，不参与覆盖身份（身份为规范化 URL）"
    )
    chunk_size: int | None = Field(default=None, ge=50, le=10000)
    chunk_overlap: int | None = Field(default=None, ge=0)


def to_summary(snapshot: KnowledgeSnapshot) -> KnowledgeSummary:
    params = snapshot.chunk_params
    return KnowledgeSummary(
        document_count=snapshot.document_count,
        chunk_count=snapshot.chunk_count,
        chunk_size=params.size,
        chunk_overlap=params.overlap,
        documents=[
            DocumentInfo(name=item.name, chunk_count=item.chunk_count)
            for item in snapshot.documents
        ],
    )
