"""Streamlit 入口：页头、侧边栏知识库、主区聊天。"""

import streamlit as st

from components.chat import render_chat_interface
from components.header import render_header
from components.sidebar.sidebar import render_sidebar
from components.utils import show_error_info
from logger import logger

st.set_page_config(page_title="知识库问答", layout="wide")


def main():
    try:
        # 子组件通过该标记请求整页刷新（开启新聊天、聊天流式结束后的历史对账）
        st.session_state["_needs_rerun"] = False

        render_header()
        render_sidebar()
        render_chat_interface()

        if st.session_state["_needs_rerun"]:
            st.rerun()

    except Exception as e:
        logger.exception(f"Exception: {e}")
        show_error_info()


if __name__ == "__main__":
    main()
