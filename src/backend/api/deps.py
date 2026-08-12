from src.backend.app.services.chat import ChatService


def get_chat_service() -> ChatService:
    return ChatService()


def get_knowledge_service():
    from src.backend.app.services.knowledge import KnowledgeService

    return KnowledgeService()
