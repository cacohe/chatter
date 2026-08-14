"""页面编排：向后端取展示历史、发起流式问答；不在本地保存对话。"""

from collections.abc import Generator

from logger import logger
from services.api_client import backend_api_client
from states.session import session_state


class SessionLogic:
    def start_new_chat(self) -> None:
        """开启新聊天：让后端清空展示历史与 LLM 记忆，再换一个会话 ID。"""
        try:
            backend_api_client.chat.start_new_chat(session_state.session_id)
        except Exception as e:
            logger.exception(f"Failed to start new chat: {e}")
        session_state.new_session()

    def load_display_history(self) -> list[dict]:
        """从后端拉取完整展示历史（不是 LLM 上下文）。"""
        payload = backend_api_client.chat.get_messages(session_state.session_id)
        return payload.get("messages") or []

    def chat_stream(
        self, content: str
    ) -> Generator[tuple[str | None, str | None], None, None]:
        """逐 token 产出 (chunk, error)；成功时 error 为 None。"""
        try:
            response = backend_api_client.chat.chat_stream(
                content=content, session_id=session_state.session_id
            )
            if response.status_code == 200:
                for line in response.iter_lines():
                    if line:
                        decoded_line = line.decode("utf-8")
                        if decoded_line.startswith("data: "):
                            chunk = decoded_line[6:]
                            yield (chunk, None)
            else:
                try:
                    error_msg = response.json().get("detail", "大模型调用失败")
                except Exception:
                    error_msg = "大模型调用失败"
                logger.error(
                    f"Error when chat stream, Status Code: {response.status_code}, "
                    f"Message: {error_msg}"
                )
                yield (None, error_msg)
        except Exception as e:
            logger.exception(f"Exception when stream chat: {e}")
            yield (None, "大模型调用失败，请稍后重试")


session_logic = SessionLogic()
