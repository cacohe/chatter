from domain.exceptions import BusinessException
from domain.models.chat import ChatMessage
from infra.chat import history


class GetChatHistory:
    """返回对话的完整历史消息"""

    def execute(self, session_id: str) -> list[ChatMessage]:
        sid = (session_id or "").strip()
        if not sid:
            raise BusinessException("请指定会话")
        return history.get_history(sid)
