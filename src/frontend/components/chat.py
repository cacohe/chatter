import streamlit as st

from src.frontend.logic.session import session_logic
from src.frontend.states.session import session_state
from src.shared.schemas import chat as chat_schema


def _render_chat_history():
    for msg in session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])


def _render_chat_content():
    _render_chat_history()

    prompt = st.chat_input("有什么想问的？", disabled=session_state.input_disabled)

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
                        full_response += chunk
                        response_placeholder.markdown(full_response)
            except Exception as e:
                st.error(f"请求失败: {str(e)}")

            if full_response:
                session_state.add_message(
                    role=chat_schema.MessageRole.USER, content=prompt
                )
                session_state.add_message(
                    role=chat_schema.MessageRole.ASSISTANT, content=full_response
                )
        st.session_state["_needs_rerun"] = True


def render_chat_interface():
    _render_chat_content()
