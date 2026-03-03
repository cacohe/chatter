import uuid
from enum import Enum
from typing import List, Optional
from datetime import datetime, timezone
from pydantic import BaseModel, Field, ConfigDict


class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"  # 预留给系统提示词


class ChatMessage(BaseModel):
    session_id: uuid.UUID = Field(..., description="所属会话的 ID")
    content: str = Field(..., min_length=1, max_length=4000, description="消息内容")
    role: MessageRole


class ChatRequest(BaseModel):
    """用户发送消息的请求模型"""

    session_id: uuid.UUID = Field(..., description="所属会话的 ID")
    content: str = Field(..., min_length=1, max_length=4000, description="消息内容")
    model_id: Optional[str] = None
    history: Optional[List[ChatMessage]] = Field(
        default_factory=list, description="历史消息列表，用于实现上下文记忆"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "session_id": 1024,
                "content": "你好，请帮我写一个 Python 脚本。",
                "model_id": "qwen",
                "history": [
                    {"session_id": 1024, "role": "user", "content": "你好"},
                    {
                        "session_id": 1024,
                        "role": "assistant",
                        "content": "你好！有什么可以帮你的吗？",
                    },
                ],
            }
        }
    )


class ChatResponse(BaseModel):
    """发送成功后即时返回的消息简报"""

    id: uuid.UUID
    session_id: uuid.UUID
    role: MessageRole
    content: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MessageRead(BaseModel):
    """单条消息的读取模型"""

    id: uuid.UUID
    role: MessageRole
    content: str
    created_at: datetime = datetime.now(timezone.utc)

    model_config = ConfigDict(from_attributes=True)


class HistoryResponse(BaseModel):
    """历史消息列表的响应模型"""

    items: List[MessageRead] = Field(..., description="消息列表")
    has_more: bool = Field(..., description="是否还有更多历史记录")
    last_message_id: Optional[int] = Field(
        None, description="用于下一次分页请求的游标 ID"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "items": [
                    {
                        "id": 1,
                        "role": "user",
                        "content": "Hi",
                        "created_at": "2024-01-01T12:00:00Z",
                    },
                    {
                        "id": 2,
                        "role": "assistant",
                        "content": "Hello!",
                        "created_at": "2024-01-01T12:00:01Z",
                    },
                ],
                "has_more": True,
                "last_message_id": 1,
            }
        }
    )
