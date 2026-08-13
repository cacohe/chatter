"""Tests for SessionLogic."""

from unittest.mock import MagicMock, patch

from logic.session import SessionLogic


class TestSessionLogic:
    def test_clear_conversation(self):
        session = SessionLogic()
        with patch("logic.session.session_state") as mock_state:
            session.clear_conversation()
        mock_state.clear_messages.assert_called_once()

    def test_history_uses_recent_messages_and_role_value(self):
        class _Role:
            value = "assistant"

        messages = [
            {"role": "user", "content": "1"},
            {"role": "user", "content": "2"},
            {"role": _Role(), "content": "3"},
        ]
        session = SessionLogic()
        with (
            patch("logic.session.session_state") as mock_state,
            patch("logic.session.settings") as mock_settings,
        ):
            mock_state.messages = messages
            mock_settings.max_history_messages = 2
            history = session._get_history_for_api()

        assert history == [
            {"role": "user", "content": "2"},
            {"role": "assistant", "content": "3"},
        ]

    def test_chat_stream_yields_sse_chunks(self):
        response = MagicMock()
        response.status_code = 200
        response.iter_lines.return_value = [
            "data: 你好".encode(),
            b"ignored",
            "data: ，世界".encode(),
        ]
        session = SessionLogic()
        with (
            patch("logic.session.session_state") as mock_state,
            patch("logic.session.backend_api_client") as mock_api,
        ):
            mock_state.messages = []
            mock_api.chat.chat_stream.return_value = response
            chunks = list(session.chat_stream("年假几天"))

        assert chunks == [("你好", None), ("，世界", None)]
        mock_api.chat.chat_stream.assert_called_once_with(
            content="年假几天", history=[]
        )

    def test_chat_stream_yields_error_from_non_200(self):
        response = MagicMock()
        response.status_code = 500
        response.json.return_value = {"detail": "模型不可用"}
        session = SessionLogic()
        with (
            patch("logic.session.session_state") as mock_state,
            patch("logic.session.backend_api_client") as mock_api,
        ):
            mock_state.messages = []
            mock_api.chat.chat_stream.return_value = response
            chunks = list(session.chat_stream("hi"))

        assert chunks == [(None, "模型不可用")]

    def test_chat_stream_yields_fallback_on_exception(self):
        session = SessionLogic()
        with (
            patch("logic.session.session_state") as mock_state,
            patch("logic.session.backend_api_client") as mock_api,
        ):
            mock_state.messages = []
            mock_api.chat.chat_stream.side_effect = RuntimeError("boom")
            chunks = list(session.chat_stream("hi"))

        assert chunks == [(None, "大模型调用失败，请稍后重试")]
