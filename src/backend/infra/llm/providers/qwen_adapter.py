import dashscope
from http import HTTPStatus
from typing import AsyncGenerator, List, Tuple, Union

from dashscope.api_entities.dashscope_response import Message

from src.backend.infra.llm.base import BaseLLM
from src.backend.infra.llm.schema import ChatMessage, LLMParameters
from src.backend.domain.exceptions import BusinessException
from src.shared.logger import logger

MULTIMODAL_MODELS = {
    "qwen-vl",
    "qwen2-vl",
    "qwen2.5-vl",
    "qwen3-vl",
    "qwen3.5-plus",
    "qwen3.5-vl",
    "qwen3-vl-plus",
    "qwen-audio",
    "qwen-audio-chat",
}


def _is_multimodal_model(model_id: str) -> bool:
    model_lower = model_id.lower()
    for mm_model in MULTIMODAL_MODELS:
        if mm_model in model_lower:
            return True
    return False


class QwenAdapter(BaseLLM):
    def __init__(self, model_id: str, api_key: str, base_url: str = None):
        super().__init__(model_id, api_key, base_url)
        self._is_mm = _is_multimodal_model(self.model_id)

    @staticmethod
    def _preprocess(
        messages, params: LLMParameters
    ) -> Tuple[List[Message], LLMParameters]:
        if not isinstance(messages, list):
            messages = [messages]

        formatted_messages = []
        for m in messages:
            if isinstance(m, Message):
                formatted_messages.append(m)
            if isinstance(m, str):
                formatted_messages.append(Message(role="user", content=m))
        if not params:
            params = LLMParameters()

        return formatted_messages, params

    def _call_api(
        self, messages: List[Message], params: LLMParameters, stream: bool = False
    ):
        if self._is_mm:
            logger.warning("Multimodal models are not supported.")
            raise Exception('Multimodal model not supported!')
            # TODO: 支持多模态模型调用
            # return dashscope.MultiModalConversation.call(
            #     model=self.model_id,
            #     api_key=self.api_key,
            #     messages=messages,
            #     result_format="message",
            #     stream=stream,
            #     temperature=params.temperature,
            #     top_p=params.top_p,
            #     max_tokens=params.max_tokens,
            # )
        return dashscope.Generation.call(
            model=self.model_id,
            api_key=self.api_key,
            messages=messages,
            result_format="message",
            stream=stream,
            incremental_output=True,
            temperature=params.temperature,
            top_p=params.top_p,
            max_tokens=params.max_tokens,
        )

    async def chat(
        self, messages: List[ChatMessage], params: LLMParameters = None
    ) -> str:
        formatted_messages, params = self._preprocess(messages, params)

        response = self._call_api(formatted_messages, params, stream=False)
        if response.status_code == HTTPStatus.OK:
            return response.output.choices[0].message.content
        raise BusinessException(f"Qwen API Error: {response.message}")

    async def stream_chat(
        self, messages: List[ChatMessage], params: LLMParameters = None
    ) -> AsyncGenerator[str, None]:
        formatted_messages, params = self._preprocess(messages, params)

        responses = self._call_api(formatted_messages, params, stream=True)
        for response in responses:
            if response.status_code == HTTPStatus.OK:
                yield response.output.choices[0].message.content
            else:
                raise BusinessException(f"Qwen Stream Error: {response.message}")
