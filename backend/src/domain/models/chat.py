"""对话消息：展示历史与 LLM 短期记忆共用。"""

from enum import Enum

from pydantic import BaseModel, Field


class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class ChatMessage(BaseModel):
    content: str
    role: MessageRole
    citations: list["Citation"] = Field(default_factory=list)


class Citation(BaseModel):
    """回答引用到的证据片段。"""

    index: int
    doc_name: str
    chunk_index: int
    snippet: str
    source_uri: str = ""
    score: float | None = None
    # 是否被回答正文中的 [n] 实际引用；None 表示未经校验。
    used: bool | None = None
