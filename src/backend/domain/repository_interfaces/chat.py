import uuid
from abc import ABC, abstractmethod
from typing import List, Tuple, Optional


class IChatRepository(ABC):
    @abstractmethod
    async def save_message(self, session_id: uuid.UUID, role: str, content: str):
        """保存单条消息"""
        pass

    @abstractmethod
    async def get_recent_messages(self, session_id: uuid.UUID, limit: int = 10):
        """获取最近几条消息用于 AI 上下文"""
        pass

    @abstractmethod
    async def get_paged_messages(
        self, session_id: uuid.UUID, last_id: Optional[int], limit: int
    ) -> Tuple[List, bool]:
        """分页获取消息，返回 (消息列表, 是否还有更多)"""
        pass

    @abstractmethod
    async def get_message_count(self, session_id: uuid.UUID) -> int:
        """获取会话的消息数量"""
        pass
