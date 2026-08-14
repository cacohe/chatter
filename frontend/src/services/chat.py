"""聊天 API：拉取完整展示历史；流式问答。LLM 短期记忆只在后端使用。"""

import requests

from config import settings


class ChatClient:
    """聊天客户端。前端只拉展示数据，不维护对话业务状态。"""

    def __init__(self):
        self.base_url = settings.backend_api_url.rstrip("/")

    def get_messages(self, session_id: str) -> dict:
        response = requests.get(
            f"{self.base_url}/chat/messages",
            params={"session_id": session_id},
            timeout=30,
        )
        response.raise_for_status()
        return response.json()

    def chat_stream(self, content: str, session_id: str) -> requests.Response:
        return requests.post(
            f"{self.base_url}/chat/stream",
            json={"content": content, "session_id": session_id},
            stream=True,
            timeout=120,
        )

    def start_new_chat(self, session_id: str) -> None:
        """通知后端清空该会话的展示历史与 LLM 短期记忆。"""
        response = requests.post(
            f"{self.base_url}/chat/new",
            json={"session_id": session_id},
            timeout=30,
        )
        response.raise_for_status()


chat_client = ChatClient()
