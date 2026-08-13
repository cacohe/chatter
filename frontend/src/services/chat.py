"""对话 API：POST /chat/stream，保持连接读取 SSE。"""

import requests

from config import settings


class ChatClient:
    """对话流客户端；调用方需自行 iter_lines 解析 SSE。"""

    def __init__(self):
        self.base_url = settings.backend_api_url.rstrip("/")

    def chat_stream(self, content: str, history: list) -> requests.Response:
        return requests.post(
            f"{self.base_url}/chat/stream",
            json={"content": content, "history": history},
            stream=True,
            timeout=120,
        )


chat_client = ChatClient()
