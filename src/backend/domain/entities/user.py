from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional


class User(BaseModel):
    id: str  # UUID from Supabase Auth
    email: EmailStr
    username: Optional[str] = None
    avatar_url: Optional[str] = None
    role: str = "user"
    created_at: datetime

    def is_admin(self) -> bool:
        return self.role == "admin"