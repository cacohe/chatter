from typing import Dict, Any
import streamlit as st

from src.shared.logger import logger


class ConfigService:
    """配置服务"""

    @staticmethod
    def get_app_config() -> Dict[str, Any]:
        """获取应用配置"""
        return {
            "app_name": "Caco",
            "version": "1.0.0",
            "max_message_length": 4000,
            "supported_formats": ["text", "markdown"],
        }

    @staticmethod
    def get_user_preferences() -> Dict[str, Any]:
        """获取用户偏好设置"""
        return st.session_state.get(
            "user_preferences",
            {
                "theme": "light",
                "language": "zh-CN",
                "auto_save": True,
            },
        )

    @staticmethod
    def save_user_preferences(preferences: Dict[str, Any]):
        """保存用户偏好设置"""
        try:
            st.session_state.user_preferences = preferences
            # 这里应该调用后端API保存设置
        except Exception as e:
            logger.exception("Exception when save user preferences: ", e)


config_service = ConfigService()
