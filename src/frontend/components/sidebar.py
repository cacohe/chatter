# src/frontend/components/sidebar.py
import streamlit as st
from src.frontend.api_client import backend_api_client
from src.frontend.state import state_manager


def _render_model_selector() -> None:
    st.subheader("模型配置")
    models = backend_api_client.get_available_models()
    if not models:
        st.warning("无可用模型")
        return

    selected = st.selectbox(
        "选择 AI 模型",
        options=models,
        index=0 if not st.session_state.current_model else models.index(st.session_state.current_model)
    )
    st.session_state.current_model = selected


def _render_history_list():
    st.caption("历史记录")
    for chat in backend_api_client.get_history():
        if st.button(f"💬 {chat['title'][:15]}", key=f"hist_{chat['id']}", use_container_width=True):
            # 加载历史逻辑
            pass


def render_sidebar():
    with st.sidebar:
        st.title("✨ Cacohe")
        if st.button("➕ 新对话", use_container_width=True, type="primary"):
            state_manager.clear_messages()
            st.rerun()

        st.divider()
        _render_model_selector()
        st.divider()
        _render_history_list()
