import datetime
import uuid
from typing import Optional, AsyncGenerator, List
from src.backend.domain.repository_interfaces.chat import IChatRepository
from src.backend.domain.repository_interfaces.session import ISessionRepository
from src.shared.schemas import chat as chat_schema
from src.backend.domain.exceptions import BusinessException
from src.backend.infra.llm.factory import LLMFactory
from src.backend.infra.llm.registry import ModelRegistry
from src.backend.infra.llm.schema import LLMParameters, ChatMessage
from src.shared.config import settings
from src.shared.logger import logger


class ChatService:
    def __init__(self, chat_repo: IChatRepository, session_repo: ISessionRepository):
        self.chat_repo = chat_repo
        self.session_repo = session_repo

    @property
    def max_history_messages(self) -> int:
        """最大历史消息数，用于控制上下文长度"""
        return (
            getattr(settings, "llm_settings", None).max_history_messages
            if hasattr(settings, "llm_settings")
            else 10
        )

    async def _is_logged_in_user(self, request: chat_schema.ChatRequest) -> bool:
        try:
            session_id = request.session_id
            return bool(await self.session_repo.get_session_by_id(session_id))
        except Exception as e:
            logger.exception(f"Failed to get session {request.session_id}")
            raise e

    async def save_message(
        self, session_id: uuid.UUID, role: chat_schema.MessageRole, content: str
    ) -> chat_schema.ChatResponse:
        try:
            return await self.chat_repo.save_message(
                session_id=session_id, role=role, content=content
            )
        except Exception as e:
            logger.exception(f"Failed to add message to session {session_id}")
            raise e

    async def get_model_id_by_session_id(self, session_id: uuid.UUID) -> Optional[int]:
        session = await self.session_repo.get_session_by_id(session_id)

        if not session:
            logger.warning(
                f"No current session {session_id} was found. Using the default model."
            )
            return settings.llm_settings.default_llm

        return session.active_model_id

    async def get_llm(self, request: chat_schema.ChatRequest):
        model_id = request.model_id

        if not model_id:
            model_id = self.get_model_id_by_session_id(session_id=request.session_id)

        target_model = (
            model_id
            if ModelRegistry.exists(model_id)
            else settings.llm_settings.default_llm
        )

        llm = LLMFactory.get_instance(target_model)
        return llm

    async def get_conversation_history(
        self, session_id: uuid.UUID
    ) -> List[ChatMessage]:
        """获取对话历史消息，转换为 LLM 需要的格式"""
        try:
            recent_messages = await self.chat_repo.get_recent_messages(
                session_id=session_id, limit=self.max_history_messages
            )

            history = []
            for msg in recent_messages:
                role = (
                    "user" if msg.role == chat_schema.MessageRole.USER else "assistant"
                )
                history.append(ChatMessage(role=role, content=msg.content))

            return history
        except Exception as e:
            logger.warning(f"Failed to get conversation history: {e}")
            return []

    def _build_messages_with_history(
        self, current_content: str, history: List[ChatMessage]
    ) -> List[ChatMessage]:
        """将历史消息和当前消息组合成完整的消息列表"""
        messages = history + [ChatMessage(role="user", content=current_content)]
        return messages

    def _get_history_from_request(
        self, request: chat_schema.ChatRequest
    ) -> List[ChatMessage]:
        """从请求中获取历史消息，转换为 ChatMessage 格式"""
        if not request.history:
            return []

        history = []
        for msg in request.history:
            role = msg.role.value if hasattr(msg.role, "value") else str(msg.role)
            role = role.lower()
            if role not in ["user", "assistant"]:
                continue
            history.append(ChatMessage(role=role, content=msg.content))
        return history

    async def handle_chat(
        self, request: chat_schema.ChatRequest
    ) -> chat_schema.ChatResponse:
        """
        处理用户消息：保存用户消息 -> 调用 LLM -> 保存 AI 回复
        """
        try:
            is_logged_in = await self._is_logged_in_user(request)

            if is_logged_in:
                msg_count = await self.chat_repo.get_message_count(request.session_id)

                await self.save_message(
                    session_id=request.session_id,
                    role=chat_schema.MessageRole.USER,
                    content=request.content,
                )

                if msg_count == 0:
                    title = (
                        request.content[:10]
                        if len(request.content) > 10
                        else request.content
                    )
                    await self.session_repo.update_title(request.session_id, title)

            history = self._get_history_from_request(request)
            if not history:
                history = await self.get_conversation_history(request.session_id)

            llm = await self.get_llm(request)
            params = LLMParameters()
            messages = self._build_messages_with_history(request.content, history)
            ai_content = await llm.chat(messages=messages, params=params)

            ai_msg = None
            if is_logged_in:
                ai_msg = await self.save_message(
                    session_id=request.session_id,
                    role=chat_schema.MessageRole.ASSISTANT,
                    content=ai_content,
                )

            return chat_schema.ChatResponse(
                id=ai_msg.id if ai_msg else uuid.uuid4(),
                session_id=request.session_id,
                role=chat_schema.MessageRole.ASSISTANT,
                content=ai_content,
                created_at=datetime.datetime.now(datetime.timezone.utc),
            )

        except Exception as e:
            logger.exception(f"Chat processing failed for session {request.session_id}")
            raise BusinessException(f"聊天处理异常: {str(e)}")

    async def handle_chat_stream(
        self, request: chat_schema.ChatRequest
    ) -> AsyncGenerator[str, None]:
        """
        流式处理用户消息：保存用户消息 -> 流式调用 LLM -> 保存 AI 回复
        """
        is_logged_in = False
        try:
            is_logged_in = await self._is_logged_in_user(request)

            if is_logged_in:
                msg_count = await self.chat_repo.get_message_count(request.session_id)

                await self.save_message(
                    session_id=request.session_id,
                    role=chat_schema.MessageRole.USER,
                    content=request.content,
                )

                if msg_count == 0:
                    title = (
                        request.content[:10]
                        if len(request.content) > 10
                        else request.content
                    )
                    await self.session_repo.update_title(request.session_id, title)

            history = self._get_history_from_request(request)
            if not history:
                history = await self.get_conversation_history(request.session_id)

            llm = await self.get_llm(request)
            params = LLMParameters()
            messages = self._build_messages_with_history(request.content, history)

            full_content = ""
            async for chunk in llm.stream_chat(messages=messages, params=params):
                full_content += chunk
                yield chunk

            if is_logged_in and full_content:
                await self.save_message(
                    session_id=request.session_id,
                    role=chat_schema.MessageRole.ASSISTANT,
                    content=full_content,
                )

        except Exception as e:
            logger.exception(
                f"Chat stream processing failed for session {request.session_id}"
            )
            yield f"Error: {str(e)}"

    async def get_history(
        self,
        session_id: uuid.UUID,
        last_message_id: Optional[int] = None,
        limit: int = 20,
    ) -> chat_schema.HistoryResponse:
        """
        分页获取历史记录
        """
        try:
            # 调用仓储的分页查询方法
            items, has_more = await self.chat_repo.get_paged_messages(
                session_id=session_id, last_id=last_message_id, limit=limit
            )

            # 业务逻辑：确保前端显示顺序为时间正序
            items.sort(key=lambda x: x.id)

            new_last_id = items[0].id if items and has_more else None

            return chat_schema.HistoryResponse(
                items=items, has_more=has_more, last_message_id=new_last_id
            )

        except Exception as e:
            logger.exception(f"Failed to fetch history for session {session_id}")
            raise BusinessException(f"获取历史记录失败: {str(e)}")
