from collections.abc import Generator

from config import settings
from logger import logger
from services.api_client import backend_api_client
from states.session import session_state


class SessionLogic:
    @staticmethod
    def clear_conversation() -> None:
        session_state.clear_messages()

    def _get_history_for_api(self) -> list:
        messages = session_state.messages
        if not messages:
            return []

        max_history = settings.max_history_messages
        history = []
        for msg in messages[-max_history:]:
            role = msg.get("role", "user")
            if hasattr(role, "value"):
                role = role.value
            history.append({"role": str(role), "content": msg.get("content", "")})
        return history

    def chat_stream(
        self, content: str
    ) -> Generator[tuple[str | None, str | None], None, None]:
        try:
            history = self._get_history_for_api()
            response = backend_api_client.chat.chat_stream(
                content=content, history=history
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
