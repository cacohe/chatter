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
    # 优先使用云平台注入的 PORT
    port: int = int(os.getenv("PORT") or settings.backend_settings.backend_listen_port)
    reload: bool = settings.backend_settings.reload

    uvicorn.run(
        app="main:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info",
        access_log=True,
    )


if __name__ == "__main__":
    main()
