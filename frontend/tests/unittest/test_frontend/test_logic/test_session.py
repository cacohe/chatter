"""Tests for SessionLogic."""

from unittest.mock import MagicMock, patch

from logic.session import SessionLogic


class TestSessionLogic:
    def test_start_new_chat_clears_llm_memory_and_display(self):
        session = SessionLogic()
        with (
            patch("logic.session.session_state") as mock_state,
            patch("logic.session.backend_api_client") as mock_api,
        ):
            mock_state.session_id = "old-id"
            session.start_new_chat()
        mock_api.chat.start_new_chat.assert_called_once_with("old-id")
        mock_state.new_session.assert_called_once()

    def test_load_display_history_from_api(self):
        session = SessionLogic()
        with (
            patch("logic.session.session_state") as mock_state,
            patch("logic.session.backend_api_client") as mock_api,
        ):
            mock_state.session_id = "s1"
            mock_api.chat.get_messages.return_value = {
                "session_id": "s1",
                "messages": [{"role": "user", "content": "问题"}],
            }
            messages = session.load_display_history()

        assert messages == [{"role": "user", "content": "问题"}]
        mock_api.chat.get_messages.assert_called_once_with("s1")

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
            mock_state.session_id = "s1"
            mock_api.chat.chat_stream.return_value = response
            chunks = list(session.chat_stream("年假几天"))

        assert chunks == [("你好", None), ("，世界", None)]
        mock_api.chat.chat_stream.assert_called_once_with(
            content="年假几天", session_id="s1"
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
            mock_state.session_id = "s1"
            mock_api.chat.chat_stream.return_value = response
            chunks = list(session.chat_stream("hi"))

        assert chunks == [(None, "模型不可用")]

    def test_chat_stream_yields_fallback_on_exception(self):
        session = SessionLogic()
        with (
            patch("logic.session.session_state") as mock_state,
            patch("logic.session.backend_api_client") as mock_api,
        ):
            mock_state.session_id = "s1"
            mock_api.chat.chat_stream.side_effect = RuntimeError("boom")
            chunks = list(session.chat_stream("hi"))

        assert chunks == [(None, "大模型调用失败，请稍后重试")]
