from openai import AsyncOpenAI
from src.backend.infra.llm.base import BaseLLM


class OpenAIAdapter(BaseLLM):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.client = AsyncOpenAI(api_key=self.api_key, base_url=self.base_url)

    async def chat(self, messages, params) -> str:
        response = await self.client.chat.completions.create(
            model=self.model_id,
            messages=[m.model_dump() for m in messages],
            temperature=params.temperature,
            max_tokens=params.max_tokens,
            stream=False
        )
        return response.choices[0].message.content

    async def stream_chat(self, messages, params):
        response = await self.client.chat.completions.create(
            model=self.model_id,
            messages=[m.model_dump() for m in messages],
            temperature=params.temperature,
            stream=True
        )
        async for chunk in response:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content