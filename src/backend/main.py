import uvicorn
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from src.backend.api.exception_handlers import register_exception_handlers
from src.backend.api.lifespan import lifespan
from src.backend.api.routes.chat import chat_router
from src.backend.api.routes.knowledge import knowledge_router
from src.shared.config import settings


def _register_routes(app: FastAPI) -> None:
    app.include_router(chat_router)
    app.include_router(knowledge_router)


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
    port: int = settings.backend_settings.backend_listen_port
    reload: bool = settings.backend_settings.reload

    uvicorn.run(
        app="src.backend.main:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info",
        access_log=True,
    )


if __name__ == "__main__":
    main()
