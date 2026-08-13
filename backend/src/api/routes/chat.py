"""对话路由：SSE 流式返回模型输出。"""

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from api.deps import get_stream_chat
from app.services.chat.stream import StreamChat
from domain.schemas import chat as chat_schema

chat_router = APIRouter(prefix="/api/v1.0/chat", tags=["chat"])


@chat_router.post("/stream")
async def chat_stream_endpoint(
    request: chat_schema.ChatRequest,
    usecase: StreamChat = Depends(get_stream_chat),
):
    """
    聊天流式响应
    """

    async def generate():
        # SSE 帧：前端按 "data: " 前缀拆 token
        async for chunk in usecase.execute(request):
            yield f"data: {chunk}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")
