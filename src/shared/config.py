from pydantic import Field, ConfigDict
import os

from pydantic_settings import BaseSettings

from src.shared.utils import load_env


class _LLMSettings(BaseSettings):
    default_llm: str = Field(default="qwen3.5-plus", description="默认模型名称")
    dashscope_api_key: str = Field(default="")
    openai_api_key: str = Field(default="")
    gemini_api_key: str = Field(default="")
    deepseek_api_key: str = Field(default="")


class _DatabaseSettings(BaseSettings):
    database_url: str = Field(
        default="postgresql://chatter:chatter@localhost:5432/chatter",
        description="PostgreSQL数据库连接URL",
    )
    database_echo: bool = Field(
        default=False, description="是否输出SQL日志（开发环境可设为True）"
    )
    supabase_url: str = Field(default="")
    supabase_key: str = Field(default="")


class _BackendSettings(BaseSettings):
    backend_listen_addr: str = Field(
        default="0.0.0.0",
        description="后端服务监听地址（0.0.0.0 表示监听所有网络接口）",
    )
    backend_listen_port: int = Field(default=8000, description="后端服务监听端口")
    backend_api_url: str = Field(
        default=f"http://localhost:8000/api/v1.0", description="后端API URL"
    )
    reload: bool = Field(default=True, description="是否自动重载")


class _JWTSettings(BaseSettings):
    jwt_secret_key: str = Field(
        default="your-secret-key-change-this-in-production",
        description="JWT密钥（生产环境请修改）",
    )
    jwt_algorithm: str = Field(default="HS256", description="JWT加密算法")
    jwt_access_token_expire_minutes: int = Field(
        default=30, description="访问令牌过期时间（分钟）"
    )
    jwt_refresh_token_expire_days: int = Field(
        default=7, description="刷新令牌过期时间（天）"
    )


class _LogSettings(BaseSettings):
    log_level: str = Field(default="INFO")
    log_path: str = Field(default="./logs")


class Settings(BaseSettings):
    """应用配置类，使用 Pydantic 进行类型验证和自动转换"""

    llm_settings: _LLMSettings
    database_settings: _DatabaseSettings
    backend_settings: _BackendSettings
    jwt_settings: _JWTSettings
    log_settings: _LogSettings

    model_config = ConfigDict(
        # 允许使用字段名或别名
        populate_by_name=True,
        extra="ignore",
    )


def _init_settings():
    load_env()
    # 从环境变量创建配置实例
    _settings = Settings(
        backend_settings=_BackendSettings(
            backend_listen_addr=os.getenv("BACKEND_LISTEN_ADDR", ""),
            backend_listen_port=int(os.getenv("BACKEND_LISTEN_PORT", "8000")),
            backend_api_url=os.getenv("BACKEND_API_URL", ""),
        ),
        llm_settings=_LLMSettings(
            default_llm=os.getenv("DEFAULT_LLM", ""),
            dashscope_api_key=os.getenv("DASHSCOPE_API_KEY", ""),
            openai_api_key=os.getenv("OPENAI_API_KEY", ""),
            gemini_api_key=os.getenv("GOOGLE_API_KEY", ""),
            deepseek_api_key=os.getenv("DEEPSEEK_API_KEY", ""),
        ),
        database_settings=_DatabaseSettings(
            database_url=os.getenv("DATABASE_URL", ""),
            database_echo=os.getenv("DATABASE_ECHO", "").lower() == "true",
            supabase_url=os.getenv("SUPABASE_URL", ""),
            supabase_key=os.getenv("SUPABASE_KEY", ""),
        ),
        jwt_settings=_JWTSettings(
            jwt_secret_key=os.getenv("JWT_SECRET_KEY", ""),
            jwt_algorithm=os.getenv("JWT_ALGORITHM", ""),
            jwt_access_token_expire_minutes=int(
                os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "15")
            ),
            jwt_refresh_token_expire_days=int(
                os.getenv("JWT_REFRESH_TOKEN_EXPIRE_DAYS", "7")
            ),
        ),
        log_settings=_LogSettings(
            log_level=os.getenv("LOG_LEVEL", ""),
            log_path=os.getenv("LOG_PATH", ""),
        ),
    )
    return _settings


# 导出配置实例（供需要完整配置对象的地方使用）
settings = _init_settings()
