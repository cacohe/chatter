from src.backend.domain.exceptions import AuthError
from src.backend.domain.repository_interfaces.auth import IAuthRepository
from src.shared.schemas import auth as auth_schemas
from src.shared.logger import logger


class AuthService:
    def __init__(self, auth_repo: IAuthRepository):
        self.auth_repo = auth_repo

    def register(
        self, request: auth_schemas.UserCreate
    ) -> auth_schemas.UserRegisterResponse:
        try:
            user_data = self.auth_repo.create_user(
                email=request.email,
                password=request.password,
                username=request.username,
            )
            return auth_schemas.UserRegisterResponse(**user_data)

        except AuthError:
            raise
        except Exception as e:
            logger.exception(f"Failed to register user: {request.email}, Error: {e}")
            raise AuthError(message="注册失败，请稍后重试")

    def login(self, request: auth_schemas.LoginRequest) -> auth_schemas.LoginResponse:
        try:
            auth_res = self.auth_repo.authenticate(
                email=request.email, password=request.password
            )
            session = auth_res.session
            auth_user = auth_res.user

            if not session or not auth_user:
                logger.error(f"Failed to login user, Error: {session}")
                raise AuthError(f"登录失败，邮箱或密码错误")

            return auth_schemas.LoginResponse(
                access_token=auth_res.session.access_token,
                refresh_token=auth_res.session.refresh_token,
                user_info=auth_schemas.UserInfo(
                    id=auth_res.user.id,
                    username=getattr(auth_res.user, "username", "fake_username"),
                    email=auth_res.user.email,
                ),
            )
        except AuthError:
            raise
        except Exception as e:
            logger.exception(f"Failed to login user: {request.email}, Error: {e}")
            raise AuthError(message="登录失败，请稍后重试")

    def get_current_user(self, token: str) -> auth_schemas.UserInfo:
        try:
            # 3. 仓库负责从 Token 解析用户并关联数据库记录
            user_data = self.auth_repo.get_user_by_token(token)
            if not user_data:
                raise AuthError(message="用户不存在")
            return auth_schemas.UserInfo(**user_data)
        except Exception:
            logger.exception(f"Failed to get user by token")
            raise AuthError(message="无效的会话或 Token 已过期")

    def logout(self) -> auth_schemas.LogoutResponse:
        # 4. 仓库执行清理逻辑
        try:
            self.auth_repo.sign_out()
            return auth_schemas.LogoutResponse(message="已安全退出登录")
        except Exception as e:
            logger.exception(f"Failed to logout user, Error: {e}")
            raise AuthError(message=str(e) or "用户退出登录失败")

    def update_user(self, user_id: str, key: str, value: str) -> auth_schemas.UserInfo:
        try:
            user_data = self.auth_repo.update_user(user_id, key, value)
            if not user_data:
                raise AuthError(message="更新用户信息失败")
            return auth_schemas.UserInfo(**user_data)
        except AuthError:
            raise
        except Exception as e:
            logger.exception(f"Failed to update user, Error: {e}")
            raise AuthError(message=f"更新用户信息失败: {str(e)}")
