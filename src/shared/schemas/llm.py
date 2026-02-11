import uuid
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict


class ModelProvider(str, Enum):
    OPENAI = "OpenAI"
    ANTHROPIC = "Anthropic"
    GOOGLE = "Google"
    DEEPSEEK = "DeepSeek"
    LOCAL = "Local"


class LLMInfo(BaseModel):
    """单个模型的详细元数据"""
    id: str = Field(..., description="模型唯一标识符，如 'gpt-4o' 或 'deepseek-chat'")
    name: str = Field(..., description="展示给用户的名称，如 'GPT-4 Omni'")
    provider: ModelProvider = Field(..., description="模型供应商")
    context_window: int = Field(default=10, description="最大上下文 Token 限制")
    description: Optional[str] = Field(None, description="模型功能简述")
    is_active: bool = Field(False, description="当前会话是否正使用此模型")
    capabilities: List[str] = Field(default_factory=list, description="能力标签，如 ['vision', 'tools']")

    model_config = ConfigDict(from_attributes=True)


class LLMListResponse(BaseModel):
    """可用模型列表响应"""
    models: List[LLMInfo]
    current_model_id: str = Field(..., description="当前默认或选中的模型 ID")


class ModelSwitchRequest(BaseModel):
    """切换模型的请求"""
    session_id: uuid.UUID = Field(..., description="需要修改的会话 ID")
    model_id: str = Field(..., description="目标模型标识符")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "session_id": 1024,
                "model_id": "deepseek-reasoner"
            }
        }
    )

class ModelSwitchResponse(BaseModel):
    """切换结果响应"""
    success: bool = True
    session_id: uuid.UUID
    active_model_id: str
    message: str = "模型切换成功"