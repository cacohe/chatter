"""从环境变量组装配置；模块导入时完成初始化，供各层直接引用 settings。"""

import os
from pathlib import Path

from dotenv import load_dotenv
from pydantic import ConfigDict, Field
from pydantic_settings import BaseSettings


class _LLMSettings(BaseSettings):
    default_llm: str = Field(default="qwen3.7-max", description="默认模型名称")
    dashscope_api_key: str = Field(default="")
    max_history_messages: int = Field(
        default=10, description="输入给 LLM 的最大历史消息数量"
    )


class _RAGSettings(BaseSettings):
    top_k: int = Field(default=4, description="检索返回的分块数量")
    chunk_size: int = Field(default=500, description="文档分块大小")
    chunk_overlap: int = Field(default=50, description="分块重叠长度")
    qdrant_url: str = Field(
        default="",
        description="Qdrant Cloud 集群 URL；:memory: 仅用于单元测试",
    )
    qdrant_api_key: str = Field(default="", description="Qdrant Cloud API Key")
    qdrant_collection: str = Field(
        default="chatter", description="Qdrant collection 名"
    )
    embed_model: str = Field(
        default="qwen3.7-text-embedding",
        description="向量化模型",
    )
    embed_dim: int = Field(
        default=1536,
        description="向量维度，需与 Qdrant collection 一致",
    )


class _BackendSettings(BaseSettings):
    backend_listen_addr: str = Field(
        default="0.0.0.0",
        description="后端服务监听地址（0.0.0.0 表示监听所有网络接口）",
    )
    backend_listen_port: int = Field(default=8000, description="后端服务监听端口")
    reload: bool = Field(
        default=False, description="是否自动重载（生产环境应为 false）"
    )


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


def _env_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None or raw == "":
        return default
    return raw.lower() in {"1", "true", "yes", "on"}


def _init_settings():
    load_env()
    # 云平台常注入 PORT；本地则用 BACKEND_LISTEN_PORT / 默认 8000
    listen_port = int(os.getenv("PORT") or os.getenv("BACKEND_LISTEN_PORT") or "8000")
    return Settings(
        backend_settings=_BackendSettings(
            backend_listen_addr=os.getenv("BACKEND_LISTEN_ADDR") or "0.0.0.0",
            backend_listen_port=listen_port,
            reload=_env_bool("RELOAD", False),
        ),
        llm_settings=_LLMSettings(
            default_llm=os.getenv("DEFAULT_LLM") or "qwen3-max-2026-01-23",
            dashscope_api_key=os.getenv("DASHSCOPE_API_KEY", ""),
            max_history_messages=int(os.getenv("MAX_HISTORY_MESSAGES") or "10"),
        ),
        rag_settings=_RAGSettings(
            top_k=int(os.getenv("RAG_TOP_K") or "4"),
            chunk_size=int(os.getenv("RAG_CHUNK_SIZE") or "500"),
            chunk_overlap=int(os.getenv("RAG_CHUNK_OVERLAP") or "50"),
            qdrant_url=os.getenv("QDRANT_URL") or "",
            qdrant_api_key=os.getenv("QDRANT_API_KEY") or "",
            qdrant_collection=os.getenv("QDRANT_COLLECTION") or "chatter",
            embed_model=os.getenv("RAG_EMBED_MODEL") or "qwen3.7-text-embedding",
            embed_dim=int(os.getenv("RAG_EMBED_DIM") or "1536"),
        ),
        log_settings=_LogSettings(
            log_level=os.getenv("LOG_LEVEL") or "INFO",
            log_path=os.getenv("LOG_PATH") or "./logs",
        ),
    )


def load_env(env_path=None) -> None:
    """加载本地环境文件；已存在的环境变量优先（不覆盖）。

    查找顺序（显式路径除外）：
    1. backend/.env.local、backend/.env
    2. 仓库根目录 .env.local、.env
    """
    if env_path:
        path = Path(env_path)
        if path.exists():
            load_dotenv(dotenv_path=path, override=False)
        return

    backend_root = Path(__file__).resolve().parents[2]
    repo_root = backend_root.parent
    for base in (backend_root, repo_root):
        for name in (".env.local", ".env"):
            path = base / name
            if path.exists():
                load_dotenv(dotenv_path=path, override=False)
                return


settings = _init_settings()
