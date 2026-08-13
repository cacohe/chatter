import streamlit as st

from logic.session import session_logic
from states.session import session_state


def _render_chat_history():
    for msg in session_state.messages:
        role = msg["role"]
        if hasattr(role, "value"):
            role = role.value
        with st.chat_message(str(role)):
            st.markdown(msg["content"])


def _render_chat_content():
    _render_chat_history()

    prompt = st.chat_input("基于知识库提问…")

    if prompt:
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            response_placeholder = st.empty()
            full_response = ""

            try:
                for chunk, error_msg in session_logic.chat_stream(content=prompt):
                    if error_msg:
                        st.error(error_msg)
                        break
                    if chunk:
                        if chunk.startswith("Error:"):
                            st.error(
                                chunk.removeprefix("Error:").strip() or "发生未知错误"
                            )
                            break
                        full_response += chunk
                        response_placeholder.markdown(full_response)
            except Exception as e:
                st.error(f"请求失败: {e!s}")

            if full_response:
                session_state.add_message(role="user", content=prompt)
                session_state.add_message(role="assistant", content=full_response)
        st.session_state["_needs_rerun"] = True


def render_chat_interface():
    _render_chat_content()
