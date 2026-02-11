import uuid
from datetime import datetime

from pydantic import BaseModel


class Session(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    title: str
    model_name: str
    created_at: datetime
    updated_at: datetime

    def is_owned_by(self, user_id: uuid.UUID) -> bool:
        return self.user_id == user_id

    def get_display_title(self) -> str:
        return self.title if self.title else "未命名会话"