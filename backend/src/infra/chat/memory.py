"""对话的短期记忆"""

from domain.models.chat import ChatMessage, MessageRole
from infra.config import settings

_sessions: dict[str, list[ChatMessage]] = {}


def get_messages(session_id: str) -> list[ChatMessage]:
    return list(_sessions.get(session_id) or [])


def append_messages(session_id: str, messages: list[ChatMessage]) -> None:
    bucket = _sessions.setdefault(session_id, [])
    for message in messages:
        if message.role not in {MessageRole.USER, MessageRole.ASSISTANT}:
            continue
        bucket.append(message)
    limit = settings.llm_settings.max_history_messages
    if len(bucket) > limit:
        del bucket[:-limit]


def clear_session(session_id: str) -> None:
    _sessions.pop(session_id, None)


def reset_memory() -> None:
    _sessions.clear()
