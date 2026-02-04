from typing import List, Dict

import httpx
import requests

import streamlit as st

from src.config import settings
from src.infra.log.logger import logger


class BackendApiClient:
    """
    负责与后端通讯的服务类。
    采用 httpx 提高并发性能，并支持全配置驱动。
    """
    def __init__(self):
        self.base_url = settings.backend_api_url.rstrip('/')
        self.timeout = httpx.Timeout(10.0, connect=5.0, read=60.0)

    @staticmethod
    def _get_headers() -> Dict:
        """生产级：通常需要在这里注入 Auth Token 或 API Key"""
        return {
            "Authorization": f"Bearer {settings.api_token}",
            "Content-Type": "application/json"
        }

    def get_available_models(self) -> List[str]:
        """获取可用模型列表"""
        try:
            response = requests.get(f"{self.base_url}/models")
            if response.status_code == 200:
                return response.json()["models"]
        except Exception as e:
            logger.error("Failed to get available models: %s", e)
        return ["openai", "gemini", "llama", "qwen"]

    def switch_model(self, model_name: str) -> bool:
        """切换模型"""
        try:
            response = requests.post(
                f"{self.base_url}/models/switch",
                json={"model_name": model_name}
            )
            return response.status_code == 200
        except Exception as e:
            logger.error("Failed to switch model: %s", e)
            return False

    def send_message(self, message: str, use_tools: bool = True) -> Dict:
        """发送消息到后端API"""
        try:
            response = requests.post(
                f"{self.base_url}/chat",
                json={
                    "message": message,
                    "session_id": st.session_state.session_id or 'default_session',
                    "use_tools": use_tools
                }
            )
            return response.json() if response.status_code == 200 else {}
        except Exception as e:
            logger.error("Failed to send message to API: %s", e)
            return {}

    def clear_session(self) -> None:
        """清空会话"""
        try:
            if st.session_state.session_id:
                requests.post(f"{self.base_url}/sessions/{st.session_state.session_id}/clear")
            st.session_state.messages = []
            st.session_state.session_id = None
        except Exception as e:
            logger.error("Failed to clear session: %s", e)

    def get_history(self) -> List:
        """获取历史记录"""
        try:
            return requests.get(f"{self.base_url}/history").json()
        except Exception as e:
            logger.error(f'Exception occur when get history: {e}')
            return []


# 单例模式供全局使用
backend_api_client = BackendApiClient()
