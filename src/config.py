from pydantic import Field
import os

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """应用配置类，使用 Pydantic 进行类型验证和自动转换"""

    # 后端服务配置
    backend_listen_addr: str = Field(
        default="0.0.0.0",
        description="后端服务监听地址（0.0.0.0 表示监听所有网络接口）"
    )
    backend_listen_port: int = Field(
        default=8000,
        description="后端服务监听端口"
    )
    backend_api_url: str = Field(
        default=f"http://localhost:8000",
        description="后端API URL"
    )

    # 默认调用的大模型
    default_llm: str = Field(
        default=os.getenv("DEFAULT_LLM", "qwen"),
        description="默认模型名称"
    )

    # 数据库配置
    database_url: str = Field(
        default="postgresql://chatter:chatter@localhost:5432/chatter",
        description="PostgreSQL数据库连接URL"
    )
    database_echo: bool = Field(
        default=False,
        description="是否输出SQL日志（开发环境可设为True）"
    )

    # JWT认证配置
    jwt_secret_key: str = Field(
        default="your-secret-key-change-this-in-production",
        description="JWT密钥（生产环境请修改）"
    )
    jwt_algorithm: str = Field(
        default="HS256",
        description="JWT加密算法"
    )
    jwt_access_token_expire_minutes: int = Field(
        default=30,
        description="访问令牌过期时间（分钟）"
    )
    jwt_refresh_token_expire_days: int = Field(
        default=7,
        description="刷新令牌过期时间（天）"
    )

    class Config:
        """Pydantic 配置"""
        # 允许使用字段名或别名
        populate_by_name = True
        env_file = ".env.local"
        extra = "ignore"


# 从环境变量创建配置实例
_settings = Settings(
    backend_listen_addr=os.getenv("BACKEND_LISTEN_ADDR", "0.0.0.0"),
    backend_listen_port=int(os.getenv("BACKEND_LISTEN_PORT", "8000")),
    backend_api_url=os.getenv("BACKEND_API_URL", "http://localhost:8000"),
    database_url=os.getenv("DATABASE_URL", "postgresql://chatter:chatter@localhost:5432/chatter"),
    database_echo=os.getenv("DATABASE_ECHO", "false").lower() == "true",
    jwt_secret_key=os.getenv("JWT_SECRET_KEY", "your-secret-key-change-this-in-production"),
    jwt_algorithm=os.getenv("JWT_ALGORITHM", "HS256"),
    jwt_access_token_expire_minutes=int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "30")),
    jwt_refresh_token_expire_days=int(os.getenv("JWT_REFRESH_TOKEN_EXPIRE_DAYS", "7"))
)

# 导出配置实例（供需要完整配置对象的地方使用）
settings = _settings
