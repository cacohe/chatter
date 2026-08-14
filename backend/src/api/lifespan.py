"""应用生命周期（FastAPI lifespan）"""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from infra.logger import logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("=" * 60)
    logger.info("RAG 知识问答服务启动中...")
    logger.info("=" * 60)
    logger.info("知识库已就绪.")

    yield

    logger.info("应用正在关闭...")
