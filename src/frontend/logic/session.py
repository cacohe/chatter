import datetime
import uuid
from typing import Generator, Tuple

import streamlit as st

from src.frontend.services.api_client import backend_api_client
from src.frontend.states.session import session_state
from src.frontend.states.user import user_state
from src.shared.logger import logger
from src.shared.schemas import chat as chat_schema
from src.shared.schemas import session as session_schema
from src.shared.config import settings


class SessionLogic:
    @staticmethod
    def switch_model(model_id: str) -> Tuple[bool, str | None]:
        """切换模型
        Returns:
            Tuple of (success, error_message)
        """
        try:
            if not session_state.session_id:
                logger.warning("Cannot switch model: no active session_id")
                return (False, "没有活动的会话")
            if user_state.is_authenticated:
                response = backend_api_client.session.switch_model(
                    session_state.session_id, model_id
                )
                if response.status_code == 200:
                    session_state.current_model_id = model_id
                    logger.info(f"Switched model to {model_id} successfully.")
                    return (True, None)
                else:
                    error_msg = response.json().get("detail", "切换模型失败")
                    logger.error(
                        f"Error when switch model, Status Code: {response.status_code}, "
                        f"Message: {error_msg}"
                    )
                    return (False, error_msg)
            else:
                session_state.current_model_id = model_id
                logger.info(f"Switched model to {model_id} successfully.")
                return (True, None)
        except Exception as e:
            logger.exception(f"Exception when switch model: {e}")
            return (False, "切换模型失败，请稍后重试")

    @staticmethod
    def _add_message(role, content):
        session_state.add_message(role, content)

    @staticmethod
    def _create_session_id() -> uuid.UUID:
        if not user_state.is_authenticated:
            session_id = uuid.uuid4()
            session_state.session_id = session_id
            logger.info(
                f"Current user is not logged in. A random UUID will be used as the session ID: {session_id}"
            )
            return session_id
        else:
            response = backend_api_client.user.create_session()
            if response.status_code == 200:
                session_id = response.json().get("id")
                session_state.session_id = session_id
                logger.info(
                    f"New session id created successfully, session ID: {session_id}"
                )
                return uuid.UUID(session_id)
            else:
                logger.warn(
                    f"Error when create session id, Status Code: {response.status_code}, "
                    f"Message: {response.json().get('detail')}"
                )
                return uuid.uuid4()

    @staticmethod
    def _rename_session_title(session_id: uuid.UUID, content: str):
        title = content[:10] if len(content) > 10 else content
        user_state.rename_session(session_id, title)

        if user_state.is_authenticated:
            backend_api_client.user.rename_session(session_id, title)

    def _handle_new_session(self, content):
        if not session_state.session_id:
            logger.info(
                "Current conversation does not have a conversation ID. A conversation ID will be created."
            )
            session_id = self._create_session_id()
            session = session_schema.SessionRead(
                id=session_state.session_id,
                model_name=session_state.current_model_id,
                created_at=datetime.datetime.now(datetime.timezone.utc),
                updated_at=datetime.datetime.now(datetime.timezone.utc),
            ).model_dump()
            user_state.add_session(session)
            self._rename_session_title(session_id, content)

    def _get_history_for_api(self) -> list:
        """获取历史消息列表，用于传递给 API 实现记忆功能"""
        messages = session_state.messages
        if not messages:
            return []

        history = []
        max_history = (
            getattr(settings.llm_settings, "max_history_messages", 10)
            if hasattr(settings, "llm_settings")
            else 10
        )

        for msg in messages[-max_history:]:
            history.append(
                {
                    "session_id": str(session_state.session_id)
                    if session_state.session_id
                    else "",
                    "role": msg.get("role", "user"),
                    "content": msg.get("content", ""),
                }
            )
        return history

    def chat_non_stream(self, content) -> Tuple[str | None, str | None]:
        """发送消息并获取非流式响应
        Returns:
            Tuple of (response_content, error_message)
        """
        try:
            self._handle_new_session(content)

            self._add_message(role=chat_schema.MessageRole.USER, content=content)

            history = self._get_history_for_api()
            response = backend_api_client.session.chat_non_stream(
                session_id=session_state.session_id,
                content=content,
                model_id=session_state.current_model_id,
                history=history,
            )
            if response.status_code == 200:
                response_content = response.json().get("content")
                self._add_message(
                    role=chat_schema.MessageRole.ASSISTANT, content=response_content
                )
                return (response_content, None)
            else:
                error_msg = response.json().get("detail", "大模型调用失败")
                logger.error(
                    f"Error when get response from LLM, Status Code: {response.status_code}, "
                    f"Message: {error_msg}"
                )
                return (None, error_msg)
        except Exception as e:
            logger.exception(f"Exception when chat: {e}")
            return (None, "大模型调用失败，请稍后重试")

    def chat_stream(
        self, content
    ) -> Generator[Tuple[str | None, str | None], None, None]:
        """发送消息并获取流式响应
        Yields:
            Tuple of (chunk, error_message)
        """
        try:
            self._handle_new_session(content)

            history = self._get_history_for_api()
            response = backend_api_client.session.chat_stream(
                session_id=session_state.session_id,
                content=content,
                model_id=session_state.current_model_id,
                history=history,
            )
            if response.status_code == 200:
                for line in response.iter_lines():
                    if line:
                        decoded_line = line.decode("utf-8")
                        if decoded_line.startswith("data: "):
                            chunk = decoded_line[6:]
                            yield (chunk, None)
            else:
                error_msg = response.json().get("detail", "大模型调用失败")
                logger.error(
                    f"Error when chat stream, Status Code: {response.status_code}, "
                    f"Message: {error_msg}"
                )
                yield (None, error_msg)
        except Exception as e:
            logger.exception(f"Exception when stream chat: {e}")
            yield (None, "大模型调用失败，请稍后重试")


def get_session_logic():
    return SessionLogic()


session_logic = get_session_logic()
