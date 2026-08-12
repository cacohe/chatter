from fastapi import APIRouter, Depends, File, Form, UploadFile

from src.backend.api.deps import get_knowledge_service
from src.backend.app.services.knowledge import KnowledgeService
from src.shared.schemas import knowledge as knowledge_schema

knowledge_router = APIRouter(prefix="/api/v1.0/knowledge", tags=["knowledge"])


@knowledge_router.get("/status", response_model=knowledge_schema.KnowledgeStatus)
async def knowledge_status(
    knowledge_service: KnowledgeService = Depends(get_knowledge_service),
):
    return knowledge_service.get_status()


@knowledge_router.post("/reload", response_model=knowledge_schema.KnowledgeStatus)
async def knowledge_reload(
    request: knowledge_schema.ReloadKnowledgeRequest,
    knowledge_service: KnowledgeService = Depends(get_knowledge_service),
):
    return knowledge_service.reload(request)


@knowledge_router.post("/upload", response_model=knowledge_schema.KnowledgeStatus)
async def knowledge_upload(
    files: list[UploadFile] = File(...),
    chunk_size: int | None = Form(default=None),
    chunk_overlap: int | None = Form(default=None),
    knowledge_service: KnowledgeService = Depends(get_knowledge_service),
):
    payload: list[tuple[str, bytes]] = []
    for upload in files:
        content = await upload.read()
        payload.append((upload.filename or "upload.txt", content))
    return knowledge_service.upload_files(
        payload,
        chunk_size=chunk_size,
        overlap=chunk_overlap,
    )


@knowledge_router.get("/chunks", response_model=list[knowledge_schema.ChunkPreview])
async def knowledge_chunks(
    doc_name: str | None = None,
    limit: int = 50,
    knowledge_service: KnowledgeService = Depends(get_knowledge_service),
):
    return knowledge_service.list_chunks(doc_name=doc_name, limit=limit)
