from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from src.backend.security import verify_password, get_password_hash, create_access_token, create_refresh_token
from src.backend.repository.user_repository import UserRepository
from src.backend.schemas.auth import UserCreate, UserLogin, Token, UserResponse


class AuthController:
    """认证控制器"""

    def __init__(self, db: Session):
        self.db = db
        self.user_repo = UserRepository(db)

    def register(self, user_data: UserCreate) -> Token:
        """
        用户注册

        Args:
            user_data: 用户注册信息

        Returns:
            Token对象，包含访问令牌和刷新令牌

        Raises:
            HTTPException: 如果用户名或邮箱已存在
        """
        # 检查用户名是否已存在
        if self.user_repo.get_by_username(user_data.username):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="用户名已被使用"
            )

        # 检查邮箱是否已存在
        if self.user_repo.get_by_email(user_data.email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="邮箱已被注册"
            )

        # 创建用户
        hashed_password = get_password_hash(user_data.password)
        user = self.user_repo.create_user(
            username=user_data.username,
            email=user_data.email,
            hashed_password=hashed_password,
            full_name=user_data.full_name
        )

        # 生成token
        access_token = create_access_token(data={"sub": user.id})
        refresh_token = create_refresh_token(data={"sub": user.id})

        # 返回token和用户信息
        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
            user=UserResponse.model_validate(user)
        )

    def login(self, login_data: UserLogin) -> Token:
        """
        用户登录

        Args:
            login_data: 用户登录信息

        Returns:
            Token对象，包含访问令牌和刷新令牌

        Raises:
            HTTPException: 如果用户名或密码错误
        """
        # 查找用户
        user = self.user_repo.get_by_username(login_data.username)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户名或密码错误"
            )

        # 验证密码
        if not verify_password(login_data.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户名或密码错误"
            )

        # 检查用户是否激活
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="用户账户已被禁用"
            )

        # 生成token
        access_token = create_access_token(data={"sub": user.id})
        refresh_token = create_refresh_token(data={"sub": user.id})

        # 返回token和用户信息
        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
            user=UserResponse.model_validate(user)
        )

    def refresh_token(self, refresh_token: str) -> dict:
        """
        刷新访问令牌

        Args:
            refresh_token: 刷新令牌

        Returns:
            新的访问令牌

        Raises:
            HTTPException: 如果刷新令牌无效
        """
        from src.backend.security import decode_token

        # 解码刷新令牌
        payload = decode_token(refresh_token)
        if payload is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效的刷新令牌"
            )

        # 检查是否是刷新令牌
        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效的令牌类型"
            )

        # 获取用户ID
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效的令牌"
            )

        # 验证用户是否存在
        user = self.user_repo.get_by_id(user_id)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户不存在"
            )

        # 生成新的访问令牌
        access_token = create_access_token(data={"sub": user.id})

        return {"access_token": access_token}
