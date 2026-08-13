"""应用生命周期（FastAPI lifespan）"""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from infra.logger import logger
from infra.rag.loader import load_docs


@asynccontextmanager
async def lifespan(app: FastAPI):
    """启动时从磁盘种子目录加载知识库；关闭时仅打日志（知识在内存中，无需持久化）。"""
    logger.info("=" * 60)
    logger.info("RAG 知识问答服务启动中...")
    logger.info("=" * 60)

    store = load_docs()
    logger.info(f"知识库就绪: {store.document_count} 个文档, {len(store.nodes)} 个分块")

    yield

    logger.info("应用正在关闭...")
