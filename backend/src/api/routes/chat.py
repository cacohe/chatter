"""
聊天路由：

- 创建新对话
- 流式输出回答
- 获取对话历史
"""

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from api.deps import get_chat_history, get_start_new_chat, get_stream_chat
from api.schemas import chat as chat_schema
from app.services.chat.get_history import GetChatHistory
from app.services.chat.start_new_chat import StartNewChat
from app.services.chat.stream import StreamChat

chat_router = APIRouter(prefix="/api/v1.0/chat", tags=["chat"])


@chat_router.post("/new")
async def start_new_chat(
    request: chat_schema.StartNewChatRequest,
    usecase: StartNewChat = Depends(get_start_new_chat),
):
    """开启新聊天：清空当前会话的展示历史与 LLM 短期记忆。"""
    usecase.execute(request.session_id)
    return {"ok": True}


@chat_router.post("/stream")
async def chat_stream_endpoint(
    request: chat_schema.ChatRequest,
    usecase: StreamChat = Depends(get_stream_chat),
):
    """聊天流式响应；成功后分别写入展示历史与 LLM 短期记忆。"""

    async def generate():
        async for chunk in usecase.execute(request.session_id, request.content):
            yield f"data: {chunk}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


@chat_router.get("/messages", response_model=chat_schema.ChatHistoryResponse)
async def chat_messages(
    session_id: str,
    usecase: GetChatHistory = Depends(get_chat_history),
):
    """返回该会话的完整展示历史，不是 LLM 上下文窗口。"""
    return chat_schema.ChatHistoryResponse(
        session_id=session_id,
        messages=usecase.execute(session_id),
    )
