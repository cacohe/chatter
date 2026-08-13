"""页头标题。"""

from logger import logger


def render_header():
    """渲染页头。"""
    try:
        import streamlit as st

        st.header("知识库问答")
    except Exception as e:
        logger.exception(f"Exception when rendering header: {e}")
