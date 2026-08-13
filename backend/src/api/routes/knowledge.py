"""知识库路由：每个接口对应一个用例，不在此层处理分块/检索细节。"""

from fastapi import APIRouter, Depends, File, Form, UploadFile

from api.deps import (
    get_delete_document,
    get_ingest_web,
    get_knowledge_summary,
    get_list_chunks,
    get_reload_knowledge,
    get_sync_database,
    get_upload_files,
)
from app.services.knowledge.delete_document import DeleteDocument
from app.services.knowledge.get_summary import GetSummary
from app.services.knowledge.ingest_web import IngestWeb
from app.services.knowledge.list_chunks import ListChunks
from app.services.knowledge.reload import ReloadKnowledge
from app.services.knowledge.sync_database import SyncDatabase
from app.services.knowledge.upload_files import UploadFiles
from domain.schemas import knowledge as knowledge_schema

knowledge_router = APIRouter(prefix="/api/v1.0/knowledge", tags=["knowledge"])


@knowledge_router.get("/summary", response_model=knowledge_schema.KnowledgeSummary)
async def knowledge_summary(
    usecase: GetSummary = Depends(get_knowledge_summary),
):
    """
    获取知识库摘要
    """
    return usecase.execute()


@knowledge_router.post("/reload", response_model=knowledge_schema.KnowledgeSummary)
async def knowledge_reload(
    request: knowledge_schema.ReloadKnowledgeRequest,
    usecase: ReloadKnowledge = Depends(get_reload_knowledge),
):
    """
    按新参数重新分块
    """
    return usecase.execute(request)


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
    return usecase.execute(
        payload,
        chunk_size=chunk_size,
        overlap=chunk_overlap,
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
    return usecase.execute(request)


@knowledge_router.post("/ingest/web", response_model=knowledge_schema.KnowledgeSummary)
async def knowledge_ingest_web(
    request: knowledge_schema.IngestWebRequest,
    usecase: IngestWeb = Depends(get_ingest_web),
):
    """
    从网页加载知识库
    """
    return usecase.execute(request)


@knowledge_router.delete("/documents", response_model=knowledge_schema.KnowledgeSummary)
async def knowledge_delete_document(
    doc_name: str,
    usecase: DeleteDocument = Depends(get_delete_document),
):
    """
    删除文档
    """
    return usecase.execute(doc_name)


@knowledge_router.get("/chunks", response_model=list[knowledge_schema.ChunkPreview])
async def knowledge_chunks(
    doc_name: str | None = None,
    limit: int = 50,
    usecase: ListChunks = Depends(get_list_chunks),
):
    """
    获取文档分块列表
    """
    return usecase.execute(doc_name=doc_name, limit=limit)
