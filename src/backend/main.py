import argparse
import sys

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.config import settings
from src.infra.log.logger import logger
from src.backend.database import init_db
from src.backend.routes import auth, session, chat


app = FastAPI(title="多模型AI聊天机器人")


# CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# 注册路由
app.include_router(auth.router)
app.include_router(session.router)
app.include_router(chat.router)


@app.on_event("startup")
async def startup_event():
    """应用启动事件"""
    logger.info("初始化数据库...")
    try:
        init_db()
        logger.info("数据库初始化成功")
    except Exception as e:
        logger.error(f"数据库初始化失败: {e}")
        # 不抛出异常，允许应用继续启动（数据库可能在其他容器中）


@app.get("/")
async def root():
    """根端点"""
    return {
        "message": "多模型AI聊天机器人 API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """健康检查端点"""
    return {"status": "healthy"}


def main(host: str = None, port: int = None, reload: bool = False):
    """
    启动后端服务
    
    Args:
        host: 监听地址，默认从配置读取
        port: 监听端口，默认从配置读取
        reload: 是否启用自动重载（开发模式）
    """
    host = host or settings.backend_host
    port = port or settings.backend_port
    
    logger.info(f"启动后端服务: {host}:{port}")
    logger.info(f"API文档地址: http://{host}:{port}/docs")
    
    uvicorn.run(
        "src.backend.main:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="启动多模型AI聊天机器人后端服务")
    parser.add_argument(
        "--host",
        type=str,
        default=None,
        help=f"监听地址（默认: {settings.backend_host}）"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=None,
        help=f"监听端口（默认: {settings.backend_port}）"
    )
    parser.add_argument(
        "--reload",
        action="store_true",
        help="启用自动重载（开发模式）"
    )
    
    args = parser.parse_args()
    
    try:
        main(host=args.host, port=args.port, reload=args.reload)
    except KeyboardInterrupt:
        logger.info("服务已停止")
        sys.exit(0)
    except Exception as e:
        logger.error(f"启动失败: {e}")
        sys.exit(1)
