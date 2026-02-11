import google.genai as genai
from typing import AsyncGenerator, List
from src.backend.infra.llm.base import BaseLLM
from src.backend.infra.llm.schema import ChatMessage, LLMParameters


class GeminiAdapter(BaseLLM):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        genai.configure(api_key=self.api_key)
        self.client = genai.GenerativeModel(self.model_id)

    @staticmethod
    def _convert_messages(messages: List[ChatMessage]):
        """将标准格式转换为 Gemini 格式: user/model"""
        gemini_history = []
        for m in messages:
            role = "user" if m.role == "user" else "model"
            gemini_history.append({"role": role, "parts": [m.content]})
        return gemini_history

    async def chat(self, messages: List[ChatMessage], params: LLMParameters) -> str:
        # Gemini 推荐使用 start_chat 维护上下文，或者直接发送 history
        history = self._convert_messages(messages[:-1])
        last_msg = messages[-1].content

        chat_session = self.client.start_chat(history=history)
        config = genai.types.GenerationConfig(
            temperature=params.temperature,
            top_p=params.top_p,
            max_output_tokens=params.max_tokens
        )

        response = await chat_session.send_message_async(last_msg, generation_config=config)
        return response.text

    async def stream_chat(self, messages: List[ChatMessage], params: LLMParameters) -> AsyncGenerator[str, None]:
        history = self._convert_messages(messages[:-1])
        last_msg = messages[-1].content

        chat_session = self.client.start_chat(history=history)
        config = genai.types.GenerationConfig(temperature=params.temperature)

        response = await chat_session.send_message_async(
            last_msg,
            generation_config=config,
            stream=True
        )
        async for chunk in response:
            if chunk.text:
                yield chunk.text