import streamlit as st
from typing import List, Dict


class SessionManager:
    """封装所有状态读写逻辑，提高可维护性"""

    @staticmethod
    def init():
        defaults = {
            "messages": [],
            "current_model": None,
            "models": [],
            "is_processing": False
        }
        for key, val in defaults.items():
            if key not in st.session_state:
                st.session_state[key] = val

    @property
    def messages(self) -> List[Dict[str, str]]:
        return st.session_state.messages

    def add_message(self, role: str, content: str, **kwargs):
        msg = {"role": role, "content": content, **kwargs}
        st.session_state.messages.append(msg)

    def clear_messages(self):
        st.session_state.messages = []


# 实例化单例
state_manager = SessionManager()
