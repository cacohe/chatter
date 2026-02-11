import uuid

from src.backend.domain.repository_interfaces.session import ISessionRepository
from src.shared.schemas import session as session_schema
from src.backend.domain.exceptions import BusinessException
from src.shared.schemas.session import SessionListResponse
from src.shared.logger import logger


class SessionService:
    def __init__(self, session_repo: ISessionRepository):
        self.session_repo = session_repo

    async def create_session(self, user_id: uuid.UUID) -> session_schema.SessionRead:
        try:
            # 业务逻辑：可以设置默认标题
            default_title = "新对话"
            new_session = await self.session_repo.create(
                user_id=user_id, title=default_title
            )
            return session_schema.SessionRead(**new_session.dict())
        except Exception:
            logger.exception("Failed to create session")
            raise BusinessException("创建会话失败")

    async def rename_session(self, session_id: uuid.UUID, new_title: str) -> bool:
        # 业务规则：标题不能为空或只有空格且不能过长
        if not new_title or not new_title.strip() or len(new_title) > 50:
            raise BusinessException("标题长度不合法")

        try:
            success = await self.session_repo.update_title(session_id, new_title)
            if not success:
                raise BusinessException("会话不存在或重命名失败")
            return True
        except BusinessException:
            raise
        except Exception:
            logger.exception("Failed to rename session")
            raise BusinessException("会话不存在或重命名失败")

    async def get_history(self, user_id: uuid.UUID) -> SessionListResponse:
        """获取该用户的所有历史会话列表"""
        sessions = await self.session_repo.get_sessions_by_user(user_id)
        return SessionListResponse(
            sessions=[session_schema.SessionRead(**s.dict()) for s in sessions],
            total_count=len(sessions),
        )

    async def delete_session(self, session_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        try:
            success = await self.session_repo.delete_by_user(session_id, user_id)
            if not success:
                raise BusinessException("删除失败，会话可能已被删除")
            return True
        except BusinessException:
            raise
        except Exception:
            logger.exception("Failed to delete session")
            raise BusinessException("删除失败，会话可能已被删除")
