from collections.abc import AsyncGenerator

from src.backend.domain.exceptions import BusinessException
from src.backend.infra.llm.client import stream_chat
from src.backend.infra.rag.retriever import format_context, retrieve
from src.shared.config import settings
from src.shared.logger import logger
from src.shared.schemas import chat as chat_schema

_SYSTEM_PROMPT = (
    "你是一个知识库问答助手。请优先依据「参考文档」回答用户问题；"
    "若参考文档不足以回答，请明确说明知识库中未找到相关信息，不要编造。"
)


class ChatService:
    @property
    def max_history_messages(self) -> int:
        return settings.llm_settings.max_history_messages

    def _history_from_request(
        self, request: chat_schema.ChatRequest
    ) -> list[dict[str, str]]:
        if not request.history:
            return []

        history: list[dict[str, str]] = []
        for msg in request.history[-self.max_history_messages :]:
            role = msg.role.value if hasattr(msg.role, "value") else str(msg.role)
            role = role.lower()
            if role not in ("user", "assistant"):
                continue
            history.append({"role": role, "content": msg.content})
        return history

    def _build_messages(self, request: chat_schema.ChatRequest) -> list[dict[str, str]]:
        messages: list[dict[str, str]] = [{"role": "system", "content": _SYSTEM_PROMPT}]

        chunks = retrieve(request.content)
        context = format_context(chunks)
        if context:
            messages.append(
                {"role": "system", "content": f"以下是参考文档内容:\n{context}"}
            )
            logger.info(f"RAG retrieved {len(chunks)} chunks for query")
        else:
            logger.info("RAG retrieved no chunks for query")

        messages.extend(self._history_from_request(request))
        messages.append({"role": "user", "content": request.content})
        return messages

    async def handle_chat_stream(
        self, request: chat_schema.ChatRequest
    ) -> AsyncGenerator[str, None]:
        try:
            messages = self._build_messages(request)
            async for chunk in stream_chat(messages):
                yield chunk
        except BusinessException as e:
            logger.exception("Chat stream processing failed")
            yield f"Error: {e.message}"
        except Exception as e:
            logger.exception("Chat stream processing failed")
            yield f"Error: {e!s}"
