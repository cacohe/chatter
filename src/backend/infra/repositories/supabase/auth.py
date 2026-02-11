from src.backend.domain.repository_interfaces.auth import IAuthRepository
from src.backend.infra.db.supabase.client import create_supabase
from src.backend.domain.exceptions import AuthError


class SupabaseAuthRepository(IAuthRepository):
    def __init__(self, db_client=None):
        self.db_client = db_client if db_client else create_supabase()

    def create_user(self, email, password, username):
        """注册新用户并返回数据库记录"""
        # 1. Supabase Auth 注册
        response = self.db_client.auth.sign_up(
            {
                "email": email,
                "password": password,
                "options": {"data": {"username": username}},
            }
        )

        if not response.user:
            raise AuthError("注册失败：无法创建认证账号")

        # 2. 获取 public.user 表中的详细信息
        # 通常这里会通过数据库触发器在 Auth 注册时自动同步
        res = (
            self.db_client.table("user")
            .select("*")
            .eq("id", response.user.id)
            .maybe_single()
            .execute()
        )
        return res.data

    def authenticate(self, email, password):
        """登录并返回 Session 对象"""
        # 使用 Supabase 提供的账号密码登录
        response = self.db_client.auth.sign_in_with_password(
            {"email": email, "password": password}
        )

        if not response:
            raise AuthError("登录失败：凭证无效")

        return response

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
