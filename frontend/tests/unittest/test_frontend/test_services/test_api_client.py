"""Tests for BackendAPIClient."""

from services.api_client import BackendAPIClient
from services.chat import chat_client
from services.knowledge import knowledge_client


class TestBackendAPIClient:
    def test_exposes_chat_and_knowledge_clients(self):
        client = BackendAPIClient()
        assert client.chat is chat_client
        assert client.knowledge is knowledge_client
