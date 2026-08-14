"""Tests for SessionState."""

from unittest.mock import patch

from states.session import SessionState


class TestSessionState:
    def test_creates_session_id_once(self):
        state = {}
        session = SessionState()
        with patch("states.session.st.session_state", state):
            first = session.session_id
            second = session.session_id
        assert first == second
        assert state["session_id"] == first

    def test_new_session_replaces_id(self):
        state = {"session_id": "old"}
        session = SessionState()
        with patch("states.session.st.session_state", state):
            new_id = session.new_session()
        assert new_id != "old"
        assert state["session_id"] == new_id
