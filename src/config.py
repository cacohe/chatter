from pydantic import BaseModel, Field
import os


class Settings(BaseModel):
    """应用配置类，使用 Pydantic 进行类型验证和自动转换"""

    # 后端服务配置
    backend_ip: str = Field(
        default="localhost",
        description="后端服务IP地址（前端连接使用）"
    )

    backend_host: str = Field(
        default="0.0.0.0",
        description="后端服务监听地址（0.0.0.0 表示监听所有网络接口）"
    )

    backend_port: int = Field(
        default=8000,
        description="后端服务端口",
        ge=1,  # 最小值为1
        le=65535  # 最大值为65535
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


# 从环境变量创建配置实例
_settings = Settings(
    backend_ip=os.getenv("BACKEND_IP", "localhost"),
    backend_host=os.getenv("BACKEND_HOST", "0.0.0.0"),
    backend_port=int(os.getenv("BACKEND_PORT", "8000")),
    database_url=os.getenv("DATABASE_URL", "postgresql://chatter:chatter@localhost:5432/chatter"),
    database_echo=os.getenv("DATABASE_ECHO", "false").lower() == "true",
    jwt_secret_key=os.getenv("JWT_SECRET_KEY", "your-secret-key-change-this-in-production"),
    jwt_algorithm=os.getenv("JWT_ALGORITHM", "HS256"),
    jwt_access_token_expire_minutes=int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "30")),
    jwt_refresh_token_expire_days=int(os.getenv("JWT_REFRESH_TOKEN_EXPIRE_DAYS", "7"))
)

# 导出配置实例（供需要完整配置对象的地方使用）
settings = _settings
