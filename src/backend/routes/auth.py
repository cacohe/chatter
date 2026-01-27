from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Annotated

from src.backend.database import get_db
from src.backend.controller.auth_controller import AuthController
from src.backend.schemas.auth import UserCreate, UserLogin, Token, TokenRefresh
from src.backend.models.user import User
from src.backend.dependencies import CurrentActiveUser

router = APIRouter(prefix="/auth", tags=["认证"])


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    """用户注册"""
    auth_controller = AuthController(db)
    return auth_controller.register(user_data)


@router.post("/login", response_model=Token)
async def login(
    login_data: UserLogin,
    db: Session = Depends(get_db)
):
    """用户登录"""
    auth_controller = AuthController(db)
    return auth_controller.login(login_data)


@router.post("/refresh")
async def refresh_token(
    token_data: TokenRefresh,
    db: Session = Depends(get_db)
):
    """刷新访问令牌"""
    auth_controller = AuthController(db)
    return auth_controller.refresh_token(token_data.refresh_token)


@router.get("/me", response_model=User)
async def get_current_user_info(
    current_user: Annotated[User, Depends(get_current_user)]
):
    """获取当前用户信息"""
    return current_user
