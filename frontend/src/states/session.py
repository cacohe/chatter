"""本页只保留 session_id；完整展示历史由后端保存，前端通过 API 拉取。"""

from uuid import uuid4

import streamlit as st


class SessionState:
    """会话标识。展示历史不放在前端，也不参与模型上下文。"""

    @property
    def session_id(self) -> str:
        sid = st.session_state.get("session_id")
        if not sid:
            sid = str(uuid4())
            st.session_state["session_id"] = sid
        return str(sid)

    def new_session(self) -> str:
        sid = str(uuid4())
        st.session_state["session_id"] = sid
        return sid


session_state = SessionState()
