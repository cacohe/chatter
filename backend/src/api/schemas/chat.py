"""聊天请求/响应模型：由后端按 session_id 持有。"""

from pydantic import BaseModel, ConfigDict, Field

from domain.models.chat import ChatMessage


class ChatRequest(BaseModel):
    """用户对话请求"""

    session_id: str = Field(..., min_length=1, max_length=128, description="会话 ID")
    content: str = Field(..., min_length=1, max_length=8000, description="用户问题")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "session_id": "11111111-1111-1111-1111-111111111111",
                "content": "公司年假政策是什么？",
            }
        }
    )


class StartNewChatRequest(BaseModel):
    session_id: str = Field(
        ..., min_length=1, max_length=128, description="当前会话 ID"
    )


class ChatHistoryResponse(BaseModel):
    """完整的对话历史消息。"""

    session_id: str
    messages: list[ChatMessage]
