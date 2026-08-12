import os

from pydantic import ConfigDict, Field
from pydantic_settings import BaseSettings

from src.shared.utils import load_env


class _LLMSettings(BaseSettings):
    default_llm: str = Field(default="qwen3-max-2026-01-23", description="默认模型名称")
    dashscope_api_key: str = Field(default="")
    max_history_messages: int = Field(
        default=10, description="最大历史消息数，用于控制上下文长度"
    )


class _RAGSettings(BaseSettings):
    docs_path: str = Field(default="./data/docs", description="知识库文档目录")
    top_k: int = Field(default=4, description="检索返回的分块数量")
    chunk_size: int = Field(default=500, description="文档分块大小（字符）")
    chunk_overlap: int = Field(default=50, description="分块重叠字符数")


class _BackendSettings(BaseSettings):
    backend_listen_addr: str = Field(
        default="0.0.0.0",
        description="后端服务监听地址（0.0.0.0 表示监听所有网络接口）",
    )
    backend_listen_port: int = Field(default=8000, description="后端服务监听端口")
    backend_api_url: str = Field(
        default="http://localhost:8000/api/v1.0", description="后端API URL"
    )
    reload: bool = Field(default=True, description="是否自动重载")


class _LogSettings(BaseSettings):
    log_level: str = Field(default="INFO")
    log_path: str = Field(default="./logs")


class Settings(BaseSettings):
    """应用配置类，使用 Pydantic 进行类型验证和自动转换"""

    llm_settings: _LLMSettings
    rag_settings: _RAGSettings
    backend_settings: _BackendSettings
    log_settings: _LogSettings

    model_config = ConfigDict(
        populate_by_name=True,
        extra="ignore",
    )


def _init_settings():
    load_env()
    return Settings(
        backend_settings=_BackendSettings(
            backend_listen_addr=os.getenv("BACKEND_LISTEN_ADDR") or "0.0.0.0",
            backend_listen_port=int(os.getenv("BACKEND_LISTEN_PORT") or "8000"),
            backend_api_url=os.getenv("BACKEND_API_URL")
            or "http://localhost:8000/api/v1.0",
            reload=(os.getenv("RELOAD") or "true").lower() == "true",
        ),
        llm_settings=_LLMSettings(
            default_llm=os.getenv("DEFAULT_LLM") or "qwen3-max-2026-01-23",
            dashscope_api_key=os.getenv("DASHSCOPE_API_KEY", ""),
            max_history_messages=int(os.getenv("MAX_HISTORY_MESSAGES") or "10"),
        ),
        rag_settings=_RAGSettings(
            docs_path=os.getenv("RAG_DOCS_PATH") or "./data/docs",
            top_k=int(os.getenv("RAG_TOP_K") or "4"),
            chunk_size=int(os.getenv("RAG_CHUNK_SIZE") or "500"),
            chunk_overlap=int(os.getenv("RAG_CHUNK_OVERLAP") or "50"),
        ),
        log_settings=_LogSettings(
            log_level=os.getenv("LOG_LEVEL") or "INFO",
            log_path=os.getenv("LOG_PATH") or "./logs",
        ),
    )


settings = _init_settings()
