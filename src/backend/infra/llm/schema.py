from pydantic import BaseModel, Field
from typing import Optional, Dict


class LLMParameters(BaseModel):
    """统一的推理参数"""
    temperature: float = Field(default=0.7, ge=0, le=2.0)
    top_p: float = Field(default=1.0)
    max_tokens: Optional[int] = Field(default=2048)
    stream: bool = Field(default=False)
    # 允许透传特定模型特有的参数
    extra_body: Dict = Field(default_factory=dict)


class ChatMessage(BaseModel):
    """统一的消息格式"""
    role: str
    content: str