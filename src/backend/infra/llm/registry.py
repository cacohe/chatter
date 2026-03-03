from typing import Dict, Type
from src.backend.infra.llm.base import BaseLLM
from src.backend.infra.llm.providers.openai_adapter import OpenAIAdapter
from src.backend.infra.llm.providers.gemini_adapter import GeminiAdapter
from src.backend.infra.llm.providers.qwen_adapter import QwenAdapter
from src.shared.config import settings
from src.shared.logger import logger


class ModelRegistry:
    """仅仅作为一个映射仓库"""

    _mapping: Dict[str, Type[BaseLLM]] = {
        "gpt-4o": OpenAIAdapter,
        "gpt-3.5-turbo": OpenAIAdapter,
        "gemini-1.5-pro": GeminiAdapter,
        "deepseek-chat": OpenAIAdapter,  # 兼容 OpenAI 格式
        "qwen-flash-character": QwenAdapter,
        "qwen3-max-2026-01-23": QwenAdapter,
    }

    _api_key_map = {
        "gpt-4o": "openai_api_key",
        "gpt-3.5-turbo": "openai_api_key",
        "gemini-1.5-pro": "gemini_api_key",
        "deepseek-chat": "deepseek_api_key",
        "qwen-flash-character": "dashscope_api_key",
        "qwen3-max-2026-01-23": "dashscope_api_key",
    }

    _model_id_to_name_mapping: Dict[str, str] = {
        "gpt-4o": "GPT-4O",
        "gpt-3.5-turbo": "GPT-3.5-TURBO",
        "gemini-1.5-pro": "Gemini-1.5-Pro",
        "deepseek-chat": "DeepSeek-Chat",
        "qwen-flash-character": "Qwen-Flash",
        "qwen3-max-2026-01-23": "Qwen-Max",
    }

    @classmethod
    def get_class(cls, model_id: str) -> Type[BaseLLM]:
        adapter_cls = cls._mapping.get(model_id)
        if not adapter_cls:
            raise ValueError(f"模型 {model_id} 未在注册中心登记")
        return adapter_cls

    @classmethod
    def exists(cls, target_model_id):
        return target_model_id in cls._mapping

    @classmethod
    def get_all_model_ids(cls):
        return cls._mapping.keys()

    @classmethod
    def is_model_available(cls, model_id: str) -> bool:
        """检查模型是否可用（是否有配置 API Key）"""
        api_key_attr = cls._api_key_map.get(model_id)
        if not api_key_attr:
            return False

        api_key = getattr(settings.llm_settings, api_key_attr, None)
        if not api_key:
            logger.warning(f"模型 {model_id} 的 API Key 未配置，已跳过加载")
            return False
        return True

    @classmethod
    def get_available_model_ids(cls) -> list:
        """获取所有可用的模型 ID（已配置 API Key 的模型）"""
        available = []
        for model_id in cls._mapping.keys():
            if cls.is_model_available(model_id):
                available.append(model_id)
        return available

    @classmethod
    def get_model_name(cls, model_id: str) -> str:
        return cls._model_id_to_name_mapping.get(model_id, model_id.upper())
