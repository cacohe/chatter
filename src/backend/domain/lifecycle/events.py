"""
应用生命周期事件处理
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from src.shared.config import settings
from src.shared.logger import logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    应用生命周期管理

    启动时和关闭时执行的操作
    """
    # ========== 启动时执行 ==========
    logger.info("=" * 60)
    logger.info("应用启动中...")
    logger.info(f"环境: {'开发' if getattr(settings, 'debug', False) else '生产'}")
    logger.info(f"后端地址: {settings.backend_settings.backend_listen_addr}:{settings.backend_settings.backend_listen_port}")
    logger.info("=" * 60)

    # 这里可以添加启动时的初始化逻辑
    # 例如：数据库连接、缓存预热、加载模型等

    yield

    # ========== 关闭时执行 ==========
    logger.info("=" * 60)
    logger.info("应用正在关闭...")
    logger.info("=" * 60)

    # 这里可以添加关闭时的清理逻辑
    # 例如：关闭数据库连接、保存状态、释放资源等