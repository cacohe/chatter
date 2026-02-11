from abc import ABC, abstractmethod
import uuid


class ISessionRepository(ABC):
    @abstractmethod
    async def create(self, user_id: uuid.UUID, title: str):
        pass

    @abstractmethod
    async def update_title(self, session_id: uuid.UUID, new_title: str):
        pass

    @abstractmethod
    async def update_session_model(self, session_id: uuid.UUID, model_id: str):
        pass

    @abstractmethod
    async def get_sessions_by_user(self, user_id: uuid.UUID):
        pass

    @abstractmethod
    async def delete_by_user(self, session_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        pass

    @abstractmethod
    async def get_session_by_id(self, session_id: uuid.UUID):
        pass
