from logger import logger


def render_header():
    try:
        import streamlit as st

        st.header("知识库问答")
    except Exception as e:
        logger.exception(f"Exception when rendering header: {e}")
