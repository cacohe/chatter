import requests
import streamlit as st
import uuid
from requests import Response

from src.shared.config import settings
from src.shared.schemas import auth as auth_schema


class UserClients:
    def __init__(self, base_url: str):
        self.auth_url = base_url + "/auth"
        self.session_url = base_url + "/session"
        self.llm_url = base_url + "/llm"

    @staticmethod
    def _get_headers():
        """统一获取带 Token 的请求头"""
        headers = {}
        token = st.session_state.get("access_token")
        if token:
            headers["Authorization"] = f"Bearer {token}"
        return headers

    def register(self, user_data: auth_schema.UserCreate) -> Response:
        """用户注册"""
        url = f"{self.auth_url}/register"
        return requests.post(url, json=user_data.model_dump())

    def login(self, login_data: auth_schema.LoginRequest) -> Response:
        """
        用户登录
        成功后将 Token 写入 session_state
        """
        url = f"{self.auth_url}/login"
        return requests.post(url, json=login_data.model_dump())

    def get_me(self) -> Response:
        """获取当前用户信息"""
        url = f"{self.auth_url}/me"
        return requests.get(url, headers=self._get_headers())

    def update_me(self, update_data: auth_schema.UserUpdate) -> Response:
        """更新当前用户信息"""
        url = f"{self.auth_url}/update"
        return requests.post(url, json=update_data.model_dump())

    def logout(self) -> Response:
        """退出登录"""
        url = f"{self.auth_url}/logout"
        return requests.post(url, headers=self._get_headers())

    def create_session(self) -> Response:
        """创建新会话"""
        url = f"{self.session_url}/create"
        return requests.post(url, headers=self._get_headers())

    def get_history(self) -> Response:
        """获取当前用户的所有会话历史"""
        url = f"{self.session_url}/history"
        return requests.get(url, headers=self._get_headers())

    def delete_session(self, session_id: uuid.UUID) -> Response:
        """删除指定会话"""
        url = f"{self.session_url}/delete"
        payload = {"session_id": str(session_id)}
        return requests.post(url, json=payload, headers=self._get_headers())

    def rename_session(self, session_id: uuid.UUID, new_title: str) -> Response:
        """重命名会话"""
        url = f"{self.session_url}/rename"
        payload = {"session_id": str(session_id), "new_title": new_title}
        return requests.post(url, json=payload, headers=self._get_headers())

    def add_session(self, session_id: uuid.UUID, title: str) -> Response:
        """添加会话到会话历史"""
        url = f"{self.session_url}/add"
        payload = {"session_id": str(session_id), "title": title}
        return requests.post(url, json=payload, headers=self._get_headers())

    def get_available_models(self) -> Response:
        url = f"{self.llm_url}/list"
        return requests.get(url, headers=self._get_headers())


@st.cache_resource
def get_user_client():
    """
    使用 st.cache_resource 确保在同一个会话(Session)或跨会话中，
    UserClients 只被实例化一次。
    """
    return UserClients(base_url=settings.backend_settings.backend_api_url)


# 获取实例
user_client = get_user_client()
