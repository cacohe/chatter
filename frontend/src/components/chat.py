"""主区聊天：展示历史通过 API 从后端获取，本页只负责渲染。"""

import streamlit as st

from logger import logger
from logic.session import session_logic


def _render_chat_history():
    try:
        messages = session_logic.load_display_history()
    except Exception as e:
        logger.exception(f"Failed to load display history: {e}")
        st.error("加载对话历史失败")
        return

    for msg in messages:
        role = msg.get("role")
        if hasattr(role, "value"):
            role = role.value
        with st.chat_message(str(role)):
            st.markdown(msg.get("content") or "")


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

        st.session_state["_needs_rerun"] = True


def render_chat_interface():
    """渲染主区问答界面。"""
    _render_chat_content()
