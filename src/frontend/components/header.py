import streamlit as st

from src.shared.logger import logger


def render_header():
    """渲染页面头部"""
    try:
        st.header('✨Caco')
        # TODO: add session title
    except Exception as e:
        logger.exception(f'Exception when rendering header: {e}')
