from abc import ABC, abstractmethod
from typing import AsyncGenerator, Optional, List
from src.backend.infra.llm.schema import LLMParameters, ChatMessage


class BaseLLM(ABC):
    def __init__(self, model_id: str, api_key: str, base_url: Optional[str] = None):
        self.model_id = model_id
        self.api_key = api_key
        self.base_url = base_url

    @abstractmethod
    async def chat(self, messages: List[ChatMessage], params: LLMParameters) -> str:
        """非流式对话"""
        pass

    @abstractmethod
    async def stream_chat(self, messages: List[ChatMessage], params: LLMParameters) -> AsyncGenerator[str, None]:
        """流式对话接口"""
        pass