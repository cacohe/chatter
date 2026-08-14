"""前端配置：后端 API 地址。"""

import os

from pydantic import ConfigDict, Field
from pydantic_settings import BaseSettings

from utils import load_env


class Settings(BaseSettings):
    """应用配置类，使用 Pydantic 进行类型验证和自动转换"""

    backend_api_url: str = Field(
        default="http://localhost:8000/api/v1.0",
        description="后端 API 地址",
    )

    model_config = ConfigDict(
        populate_by_name=True,
        extra="ignore",
    )


def _init_settings():
    load_env()
    return Settings(
        backend_api_url=(
            os.getenv("BACKEND_API_URL") or "http://localhost:8000/api/v1.0"
        ).rstrip("/"),
    )


settings = _init_settings()
