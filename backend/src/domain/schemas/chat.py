"""对话请求模型：历史消息由前端持有，后端无会话存储。"""

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class ChatMessage(BaseModel):
    content: str = Field(..., min_length=1, max_length=8000, description="消息内容")
    role: MessageRole


class ChatRequest(BaseModel):
    """单次问答请求：当前问题 + 本轮对话历史（前端持有）"""

    content: str = Field(..., min_length=1, max_length=8000, description="用户问题")
    history: list[ChatMessage] | None = Field(
        default_factory=list, description="本轮对话内的历史消息"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "content": "公司年假政策是什么？",
                "history": [
                    {"role": "user", "content": "你好"},
                    {
                        "role": "assistant",
                        "content": "你好，我可以基于知识库回答问题。",
                    },
                ],
            }
        }
    )
