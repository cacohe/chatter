"""
知识库相关路由

- 从文件导入数据
- 从网页导入数据
- 从数据库导入数据
- 获取知识库摘要
- 获取文档分块列表
- 删除文档
"""

from fastapi import APIRouter, Depends, File, Form, UploadFile

from api.deps import (
    get_delete_document,
    get_ingest_web,
    get_knowledge_summary,
    get_list_chunks,
    get_sync_database,
    get_upload_files,
)
from api.schemas import knowledge as knowledge_schema
from app.services.knowledge.delete_document import DeleteDocument
from app.services.knowledge.get_summary import GetSummary
from app.services.knowledge.ingest_web import IngestWeb
from app.services.knowledge.list_chunks import ListChunks
from app.services.knowledge.sync_database import SyncDatabase
from app.services.knowledge.upload_files import UploadFiles

knowledge_router = APIRouter(prefix="/api/v1.0/knowledge", tags=["knowledge"])


@knowledge_router.post("/upload", response_model=knowledge_schema.KnowledgeSummary)
async def knowledge_upload(
    files: list[UploadFile] = File(...),
    chunk_size: int | None = Form(default=None),
    chunk_overlap: int | None = Form(default=None),
    usecase: UploadFiles = Depends(get_upload_files),
):
    """
    从文件导入知识库
    """
    payload: list[tuple[str, bytes]] = []
    for upload in files:
        content = await upload.read()
        payload.append((upload.filename or "upload.txt", content))
    return knowledge_schema.to_summary(
        usecase.execute(
            payload,
            chunk_size=chunk_size,
            overlap=chunk_overlap,
        )
    )


@knowledge_router.post("/ingest/web", response_model=knowledge_schema.KnowledgeSummary)
async def knowledge_ingest_web(
    request: knowledge_schema.IngestWebRequest,
    usecase: IngestWeb = Depends(get_ingest_web),
):
    """
    从网页加载知识库
    """
    return knowledge_schema.to_summary(
        usecase.execute(
            request.url,
            chunk_size=request.chunk_size,
            overlap=request.chunk_overlap,
        )
    )


@knowledge_router.post(
    "/sync/database", response_model=knowledge_schema.KnowledgeSummary
)
async def knowledge_sync_database(
    request: knowledge_schema.SyncDatabaseRequest,
    usecase: SyncDatabase = Depends(get_sync_database),
):
    """
    从数据库导入知识库
    """
    return knowledge_schema.to_summary(
        usecase.execute(
            request.uri,
            request.query,
            chunk_size=request.chunk_size,
            overlap=request.chunk_overlap,
        )
    )


@knowledge_router.get("/summary", response_model=knowledge_schema.KnowledgeSummary)
async def knowledge_summary(
    usecase: GetSummary = Depends(get_knowledge_summary),
):
    """
    获取知识库摘要
    """
    return knowledge_schema.to_summary(usecase.execute())


@knowledge_router.get("/chunks", response_model=list[knowledge_schema.ChunkPreview])
async def knowledge_chunks(
    doc_name: str | None = None,
    limit: int = 50,
    usecase: ListChunks = Depends(get_list_chunks),
):
    """
    获取文档分块列表
    """
    return [
        knowledge_schema.ChunkPreview(
            doc_name=str(item.metadata.get("doc_name") or ""),
            chunk_index=int(item.metadata.get("chunk_index") or 0),
            content=item.get_content(),
        )
        for item in usecase.execute(doc_name=doc_name, limit=limit)
    ]


@knowledge_router.delete("/documents", response_model=knowledge_schema.KnowledgeSummary)
async def knowledge_delete_document(
    doc_name: str,
    usecase: DeleteDocument = Depends(get_delete_document),
):
    """
    删除文档
    """
    return knowledge_schema.to_summary(usecase.execute(doc_name))
