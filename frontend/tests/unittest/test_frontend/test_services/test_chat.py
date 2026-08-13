"""Tests for ChatClient."""

from unittest.mock import MagicMock, patch

from services.chat import ChatClient


class TestChatClient:
    def test_chat_stream_posts_content_and_history(self):
        client = ChatClient()
        client.base_url = "http://backend.test/api/v1.0"
        mock_response = MagicMock()

        with patch("services.chat.requests.post", return_value=mock_response) as post:
            result = client.chat_stream(
                "年假几天",
                [{"role": "user", "content": "你好"}],
            )

        assert result is mock_response
        post.assert_called_once_with(
            "http://backend.test/api/v1.0/chat/stream",
            json={
                "content": "年假几天",
                "history": [{"role": "user", "content": "你好"}],
            },
            stream=True,
            timeout=120,
        )
