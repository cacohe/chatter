from src.backend.domain.repository_interfaces.chat import IChatRepository


class SQLAlchemyChatRepository(IChatRepository):
    def __init__(self, client=None):
        self.client = client

    async def get_messages_by_session(self, session_id: int) -> list:
        # TODO
        pass
