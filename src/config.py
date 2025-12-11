from pathlib import Path
from pydantic import BaseModel, Field
from dotenv import load_dotenv
import os


# 加载 .env 文件（如果存在）
env_path = Path(__file__).parent.parent.resolve() / ".env"
load_dotenv(dotenv_path=env_path, override=False)


class Settings(BaseModel):
    """应用配置类，使用 Pydantic 进行类型验证和自动转换"""
    
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
    
    class Config:
        """Pydantic 配置"""
        # 允许使用字段名或别名
        populate_by_name = True


# 从环境变量创建配置实例
_settings = Settings(
    backend_ip=os.getenv("BACKEND_IP", "localhost"),
    backend_host=os.getenv("BACKEND_HOST", "0.0.0.0"),
    backend_port=int(os.getenv("BACKEND_PORT", "8000"))
)

# 导出配置实例（供需要完整配置对象的地方使用）
settings = _settings
