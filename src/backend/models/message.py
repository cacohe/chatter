from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from src.backend.models.user import Base


class MessageRole(str, enum.Enum):
    """消息角色枚举"""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


class Message(Base):
    """消息表模型"""
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("sessions.id"), nullable=False)
    role = Column(SQLEnum(MessageRole), nullable=False)
    content = Column(Text, nullable=False)
    tool_calls = Column(Text, nullable=True)  # JSON字符串存储工具调用信息
    tool_result = Column(Text, nullable=True)  # 工具执行结果
    model_used = Column(String(50), nullable=True)
    temperature = Column(String(10), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # 关系：一条消息属于一个会话
    session = relationship("ChatSession", back_populates="messages")

    def __repr__(self):
        return f"<Message(id={self.id}, role='{self.role}', content='{self.content[:50]}...')>"
