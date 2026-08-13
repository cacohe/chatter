from pydantic import BaseModel, Field, field_validator


class DocumentInfo(BaseModel):
    name: str
    chunk_count: int


class ChunkPreview(BaseModel):
    doc_name: str
    chunk_index: int
    content: str


class KnowledgeStatus(BaseModel):
    document_count: int
    chunk_count: int
    chunk_size: int
    chunk_overlap: int
    docs_path: str
    documents: list[DocumentInfo]


class ReloadKnowledgeRequest(BaseModel):
    chunk_size: int = Field(..., ge=50, le=10000, description="分块大小（字符）")
    chunk_overlap: int = Field(..., ge=0, description="分块重叠（字符）")

    @field_validator("chunk_overlap")
    @classmethod
    def overlap_less_than_size(cls, overlap: int, info):
        chunk_size = info.data.get("chunk_size")
        if chunk_size is not None and overlap >= chunk_size:
            raise ValueError("chunk_overlap 必须小于 chunk_size")
        return overlap
