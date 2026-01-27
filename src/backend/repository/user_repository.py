from typing import Optional
from sqlalchemy.orm import Session

from src.backend.repository.base_repository import BaseRepository
from src.backend.models.user import User


class UserRepository(BaseRepository[User]):
    """用户Repository"""

    def __init__(self, db: Session):
        super().__init__(User, db)

    def get_by_username(self, username: str) -> Optional[User]:
        """根据用户名获取用户"""
        return self.db.query(User).filter(User.username == username).first()

    def get_by_email(self, email: str) -> Optional[User]:
        """根据邮箱获取用户"""
        return self.db.query(User).filter(User.email == email).first()

    def create_user(
        self,
        username: str,
        email: str,
        hashed_password: str,
        full_name: str = None
    ) -> User:
        """创建新用户"""
        return self.create(
            username=username,
            email=email,
            hashed_password=hashed_password,
            full_name=full_name
        )
