"""对话消息：展示历史与 LLM 短期记忆共用。"""

from enum import Enum

from pydantic import BaseModel


class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class ChatMessage(BaseModel):
    content: str
    role: MessageRole
