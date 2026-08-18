import re
from collections.abc import AsyncGenerator

from llama_index.core.schema import TextNode

from domain.exceptions import BusinessException
from domain.models.chat import Citation, ChatMessage, MessageRole
from infra.chat import history, memory
from infra.config import settings
from infra.llm.client import stream_chat
from infra.logger import logger
from infra.rag.runtime import get_retriever

_SYSTEM_PROMPT = (
    "你是一个知识库问答助手。请优先依据「参考文档」回答用户问题；"
    "若参考文档不足以回答，请明确说明知识库中未找到相关信息，不要编造。"
    "若使用了参考文档中的事实，请在对应语句后标注方括号编号，如 [1]、[2]。"
)


def _citable_chunks(chunks: list[TextNode]) -> list[tuple[int, TextNode]]:
    """过滤出有 doc_name 的 chunk 并统一编号（从 1 开始）。

    format_context 和 build_citations 必须共用此序列，
    否则 prompt 中的 [n] 与 Citation.index 会错位。
    """
    result: list[tuple[int, TextNode]] = []
    for chunk in chunks:
        if not str(chunk.metadata.get("doc_name") or ""):
            continue
        result.append((len(result) + 1, chunk))
    return result


def format_context(chunks: list[TextNode]) -> str:
    numbered = _citable_chunks(chunks)
    if not numbered:
        return ""
    parts = [
        f"[{index}] 来源: {chunk.metadata.get('doc_name') or ''}\n{chunk.get_content()}"
        for index, chunk in numbered
    ]
    return "\n\n".join(parts)


def build_citations(chunks: list[TextNode]) -> list[Citation]:
    citations: list[Citation] = []
    for index, chunk in _citable_chunks(chunks):
        doc_name = str(chunk.metadata.get("doc_name") or "")
        try:
            chunk_index = int(chunk.metadata.get("chunk_index") or 0)
        except (TypeError, ValueError):
            chunk_index = 0
        snippet = chunk.get_content().strip().replace("\n", " ")
        if len(snippet) > 200:
            snippet = snippet[:200] + "…"
        source_uri = str(chunk.metadata.get("source_uri") or "")
        score_raw = chunk.metadata.get("score")
        score: float | None = None
        if score_raw is not None:
            try:
                score = float(score_raw)
            except (TypeError, ValueError):
                score = None
        citations.append(
            Citation(
                index=index,
                doc_name=doc_name,
                chunk_index=chunk_index,
                snippet=snippet,
                source_uri=source_uri,
                score=score,
            )
        )
    return citations


# 匹配回答正文中的引用编号：半角 [1] / 全角【1】/ 全角方括号 ［1］
_CITATION_RE = re.compile(r"[\[【［](\d+)[\]】］]")


def validate_citations(response: str, citations: list[Citation]) -> list[Citation]:
    """校验回答中的引用编号，标记每条 citation 是否被实际使用。

    - 从回答正文提取所有 [n] 编号
    - 编号在 citations 范围内的标记 used=True
    - 检索到但未被引用的标记 used=False
    - 回答中出现的无效编号（超出范围）仅记录日志，不影响结果
    """
    cited_indices = {int(m) for m in _CITATION_RE.findall(response)}
    valid_indices = {c.index for c in citations}
    # 记录无效引用编号，便于排查模型幻觉
    invalid = cited_indices - valid_indices
    if invalid:
        logger.warning("回答中出现无效引用编号: %s", sorted(invalid))
    validated: list[Citation] = []
    for citation in citations:
        validated.append(citation.model_copy(update={"used": citation.index in cited_indices}))
    return validated


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

    def _build_messages(
        self, session_id: str, content: str
    ) -> tuple[list[dict[str, str]], list[Citation]]:
        """
        构建完整的、需要输入LLM的消息
        """
        messages: list[dict[str, str]] = [{"role": "system", "content": _SYSTEM_PROMPT}]

        related_chunks = get_retriever().retrieve(content, settings.rag_settings.top_k)
        context = format_context(related_chunks)
        citations = build_citations(related_chunks)

        if context:
            messages.append(
                {"role": "system", "content": f"以下是参考文档内容:\n{context}"}
            )
            logger.info(f"RAG retrieved {len(related_chunks)} chunks for query")
        else:
            logger.info("RAG retrieved no chunks for query")

        messages.extend(self._get_chat_context(session_id))
        messages.append({"role": "user", "content": content})
        return messages, citations

    def _save_messages(
        self,
        session_id: str,
        content: str,
        full_response: str,
        citations: list[Citation],
    ):
        """
        保存消息到历史消息列表和短期记忆
        """
        message_pair = [
            ChatMessage(role=MessageRole.USER, content=content),
            ChatMessage(
                role=MessageRole.ASSISTANT,
                content=full_response,
                citations=citations,
            ),
        ]
        history.append_history(session_id, message_pair)
        memory.append_messages(session_id, message_pair)

    async def execute(self, session_id: str, content: str) -> AsyncGenerator[str, None]:
        """
        流式输出回答
        """
        full_response = ""
        failed = False
        citations: list[Citation] = []

        try:
            messages, citations = self._build_messages(session_id, content)
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

        # 流式结束后校验：标记哪些来源被回答实际引用
        citations = validate_citations(full_response, citations)
        self._save_messages(session_id, content, full_response, citations)
