from typing import Annotated
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from src.backend.database import get_db
from src.backend.security import decode_token
from src.backend.models.user import User
from src.backend.repository.user_repository import UserRepository

# OAuth2密码认证方案
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Session = Depends(get_db)
) -> User:
    """
    获取当前登录用户

    Args:
        token: JWT访问令牌
        db: 数据库会话

    Returns:
        当前用户对象

    Raises:
        HTTPException: 如果token无效或用户不存在
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无法验证凭据",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # 解码token
    payload = decode_token(token)
    if payload is None:
        raise credentials_exception

    # 获取用户ID
    user_id: int = payload.get("sub")
    if user_id is None:
        raise credentials_exception

    # 从数据库查询用户
    user_repo = UserRepository(db)
    user = user_repo.get_by_id(user_id)
    if user is None:
        raise credentials_exception

    return user


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)]
) -> User:
    """
    获取当前活跃用户

    Args:
        current_user: 当前用户对象

    Returns:
        活跃用户对象

    Raises:
        HTTPException: 如果用户未激活
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="用户账户未激活"
        )
    return current_user


# 导出便于使用的类型别名
CurrentUser = Annotated[User, Depends(get_current_user)]
CurrentActiveUser = Annotated[User, Depends(get_current_active_user)]
