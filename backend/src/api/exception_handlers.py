"""HTTP 异常到响应的映射（交付层，非领域逻辑）"""

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from domain.exceptions import BusinessException
from infra.logger import logger


def register_exception_handlers(app: FastAPI) -> None:
    """把领域异常转成统一 JSON，避免未捕获异常把栈信息暴露给前端。"""

    @app.exception_handler(BusinessException)
    async def business_exception_handler(request: Request, exc: BusinessException):
        logger.warning(f"业务异常 [path={request.url.path}]: {exc.message}")
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.message, "path": str(request.url.path)},
        )

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.error(f"未处理的异常 [path={request.url.path}]: {exc}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "detail": "服务器内部错误，请稍后重试",
                "path": str(request.url.path),
            },
        )

    @app.exception_handler(ValueError)
    async def value_error_handler(request: Request, exc: ValueError):
        logger.warning(f"参数错误 [path={request.url.path}]: {exc}")
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"detail": str(exc), "path": str(request.url.path)},
        )
