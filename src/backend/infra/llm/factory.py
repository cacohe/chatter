from src.shared.config import settings
from src.backend.infra.llm.registry import ModelRegistry


class LLMFactory:
    @classmethod
    def get_instance(cls, model_id: str):
        # 1. 从注册中心拿到类
        adapter_cls = ModelRegistry.get_class(model_id)

        # 2. 集中处理配置注入逻辑 (从 Settings 获取)
        if model_id.startswith("gpt"):
            return adapter_cls(model_id=model_id, api_key=settings.llm_settings.openai_api_key)

        if model_id.startswith("gemini"):
            return adapter_cls(model_id=model_id, api_key=settings.llm_settings.gemini_api_key)

        if model_id.startswith("qwen"):
            return adapter_cls(model_id=model_id, api_key=settings.llm_settings.dashscope_api_key)

        # 3. 兜底逻辑
        return adapter_cls(model_id=model_id, api_key=settings.llm_settings.dashscope_api_key)