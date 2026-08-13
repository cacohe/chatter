"""Tests for SessionState."""

from unittest.mock import patch

from states.session import SessionState


class TestSessionState:
    def test_messages_default_to_empty_list(self):
        state = {}
        with patch("states.session.st.session_state", state):
            assert SessionState().messages == []

    def test_messages_roundtrip(self):
        state = {}
        session = SessionState()
        with patch("states.session.st.session_state", state):
            session.messages = [{"role": "user", "content": "你好"}]
            assert session.messages == [{"role": "user", "content": "你好"}]
            assert state["messages"] == [{"role": "user", "content": "你好"}]

    def test_add_message_appends(self):
        state = {}
        with patch("states.session.st.session_state", state):
            SessionState.add_message("user", "问题")
            SessionState.add_message("assistant", "回答")

        assert state["messages"] == [
            {"role": "user", "content": "问题"},
            {"role": "assistant", "content": "回答"},
        ]

    def test_clear_messages(self):
        state = {"messages": [{"role": "user", "content": "旧消息"}]}
        with patch("states.session.st.session_state", state):
            SessionState().clear_messages()

        assert state["messages"] == []
