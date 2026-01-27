from typing import List
from sqlalchemy.orm import Session

from src.backend.repository.base_repository import BaseRepository
from src.backend.models.message import Message, MessageRole


class MessageRepository(BaseRepository[Message]):
    """消息Repository"""

    def __init__(self, db: Session):
        super().__init__(Message, db)

    def get_session_messages(
        self,
        session_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> List[Message]:
        """获取会话的所有消息"""
        return self.db.query(Message).filter(
            Message.session_id == session_id
        ).order_by(Message.created_at.asc()).offset(skip).limit(limit).all()

    def create_message(
        self,
        session_id: int,
        role: MessageRole,
        content: str,
        tool_calls: str = None,
        tool_result: str = None,
        model_used: str = None,
        temperature: str = None
    ) -> Message:
        """创建新消息"""
        return self.create(
            session_id=session_id,
            role=role,
            content=content,
            tool_calls=tool_calls,
            tool_result=tool_result,
            model_used=model_used,
            temperature=temperature
        )

    def delete_session_messages(self, session_id: int) -> int:
        """删除会话的所有消息"""
        count = self.db.query(Message).filter(Message.session_id == session_id).count()
        self.db.query(Message).filter(Message.session_id == session_id).delete()
        self.db.commit()
        return count
