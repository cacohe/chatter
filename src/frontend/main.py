import streamlit as st

from src.frontend.components.chat import render_chat_interface
from src.frontend.components.header import render_header
from src.frontend.components.sidebar.sidebar import render_sidebar
from src.frontend.components.utils import show_error_info
from src.shared.logger import logger


st.set_page_config(page_title="Caco", layout="wide")


def main():
    try:
        render_header()
        render_sidebar()
        render_chat_interface()
    except Exception as e:
        logger.exception(f"Exception: {e}")
        show_error_info()


if __name__ == "__main__":
    main()
