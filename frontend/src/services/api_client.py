import streamlit as st
from services.chat import chat_client
from services.knowledge import knowledge_client


class BackendAPIClient:
    def __init__(self):
        self.chat = chat_client
        self.knowledge = knowledge_client


@st.cache_resource
def get_api_client():
    return BackendAPIClient()


backend_api_client = get_api_client()
