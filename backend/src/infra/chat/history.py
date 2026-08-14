"""对话的完整历史消息"""

from domain.models.chat import ChatMessage, MessageRole

_histories: dict[str, list[ChatMessage]] = {}


def get_history(session_id: str) -> list[ChatMessage]:
    return list(_histories.get(session_id) or [])


def append_history(session_id: str, messages: list[ChatMessage]) -> None:
    bucket = _histories.setdefault(session_id, [])
    for message in messages:
        if message.role not in {MessageRole.USER, MessageRole.ASSISTANT}:
            continue
        bucket.append(message)


def clear_history(session_id: str) -> None:
    _histories.pop(session_id, None)


def reset_histories() -> None:
    _histories.clear()
