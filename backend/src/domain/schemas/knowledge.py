"""知识库相关的请求/响应模型。"""

from pydantic import BaseModel, Field, field_validator


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
    """知识库快照（文档数、分块参数），不是服务健康状态。"""

    document_count: int
    chunk_count: int
    chunk_size: int
    chunk_overlap: int
    documents: list[DocumentInfo]


class ChunkParamsMixin(BaseModel):
    chunk_size: int | None = Field(
        default=None, ge=50, le=10000, description="分块大小"
    )
    chunk_overlap: int | None = Field(default=None, ge=0, description="分块重叠")

    @field_validator("chunk_overlap")
    @classmethod
    def overlap_less_than_size(cls, overlap: int | None, info):
        chunk_size = info.data.get("chunk_size")
        if overlap is not None and chunk_size is not None and overlap >= chunk_size:
            raise ValueError("chunk_overlap 必须小于 chunk_size")
        return overlap


class ReloadKnowledgeRequest(BaseModel):
    chunk_size: int = Field(..., ge=50, le=10000, description="分块大小")
    chunk_overlap: int = Field(..., ge=0, description="分块重叠")

    @field_validator("chunk_overlap")
    @classmethod
    def overlap_less_than_size(cls, overlap: int, info):
        chunk_size = info.data.get("chunk_size")
        if chunk_size is not None and overlap >= chunk_size:
            raise ValueError("chunk_overlap 必须小于 chunk_size")
        return overlap


class SyncDatabaseRequest(BaseModel):
    uri: str = Field(..., min_length=1, description="SQLAlchemy 连接串")
    query: str = Field(..., min_length=1, description="查询语句")
    name: str | None = Field(default=None, description="来源名称")
    chunk_size: int | None = Field(default=None, ge=50, le=10000)
    chunk_overlap: int | None = Field(default=None, ge=0)


class IngestWebRequest(BaseModel):
    url: str = Field(..., min_length=1, description="网页链接")
    name: str | None = Field(default=None, description="来源名称")
    chunk_size: int | None = Field(default=None, ge=50, le=10000)
    chunk_overlap: int | None = Field(default=None, ge=0)
