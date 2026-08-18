from domain.exceptions import BusinessException
from infra.chat import history, memory
from infra.logger import logger


class StartNewChat:
    """开启新对话"""

    def execute(self, session_id: str) -> None:
        sid = (session_id or "").strip()
        if not sid:
            raise BusinessException("请指定会话")

        # 清空对话历史 与 LLM 短期记忆
        history.clear_history(sid)
        memory.clear_session(sid)
        logger.info(
            "Started new chat, cleared display history and LLM memory for %s", sid
        )
