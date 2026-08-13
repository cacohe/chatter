import streamlit as st


class SessionState:
    @property
    def messages(self) -> list[dict[str, str]]:
        return st.session_state.get("messages") or []

    @messages.setter
    def messages(self, value: list) -> None:
        st.session_state["messages"] = value

    @staticmethod
    def add_message(role: str, content: str, **kwargs) -> None:
        msg = {"role": role, "content": content, **kwargs}
        if "messages" not in st.session_state or st.session_state["messages"] is None:
            st.session_state["messages"] = []
        st.session_state["messages"].append(msg)

    def clear_messages(self) -> None:
        st.session_state["messages"] = []


session_state = SessionState()
