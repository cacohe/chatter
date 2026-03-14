from src.backend.domain.repository_interfaces.auth import IAuthRepository
from src.backend.infra.db.supabase.client import create_supabase
from src.backend.domain.exceptions import AuthError
from supabase.lib.client_options import ClientOptions
import httpx


class SupabaseAuthRepository(IAuthRepository):
    def __init__(self, db_client=None):
        self.db_client = db_client if db_client else create_supabase()

    def _handle_supabase_error(self, e: Exception, action: str) -> None:
        """处理 Supabase 返回的错误，将其转换为友好的中文消息"""
        error_msg = str(e)

        if hasattr(e, "args") and e.args:
            error_data = e.args[0]
            if isinstance(error_data, dict):
                msg = error_data.get("msg", "")
                if "email" in msg.lower() or "already" in msg.lower():
                    raise AuthError(message="该邮箱已被注册，请直接登录或使用其他邮箱")
                if "password" in msg.lower():
                    raise AuthError(
                        message="密码强度不足，需至少8位且包含数字和大小写字母"
                    )

        if "email" in error_msg.lower() and (
            "already" in error_msg.lower() or "exists" in error_msg.lower()
        ):
            raise AuthError(message="该邮箱已被注册，请直接登录或使用其他邮箱")
        if (
            "invalid login" in error_msg.lower()
            or "invalid credentials" in error_msg.lower()
        ):
            raise AuthError(message="邮箱或密码错误，请检查后重新输入")
        if "rate limit" in error_msg.lower():
            raise AuthError(message="请求过于频繁，请稍后再试")

        raise AuthError(message=f"{action}失败，请稍后重试")

    def create_user(self, email, password, username):
        """注册新用户并返回数据库记录"""
        try:
            response = self.db_client.auth.sign_up(
                {
                    "email": email,
                    "password": password,
                    "options": {"data": {"username": username}},
                }
            )

            if not response.user:
                raise AuthError("注册失败：无法创建认证账号")

            if response.user and hasattr(response, "session") and not response.session:
                pass

            res = (
                self.db_client.table("user")
                .select("*")
                .eq("id", response.user.id)
                .maybe_single()
                .execute()
            )
            return res.data
        except AuthError:
            raise
        except httpx.HTTPStatusError as e:
            self._handle_supabase_error(e, "注册")
        except Exception as e:
            self._handle_supabase_error(e, "注册")

    def authenticate(self, email, password):
        """登录并返回 Session 对象"""
        try:
            response = self.db_client.auth.sign_in_with_password(
                {"email": email, "password": password}
            )

            if not response:
                raise AuthError("登录失败：凭证无效")

            return response
        except httpx.HTTPStatusError as e:
            self._handle_supabase_error(e, "登录")
        except Exception as e:
            self._handle_supabase_error(e, "登录")

    def get_user_by_token(self, token: str):
        """根据 Token 获取用户信息"""
        # 1. 调用 Supabase Auth 获取用户身份
        auth_response = self.db_client.auth.get_user(token)
        if not auth_response.user:
            return None

        # 2. 关联查询业务表获取更多信息（如头像、偏好设置等）
        res = (
            self.db_client.table("user")
            .select("*")
            .eq("id", auth_response.user.id)
            .maybe_single()
            .execute()
        )

        return res.data

    def sign_out(self):
        """执行全局登出"""
        # 注意：Supabase 的 sign_out 是基于当前客户端状态的
        self.db_client.auth.sign_out()

    def update_user(self, user_id: str, key: str, value: str):
        """更新用户信息"""
        allowed_fields = {"username", "avatar_url", "full_name", "website", "bio"}
        if key not in allowed_fields:
            raise AuthError(f"不允许更新字段: {key}，允许的字段: {allowed_fields}")

        response = (
            self.db_client.table("user")
            .update({key: value})
            .eq("id", user_id)
            .execute()
        )

        if not response.data:
            raise AuthError("更新用户信息失败")

        return response.data[0]
