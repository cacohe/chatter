import uuid
from typing import List, Tuple, Optional
from src.backend.domain.repository_interfaces.chat import IChatRepository
from src.shared.schemas import chat as chat_schema
from src.backend.infra.db.supabase.client import create_supabase
from src.backend.domain.exceptions import BusinessException


class SupabaseChatRepository(IChatRepository):
    def __init__(self, client=None):
        # 注意：在生产环境下，建议通过构造函数注入 client 以便 Mock 测试
        self.client = client if client else create_supabase()
        self._table = "message"

    async def save_message(
        self, session_id: uuid.UUID, role: str, content: str
    ) -> chat_schema.ChatResponse:
        """
        保存消息并返回保存后的记录对象
        """
        data = {"session_id": str(session_id), "role": role, "content": content}
        # execute() 是同步阻塞的，在异步环境下如果使用了异步驱动则需 await
        # Supabase-py 目前主要提供同步调用，但在 FastAPI 中建议封装在线程池或使用其异步版本
        response = self.client.table(self._table).insert(data).execute()

        if not response.data:
            raise BusinessException("消息保存失败")

        return chat_schema.ChatResponse(**response.data[0])

    async def get_recent_messages(self, session_id: uuid.UUID, limit: int = 10):
        """
        获取最近的 N 条消息，用于 LLM 的上下文参考
        """
        response = (
            self.client.table(self._table)
            .select("*")
            .eq("session_id", str(session_id))
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )

        # 转换为列表并反转，因为 LLM 需要时间正序 [旧消息, ..., 新消息]
        messages = [chat_schema.ChatResponse(**item) for item in response.data]
        messages.reverse()
        return messages

    async def get_paged_messages(
        self, session_id: uuid.UUID, last_id: Optional[int], limit: int
    ) -> Tuple[List[chat_schema.ChatResponse], bool]:
        """
        分页查询逻辑：使用 ID 游标防止深分页性能问题
        """
        query = (
            self.client.table(self._table)
            .select("*")
            .eq("session_id", str(session_id))
            .order("id", desc=True)
            .limit(limit + 1)
        )  # 多取一条用来判断 has_more

        if last_id:
            query = query.lt("id", last_id)

        response = query.execute()
        raw_data = response.data

        has_more = len(raw_data) > limit
        items = raw_data[:limit]

        # 转换成 Schema 对象列表
        result_items = [chat_schema.ChatResponse(**item) for item in items]

        return result_items, has_more

    async def get_message_count(self, session_id: uuid.UUID) -> int:
        """获取会话的消息数量"""
        response = (
            self.client.table(self._table)
            .select("id", count="exact")
            .eq("session_id", str(session_id))
            .execute()
        )

        return response.count if response.count is not None else 0
