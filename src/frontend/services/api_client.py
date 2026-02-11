import streamlit as st

from src.frontend.services.user import user_client
from src.frontend.services.session import session_client


class BackendAPIClient:
    def __init__(self):
        self.user = user_client
        self.session = session_client


@st.cache_resource
def get_api_client():
    return BackendAPIClient()


# 导出全局单例
backend_api_client = get_api_client()