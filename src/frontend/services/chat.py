import requests

from src.shared.config import settings


class ChatClient:
    def __init__(self):
        self.base_url = settings.backend_settings.backend_api_url.rstrip("/")

    def chat_stream(self, content: str, history: list) -> requests.Response:
        return requests.post(
            f"{self.base_url}/chat/stream",
            json={"content": content, "history": history},
            stream=True,
            timeout=120,
        )


chat_client = ChatClient()
