from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime

from src.backend.models.user import Base


class ChatSession(Base):
    """会话表模型"""
    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(100), unique=True, index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(200), default="新对话")
    system_prompt = Column(Text, nullable=True)
    model_name = Column(String(50), default="qwen")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系：一个会话属于一个用户
    user = relationship("User", back_populates="sessions")
    # 关系：一个会话有多条消息
    messages = relationship("Message", back_populates="session", cascade="all, delete-orphan", order_by="Message.created_at")

    def __repr__(self):
        return f"<ChatSession(id={self.id}, session_id='{self.session_id}', title='{self.title}')>"
