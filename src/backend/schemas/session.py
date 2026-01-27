from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class SessionResponse(BaseModel):
    """会话响应模型"""
    id: int
    session_id: str
    user_id: int
    title: str
    model_name: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class MessageResponse(BaseModel):
    """消息响应模型"""
    id: int
    role: str
    content: str
    model_used: Optional[str] = None
    temperature: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class SessionDetail(SessionResponse):
    """会话详情响应模型（包含消息列表）"""
    messages: List[MessageResponse]
