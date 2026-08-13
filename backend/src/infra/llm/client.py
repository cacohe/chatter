"""LiteLLM 流式调用；模型短名映射到供应商前缀（如 dashscope/...）。"""

from collections.abc import AsyncGenerator

import litellm

from domain.exceptions import BusinessException
from infra.config import settings
from infra.logger import logger

_LITELLM_MODELS: dict[str, str] = {
    "qwen-flash-character": "dashscope/qwen-flash-character",
    "qwen3-max-2026-01-23": "dashscope/qwen3-max-2026-01-23",
    "qwen3.7-max": "dashscope/qwen3.7-max",
}


def resolve_model(model_id: str) -> str:
    """只允许白名单模型，避免把任意字符串传给 LiteLLM。"""
    litellm_model = _LITELLM_MODELS.get(model_id)
    if not litellm_model:
        raise BusinessException(f"默认模型未注册: {model_id}")
    return litellm_model


async def stream_chat(
    messages: list[dict[str, str]],
    *,
    model_id: str | None = None,
    temperature: float = 0.7,
    top_p: float = 1.0,
    max_tokens: int | None = 2048,
) -> AsyncGenerator[str, None]:
    """按 token 产出模型增量文本；调用失败转为 BusinessException。"""
    model = resolve_model(model_id or settings.llm_settings.default_llm)
    try:
        response = await litellm.acompletion(
            model=model,
            messages=messages,
            api_key=settings.llm_settings.dashscope_api_key,
            temperature=temperature,
            top_p=top_p,
            max_tokens=max_tokens,
            stream=True,
        )
        async for chunk in response:
            content = chunk.choices[0].delta.content
            if content:
                yield content
    except BusinessException:
        raise
    except Exception as exc:
        logger.exception("LiteLLM stream failed for model %s", model)
        raise BusinessException(f"LLM 流式调用失败: {exc}") from exc
