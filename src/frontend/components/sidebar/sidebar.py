import uuid
import streamlit as st

from src.frontend.components.sidebar.auth import show_authentication_dialog
from src.frontend.components.sidebar.user import show_user_profile_dialog
from src.frontend.logic.user import user_logic
from src.frontend.logic.session import session_logic
from src.frontend.states.user import user_state
from src.shared.config import settings
from src.shared.logger import logger
from src.shared.schemas import session as session_schema


def _render_new_session():
    if st.button(
        label="开启新对话",
        key="new_chat_btn",
        help="开始新对话",
        use_container_width=True,
    ):
        user_logic.create_session()
        st.rerun()


def _render_history_session():
    st.markdown("### 📚 历史对话")

    sessions = user_logic.get_history_sessions()

    if sessions:
        for session in sessions:
            if isinstance(session, session_schema.SessionRead):
                session = session.model_dump()
            session_id = session.get("id")
            session_title = session.get("title")
            with st.container():
                col1, col2 = st.columns([3, 1])
                with col1:
                    if st.button(
                        f"💬 {session_title}",
                        key=f"session_{session_id}",
                        use_container_width=True,
                    ):
                        st.session_state.session_id = session_id
                        st.rerun()
                with col2:
                    if st.button(
                        "🗑️", key=f"delete_{session_id}", use_container_width=True
                    ):
                        user_logic.delete_session(session_id)
                        st.rerun()
    else:
        st.markdown("暂无历史对话")


def _render_llm_settings():
    st.markdown("### ⚙️ 模型配置")
    models = user_logic.get_available_models()
    if models:
        model_options = {model["name"]: model["id"] for model in models}
        default_model_index = list(model_options.values()).index(
            settings.llm_settings.default_llm
        )
        selected_model = st.selectbox(
            "选择模型",
            list(model_options.keys()),
            index=default_model_index,
            key="current_model_display",
        )
        selected_model_id = model_options[selected_model]
        if selected_model_id != settings.llm_settings.default_llm:
            session_logic.switch_model(selected_model_id)

    else:
        st.markdown("暂无可用模型")


def _render_user_info():
    if not user_state.is_authenticated:
        button_label = "用户登录"
        if st.button(button_label, use_container_width=True):
            show_authentication_dialog()
    else:
        button_label = "用户中心"
        user_info = user_state.user_info
        if st.button(button_label, use_container_width=True):
            show_user_profile_dialog(user_info)


def render_sidebar():
    logger.info(f"rendering sidebar...")
    try:
        with st.sidebar:
            _render_user_info()

            st.markdown("---")
            _render_new_session()

            st.markdown("---")
            _render_llm_settings()

            st.markdown("---")
            _render_history_session()

        logger.info("Render sidebar successfully.")
    except Exception as e:
        logger.exception(f"Exception when rendering sidebar: {e}")
        st.markdown("### 侧边栏暂时不可用")
        st.markdown("请刷新页面重试，或联系管理员")
