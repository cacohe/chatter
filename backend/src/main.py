"""FastAPI 入口：组装应用、CORS 与 uvicorn 启动。"""

import os

import uvicorn
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from api.exception_handlers import register_exception_handlers
from api.lifespan import lifespan
from api.routes.chat import chat_router
from api.routes.knowledge import knowledge_router
from infra.config import settings


def _register_routes(app: FastAPI) -> None:
    app.include_router(chat_router)
    app.include_router(knowledge_router)

    @app.get("/health")
    async def health():
        """云平台探活，不依赖知识库是否已加载。"""
        return {"status": "ok"}


def _create_app() -> FastAPI:
    _app = FastAPI(
        title="RAG Knowledge Q&A",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )
    register_exception_handlers(_app)
    _register_routes(_app)
    return _app


app = _create_app()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def main():
    host: str = settings.backend_settings.backend_listen_addr
    port: int = int(os.getenv("PORT") or settings.backend_settings.backend_listen_port)
    reload: bool = settings.backend_settings.reload
    log_level = settings.log_settings.log_level.lower()

    uvicorn.run(
        app="main:app",
        host=host,
        port=port,
        reload=reload,
        log_level=log_level,
        access_log=True,
    )


if __name__ == "__main__":
    main()
