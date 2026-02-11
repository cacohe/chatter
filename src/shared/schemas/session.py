import uuid
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


# --- 请求模型 ---

class SessionCreateRequest(BaseModel):
    """创建会话请求"""
    initial_title: str = Field(default="新对话", min_length=1, max_length=50)
    model_id: str = Field(default="qwen", description="初始选用的模型 ID")

class SessionRenameRequest(BaseModel):
    """重命名会话请求"""
    session_id: uuid.UUID
    new_title: str = Field(..., min_length=1, max_length=100)


class SessionDeleteRequest(BaseModel):
    session_id: uuid.UUID


# --- 响应模型 ---

class SessionRead(BaseModel):
    """单条会话的读取模型"""
    id: uuid.UUID
    title: str = '新对话'
    model_name: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class SessionListResponse(BaseModel):
    """会话列表响应"""
    sessions: List[SessionRead]
    total_count: int