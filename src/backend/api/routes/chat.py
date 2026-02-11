from fastapi import APIRouter, status, Depends
from fastapi.responses import StreamingResponse

from src.backend.api.deps import get_chat_service
from src.backend.app.services.chat import ChatService
from src.shared.schemas import chat as chat_schema


chat_router = APIRouter(prefix="/api/v1.0/chat")


@chat_router.post(
    "", status_code=status.HTTP_200_OK, response_model=chat_schema.ChatResponse
)
async def chat_endpoint(
    request: chat_schema.ChatRequest,
    chat_service: ChatService = Depends(get_chat_service),
) -> chat_schema.ChatResponse:
    return await chat_service.handle_chat(request)


@chat_router.post("/stream")
async def chat_stream_endpoint(
    request: chat_schema.ChatRequest,
    chat_service: ChatService = Depends(get_chat_service),
):
    async def generate():
        async for chunk in chat_service.handle_chat_stream(request):
            yield f"data: {chunk}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


@chat_router.get(
    "/history",
    status_code=status.HTTP_200_OK,
    response_model=chat_schema.HistoryResponse,
)
async def get_history(
    chat_service: ChatService = Depends(get_chat_service),
) -> chat_schema.HistoryResponse:
    return await chat_service.get_history()
