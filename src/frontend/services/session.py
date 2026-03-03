from typing import Optional, List, Dict
import uuid

import requests
import streamlit as st
from requests import Response

from src.shared.config import settings


class SessionClients:
    def __init__(self, base_url: str):
        self.chat_url = f"{base_url}/chat"
        self.llm_url = f"{base_url}/llm"

    @staticmethod
    def _get_headers():
        token = st.session_state.get("access_token")
        return {"Authorization": f"Bearer {token}"} if token else {}

    def switch_model(self, session_id: uuid.UUID, model_id: str) -> Response:
        """切换当前会话的模型"""
        url = f"{self.llm_url}/switch"
        payload = {"session_id": str(session_id), "model_id": model_id}
        return requests.post(url, json=payload, headers=self._get_headers())

    def chat_non_stream(
        self,
        session_id: uuid.UUID,
        content: str,
        model_id: Optional[str] = None,
        history: Optional[List[Dict]] = None,
    ) -> Response:
        """发送消息并获取非流式响应"""
        payload = {
            "session_id": str(session_id),
            "content": content,
            "model_id": model_id,
            "history": history or [],
        }
        return requests.post(
            f"{self.chat_url}", json=payload, headers=self._get_headers(), stream=False
        )

    def chat_stream(
        self,
        session_id: uuid.UUID,
        content: str,
        model_id: Optional[str] = None,
        history: Optional[List[Dict]] = None,
    ) -> Response:
        """发送消息并获取流式响应"""
        payload = {
            "session_id": str(session_id),
            "content": content,
            "model_id": model_id,
            "history": history or [],
        }

        return requests.post(
            f"{self.chat_url}/stream",
            json=payload,
            headers=self._get_headers(),
            stream=True,
        )


@st.cache_resource
def get_session_client():
    """
    使用 st.cache_resource 确保在同一个会话(Session)或跨会话中，
    SessionClients 只被实例化一次。
    """
    return SessionClients(base_url=settings.backend_settings.backend_api_url)


# 获取实例
session_client = get_session_client()
