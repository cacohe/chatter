"""应用生命周期（FastAPI lifespan）"""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.backend.infra.rag.loader import load_docs
from src.shared.logger import logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("=" * 60)
    logger.info("RAG 知识问答服务启动中...")
    logger.info("=" * 60)

    store = load_docs()
    logger.info(
        f"知识库就绪: {store.document_count} 个文档, {len(store.chunks)} 个分块"
    )

    yield

    logger.info("应用正在关闭...")
