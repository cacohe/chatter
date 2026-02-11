import dashscope
from http import HTTPStatus
from typing import AsyncGenerator, List

from dashscope.api_entities.dashscope_response import Message

from src.backend.infra.llm.base import BaseLLM
from src.backend.infra.llm.schema import ChatMessage, LLMParameters
from src.backend.domain.exceptions import BusinessException


class QwenAdapter(BaseLLM):
    MODEL_MAPPING = {
        "qwen3.5-plus": "qwen-plus",
        "qwen3.5-flash": "qwen-flash",
    }

    def _get_dashscope_model(self) -> str:
        return self.MODEL_MAPPING.get(self.model_id, self.model_id)

    async def chat(
        self, messages: List[ChatMessage], params: LLMParameters = None
    ) -> str:
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
        response = dashscope.Generation.call(
            model=self._get_dashscope_model(),
            api_key=self.api_key,
            messages=formatted_messages,
            result_format="message",
            temperature=params.temperature,
            top_p=params.top_p,
            max_tokens=params.max_tokens,
        )
        if response.status_code == HTTPStatus.OK:
            return response.output.choices[0].message.content
        raise BusinessException(f"Qwen API Error: {response.message}")

    async def stream_chat(
        self, messages: List[ChatMessage], params: LLMParameters = None
    ) -> AsyncGenerator[str, None]:
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

        responses = dashscope.Generation.call(
            model=self._get_dashscope_model(),
            api_key=self.api_key,
            messages=formatted_messages,
            result_format="message",
            stream=True,
            incremental_output=True,  # 增量输出，方便直接 yield
            temperature=params.temperature,
        )
        for response in responses:
            if response.status_code == HTTPStatus.OK:
                yield response.output.choices[0].message.content
            else:
                raise BusinessException(f"Qwen Stream Error: {response.message}")
