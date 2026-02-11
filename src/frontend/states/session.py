import streamlit as st
from typing import List, Dict, Optional

import uuid

from src.shared.config import settings


class SessionState:
    @property
    def session_id(self) -> Optional[uuid.UUID]:
        return (
            st.session_state.get("session_id")
            if st.session_state.get("session_id")
            else None
        )

    @session_id.setter
    def session_id(self, session_id: uuid.UUID) -> None:
        st.session_state["session_id"] = session_id

    @property
    def session_name(self) -> str:
        return (
            str(st.session_state.get("session_name"))
            if st.session_state.get("session_name")
            else "default-session-name"
        )

    @session_name.setter
    def session_name(self, value: str) -> None:
        st.session_state["session_name"] = value

    @property
    def current_model_id(self) -> str:
        return (
            str(st.session_state.get("current_model_id"))
            if st.session_state.get("current_model_id")
            else settings.llm_settings.default_llm
        )

    @current_model_id.setter
    def current_model_id(self, value: str) -> None:
        st.session_state["current_model_id"] = value

    @property
    def messages(self) -> List[Dict[str, str]]:
        return (
            st.session_state.get("messages") if st.session_state.get("messages") else []
        )

    @messages.setter
    def messages(self, value: List) -> None:
        st.session_state["messages"] = value

    @staticmethod
    def add_message(role: str, content: str, **kwargs) -> None:
        msg = {"role": role, "content": content, **kwargs}
        if not st.session_state.get("messages"):
            st.session_state["messages"] = []
        st.session_state.get("messages").append(msg)

    @property
    def is_processing(self) -> bool:
        return (
            st.session_state.get("is_processing")
            if st.session_state.get("is_processing")
            else False
        )

    @is_processing.setter
    def is_processing(self, value: bool) -> None:
        st.session_state["is_processing"] = value

    @property
    def input_disabled(self) -> bool:
        return self.is_processing


session_state = SessionState()
