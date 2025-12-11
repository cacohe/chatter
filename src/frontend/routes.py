import requests
import streamlit as st

from src.config import settings
from src.infra.log.logger import logger


# API基础URL
API_BASE = f"http://{settings.backend_ip}:{settings.backend_port}"


def get_available_models():
    """获取可用模型列表"""
    try:
        response = requests.get(f"{API_BASE}/models")
        if response.status_code == 200:
            return response.json()["models"]
    except Exception as e:
        logger.error("Failed to get available models: %s", e)
    return ["openai", "gemini", "llama", "qwen"]


def switch_model(model_name):
    """切换模型"""
    try:
        response = requests.post(
            f"{API_BASE}/models/switch",
            json={"model_name": model_name}
        )
        return response.status_code == 200
    except Exception as e:
        logger.error("Failed to switch model: %s", e)
        return False


def send_message(message, use_tools=True):
    """发送消息到后端API"""
    try:
        response = requests.post(
            f"{API_BASE}/chat",
            json={
                "message": message,
                "session_id": st.session_state.session_id or 'default_session',
                "use_tools": use_tools
            }
        )
        return response.json() if response.status_code == 200 else None
    except Exception as e:
        logger.error("Failed to send message to API: %s", e)
        return None
