import datetime
import uuid
from typing import Optional, AsyncGenerator
from src.backend.domain.repository_interfaces.chat import IChatRepository
from src.backend.domain.repository_interfaces.session import ISessionRepository
from src.shared.schemas import chat as chat_schema
from src.backend.domain.exceptions import BusinessException
from src.backend.infra.llm.factory import LLMFactory
from src.backend.infra.llm.registry import ModelRegistry
from src.backend.infra.llm.schema import LLMParameters
from src.shared.config import settings
from src.shared.logger import logger


class ChatService:
    def __init__(self, chat_repo: IChatRepository, session_repo: ISessionRepository):
        self.chat_repo = chat_repo
        self.session_repo = session_repo

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
            # 如果前端没传，去数据库查这个 session 绑定的模型
            model_id = self.get_model_id_by_session_id(session_id=request.session_id)

        # 校验该模型是否在注册中心
        target_model = (
            model_id
            if ModelRegistry.exists(model_id)
            else settings.llm_settings.default_llm
        )

        llm = LLMFactory.get_instance(target_model)
        return llm

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

            llm = await self.get_llm(request)
            params = LLMParameters()
            ai_content = await llm.chat(messages=request.content, params=params)

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

            llm = await self.get_llm(request)
            params = LLMParameters()

            full_content = ""
            async for chunk in llm.stream_chat(messages=request.content, params=params):
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
