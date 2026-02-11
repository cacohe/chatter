import datetime
import enum

from sqlalchemy.orm import relationship
from sqlalchemy.orm.decl_api import declarative_base
from sqlalchemy.sql.schema import Column, ForeignKey
from sqlalchemy.sql.sqltypes import TEXT, DateTime, Enum, String, Integer


Base = declarative_base()


class MessageRole(str, enum.Enum):
    """消息角色枚举"""
    USER = "user"
    ASSISTANT = "assistant"


class User(Base):
    """用户表模型"""
    __tablename__ = "user"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系：一个用户有多个会话
    sessions = relationship("Session", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', email='{self.email}')>"


class Message(Base):
    __tablename__ = "message"
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey('session.id'), index=True)
    role = Column(Enum(MessageRole), index=True)
    content = Column(TEXT)
    created_at = Column(DateTime, index=True, default=datetime.datetime.now(tz=datetime.timezone.utc))

    # 关系：一条消息属于一个会话
    session = relationship("Session", back_populates="messages")

    def __repr__(self):
        return f"<Message(id={self.id}, role='{self.role}', content='{self.content[:50]}...')>"


class Session(Base):
    """会话表模型"""
    __tablename__ = "chat_session"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    title = Column(String(200), default="新对话")
    model_name = Column(String(50), default="qwen")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系：一个会话属于一个用户
    user = relationship("User", back_populates="session")
    # 关系：一个会话有多条消息
    messages = relationship("Message", back_populates="session", cascade="all, delete-orphan", order_by="Message.created_at")

    def __repr__(self):
        return f"<ChatSession(id={self.id}, session_id='{self.session_id}', title='{self.title}')>"