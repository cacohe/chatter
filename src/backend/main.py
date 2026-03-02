import uvicorn
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from src.shared.config import settings
from src.backend.api.routes.auth import auth_router
from src.backend.api.routes.chat import chat_router
from src.backend.api.routes.llm import llm_router
from src.backend.api.routes.session import session_router
from src.backend.domain.lifecycle.events import lifespan
from src.backend.domain.middleware.error_handler import register_exception_handlers
from src.backend.infra.db.supabase.client import init_supabase


def _register_routes(app: FastAPI) -> None:
    app.include_router(auth_router)
    app.include_router(chat_router)
    app.include_router(llm_router)
    app.include_router(session_router)


def _create_app() -> FastAPI:
    _app = FastAPI(
        title="Caco AI Chat Backend",
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
    allow_origins=["*"], # 生产环境建议填具体的 streamlit 域名
    allow_methods=["*"],
    allow_headers=["*"],
)


def main():
    host: str = settings.backend_settings.backend_listen_addr
    port: int = settings.backend_settings.backend_listen_port
    reload: bool = settings.backend_settings.reload

    uvicorn.run(
        app='main:app', host=host, port=port, reload=reload, log_level="info", access_log=True
    )


if __name__ == "__main__":
    init_supabase()
    main()
