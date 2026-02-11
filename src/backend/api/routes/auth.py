from fastapi import APIRouter, status, Depends

from src.backend.api.deps import get_auth_service, get_current_active_user
from src.backend.app.services.auth import AuthService
from src.shared.schemas import auth as auth_schema


auth_router = APIRouter(prefix="/api/v1.0/auth")


@auth_router.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
    response_model=auth_schema.UserRegisterResponse,
)
async def register(
    request: auth_schema.UserCreate,
    auth_service: AuthService = Depends(get_auth_service),  # 注入点
) -> auth_schema.UserRegisterResponse:
    return auth_service.register(request)


@auth_router.post(
    "/login", status_code=status.HTTP_200_OK, response_model=auth_schema.LoginResponse
)
async def login(
    request: auth_schema.LoginRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> auth_schema.LoginResponse:
    return auth_service.login(request)


@auth_router.get(
    "/me", status_code=status.HTTP_200_OK, response_model=auth_schema.UserInfo
)
async def read_user_me(
    # FastAPI 会自动执行 get_current_active_user
    # 如果 Token 无效，该函数内部抛出的 AuthError 会直接返回给前端，不会进入此函数体
    current_user: auth_schema.UserInfo = Depends(get_current_active_user),
):
    # 进入这里时，current_user 已经是校验过的对象了
    return current_user


@auth_router.post(
    "/logout", status_code=status.HTTP_200_OK, response_model=auth_schema.LogoutResponse
)
async def logout(
    auth_service: AuthService = Depends(get_auth_service),
) -> auth_schema.LogoutResponse:
    return auth_service.logout()


@auth_router.post(
    "/update", status_code=status.HTTP_200_OK, response_model=auth_schema.UserInfo
)
async def update_user(
    request: auth_schema.UserUpdate,
    current_user: auth_schema.UserInfo = Depends(get_current_active_user),
    auth_service: AuthService = Depends(get_auth_service),
) -> auth_schema.UserInfo:
    return auth_service.update_user(str(current_user.id), request.key, request.value)
