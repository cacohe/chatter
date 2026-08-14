from collections.abc import AsyncGenerator

from llama_index.core.schema import TextNode

from domain.exceptions import BusinessException
from domain.models.chat import ChatMessage, MessageRole
from infra.chat import history, memory
from infra.config import settings
from infra.llm.client import stream_chat
from infra.logger import logger
from infra.rag.runtime import get_retriever

_SYSTEM_PROMPT = (
    "你是一个知识库问答助手。请优先依据「参考文档」回答用户问题；"
    "若参考文档不足以回答，请明确说明知识库中未找到相关信息，不要编造。"
)


def format_context(chunks: list[TextNode]) -> str:
    if not chunks:
        return ""
    parts = [
        f"[{index}] 来源: {chunk.metadata.get('doc_name') or ''}\n{chunk.get_content()}"
        for index, chunk in enumerate(chunks, start=1)
    ]
    return "\n\n".join(parts)


class StreamChat:
    """单次问答，生成流式回答"""

    def _get_chat_context(self, session_id: str) -> list[dict[str, str]]:
        """获取对话上下文。"""
        context: list[dict[str, str]] = []
        for msg in memory.get_messages(session_id):
            if msg.role not in (MessageRole.USER, MessageRole.ASSISTANT):
                continue
            context.append({"role": msg.role.value, "content": msg.content})
        return context

    def _build_messages(self, session_id: str, content: str) -> list[dict[str, str]]:
        """
        构建完整的、需要输入LLM的消息
        """
        messages: list[dict[str, str]] = [{"role": "system", "content": _SYSTEM_PROMPT}]

        related_chunks = get_retriever().retrieve(content, settings.rag_settings.top_k)
        context = format_context(related_chunks)

        if context:
            messages.append(
                {"role": "system", "content": f"以下是参考文档内容:\n{context}"}
            )
            logger.info(f"RAG retrieved {len(related_chunks)} chunks for query")
        else:
            logger.info("RAG retrieved no chunks for query")

        messages.extend(self._get_chat_context(session_id))
        messages.append({"role": "user", "content": content})
        return messages

    def _save_messages(self, session_id: str, content: str, full_response: str):
        """
        保存消息到历史消息列表和短期记忆
        """
        message_pair = [
            ChatMessage(role=MessageRole.USER, content=content),
            ChatMessage(role=MessageRole.ASSISTANT, content=full_response),
        ]
        history.append_history(session_id, message_pair)
        memory.append_messages(session_id, message_pair)

    async def execute(self, session_id: str, content: str) -> AsyncGenerator[str, None]:
        """
        流式输出回答
        """
        full_response = ""
        failed = False

        try:
            messages = self._build_messages(session_id, content)
            async for chunk in stream_chat(messages):
                if chunk.startswith("Error:"):
                    failed = True
                else:
                    full_response += chunk
                yield chunk
        except BusinessException as e:
            failed = True
            logger.exception("Chat stream processing failed")
            yield f"Error: {e.message}"
        except Exception as e:
            failed = True
            logger.exception("Chat stream processing failed")
            yield f"Error: {e!s}"

        if failed or not full_response.strip():
            return

        self._save_messages(session_id, content, full_response)
