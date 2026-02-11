from pydantic import BaseModel
from datetime import datetime
from enum import Enum


class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"

class Message(BaseModel):
    id: int
    session_id: int
    role: MessageRole
    content: str
    created_at: datetime

    @property
    def is_from_ai(self) -> bool:
        return self.role == MessageRole.ASSISTANT