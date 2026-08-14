"""Tests for ChatClient."""

from unittest.mock import MagicMock, patch

from services.chat import ChatClient


class TestChatClient:
    def test_chat_stream_posts_content_and_session_id(self):
        client = ChatClient()
        client.base_url = "http://backend.test/api/v1.0"
        mock_response = MagicMock()

        with patch("services.chat.requests.post", return_value=mock_response) as post:
            result = client.chat_stream("年假几天", "s1")

        assert result is mock_response
        post.assert_called_once_with(
            "http://backend.test/api/v1.0/chat/stream",
            json={"content": "年假几天", "session_id": "s1"},
            stream=True,
            timeout=120,
        )

    def test_get_messages(self):
        client = ChatClient()
        client.base_url = "http://backend.test/api/v1.0"
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "session_id": "s1",
            "messages": [{"role": "user", "content": "问题"}],
        }

        with patch("services.chat.requests.get", return_value=mock_response) as get:
            result = client.get_messages("s1")

        assert result["messages"][0]["content"] == "问题"
        get.assert_called_once_with(
            "http://backend.test/api/v1.0/chat/messages",
            params={"session_id": "s1"},
            timeout=30,
        )
        mock_response.raise_for_status.assert_called_once()

    def test_start_new_chat(self):
        client = ChatClient()
        client.base_url = "http://backend.test/api/v1.0"
        mock_response = MagicMock()

        with patch("services.chat.requests.post", return_value=mock_response) as post:
            client.start_new_chat("s1")

        post.assert_called_once_with(
            "http://backend.test/api/v1.0/chat/new",
            json={"session_id": "s1"},
            timeout=30,
        )
