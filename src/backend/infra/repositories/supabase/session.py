import uuid
from typing import List, Optional
from src.backend.domain.repository_interfaces.session import ISessionRepository
from src.backend.domain.entities.session import Session
from src.backend.infra.db.supabase.client import create_supabase
from src.backend.domain.exceptions import BusinessException
from src.shared.config import settings
from src.shared.logger import logger


class SupabaseSessionRepository(ISessionRepository):
    def __init__(self, client=None):
        self.client = client if client else create_supabase()
        self._table = "chat_session"

    def _map_to_entity(self, data: dict) -> Session:
        """内部转换函数：处理数据库 dict 到 Entity 的映射"""
        return Session(
            id=data["id"],
            user_id=data.get("user_id"),
            title=data.get("title", "新对话"),
            model_name=data.get("model_name", "qwen"),
            created_at=data["created_at"],
            updated_at=data["updated_at"],
        )

    async def create(self, user_id: uuid.UUID, title: str) -> Session:
        """创建新会话"""
        data = {
            "user_id": str(user_id),
            "title": title,
            "model_name": settings.llm_settings.default_llm,  # 初始默认模型
        }
        response = self.client.table(self._table).insert(data).execute()

        if not response.data:
            logger.error(f"create session error: {response.data}")
            raise BusinessException("创建会话记录失败")

        return self._map_to_entity(response.data[0])

    async def update_title(self, session_id: uuid.UUID, new_title: str) -> bool:
        """更新会话标题"""
        response = (
            self.client.table(self._table)
            .update({"title": new_title})
            .eq("id", str(session_id))
            .execute()
        )

        return len(response.data) > 0

    async def update_session_model(self, session_id: uuid.UUID, model_id: str) -> bool:
        """切换会话当前使用的 LLM 模型"""
        response = (
            self.client.table(self._table)
            .update({"model_name": model_id})
            .eq("id", str(session_id))
            .execute()
        )

        return len(response.data) > 0

    async def get_sessions_by_user(self, user_id: uuid.UUID) -> List[Session]:
        """获取用户的所有会话，按更新时间倒序"""
        response = (
            self.client.table(self._table)
            .select("*")
            .eq("user_id", str(user_id))
            .order("updated_at", desc=True)
            .execute()
        )

        return [self._map_to_entity(item) for item in response.data]

    async def get_session_by_id(self, session_id: uuid.UUID) -> Optional[Session]:
        """通过 ID 获取单个会话实体"""
        response = (
            self.client.table(self._table)
            .select("*")
            .eq("id", str(session_id))
            .maybe_single()
            .execute()
        )

        if not response or not response.data:
            return None

        return self._map_to_entity(response.data)

    async def delete_by_user(self, session_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        """
        带所有权校验的物理删除。
        安全核心：必须同时匹配 session_id 和 user_id。
        """
        response = (
            self.client.table(self._table)
            .delete()
            .eq("id", str(session_id))
            .eq("user_id", str(user_id))
            .execute()
        )

        # 如果返回的 data 为空，说明没有匹配到（可能是 ID 错或用户不对）
        return len(response.data) > 0
