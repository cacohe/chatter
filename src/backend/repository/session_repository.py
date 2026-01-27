from typing import Optional, List
from sqlalchemy.orm import Session

from src.backend.repository.base_repository import BaseRepository
from src.backend.models.session import ChatSession


class SessionRepository(BaseRepository[ChatSession]):
    """会话Repository"""

    def __init__(self, db: Session):
        super().__init__(ChatSession, db)

    def get_by_session_id(self, session_id: str) -> Optional[ChatSession]:
        """根据session_id获取会话"""
        return self.db.query(ChatSession).filter(ChatSession.session_id == session_id).first()

    def get_user_sessions(self, user_id: int, skip: int = 0, limit: int = 100) -> List[ChatSession]:
        """获取用户的所有会话"""
        return self.db.query(ChatSession).filter(
            ChatSession.user_id == user_id
        ).order_by(ChatSession.updated_at.desc()).offset(skip).limit(limit).all()

    def create_session(
        self,
        session_id: str,
        user_id: int,
        title: str = "新对话",
        system_prompt: str = None,
        model_name: str = "qwen"
    ) -> ChatSession:
        """创建新会话"""
        return self.create(
            session_id=session_id,
            user_id=user_id,
            title=title,
            system_prompt=system_prompt,
            model_name=model_name
        )

    def update_session(self, session_id: str, **kwargs) -> Optional[ChatSession]:
        """更新会话"""
        db_obj = self.get_by_session_id(session_id)
        if db_obj:
            for key, value in kwargs.items():
                if hasattr(db_obj, key):
                    setattr(db_obj, key, value)
            self.db.commit()
            self.db.refresh(db_obj)
        return db_obj

    def delete_session(self, session_id: str) -> bool:
        """删除会话"""
        db_obj = self.get_by_session_id(session_id)
        if db_obj:
            self.db.delete(db_obj)
            self.db.commit()
            return True
        return False
