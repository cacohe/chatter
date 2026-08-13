"""聚合聊天与知识库客户端，页面只依赖这一个入口。"""

from services.chat import ChatClient, chat_client
from services.knowledge import KnowledgeClient, knowledge_client


class BackendAPIClient:
    @property
    def chat(self) -> ChatClient:
        return chat_client

    @property
    def knowledge(self) -> KnowledgeClient:
        return knowledge_client


backend_api_client = BackendAPIClient()
