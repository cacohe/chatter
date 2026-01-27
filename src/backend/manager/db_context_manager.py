from typing import List, Optional
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from sqlalchemy.orm import Session

from src.backend.repository.session_repository import SessionRepository
from src.backend.repository.message_repository import MessageRepository
from src.backend.models.message import MessageRole


class DBContextManager:
    """基于数据库的上下文管理器，支持持久化存储"""

    def __init__(self, db: Session, max_turns: int = 10):
        self.db = db
        self.max_turns = max_turns
        self.system_prompt = """你是一个有帮助的AI助手。请根据对话历史和当前问题提供准确、有用的回答。
        如果使用了工具获取了信息，请基于这些信息进行回答。"""

    def initialize_session(
        self,
        session_id: str,
        user_id: int,
        system_prompt: str = None,
        title: str = "新对话",
        model_name: str = "qwen"
    ):
        """初始化会话，在数据库中创建会话记录"""
        session_repo = SessionRepository(self.db)
        message_repo = MessageRepository(self.db)

        # 检查会话是否已存在
        existing_session = session_repo.get_by_session_id(session_id)
        if existing_session is None:
            # 创建新会话
            system_prompt = system_prompt or self.system_prompt
            db_session = session_repo.create_session(
                session_id=session_id,
                user_id=user_id,
                title=title,
                system_prompt=system_prompt,
                model_name=model_name
            )

            # 添加system消息
            message_repo.create_message(
                session_id=db_session.id,
                role=MessageRole.SYSTEM,
                content=system_prompt
            )
        else:
            # 更新会话配置
            session_repo.update_session(
                session_id=session_id,
                system_prompt=system_prompt or self.system_prompt
            )

    def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        model_used: str = None,
        temperature: str = None,
        tool_calls: str = None,
        tool_result: str = None
    ):
        """添加消息到会话，并持久化到数据库"""
        session_repo = SessionRepository(self.db)
        message_repo = MessageRepository(self.db)

        # 获取会话
        db_session = session_repo.get_by_session_id(session_id)
        if db_session is None:
            raise ValueError(f"Session {session_id} not found")

        # 映射角色
        role_map = {
            "human": MessageRole.USER,
            "user": MessageRole.USER,
            "ai": MessageRole.ASSISTANT,
            "assistant": MessageRole.ASSISTANT,
            "system": MessageRole.SYSTEM,
            "tool": MessageRole.TOOL
        }
        message_role = role_map.get(role.lower(), MessageRole.USER)

        # 创建消息
        message_repo.create_message(
            session_id=db_session.id,
            role=message_role,
            content=content,
            tool_calls=tool_calls,
            tool_result=tool_result,
            model_used=model_used,
            temperature=temperature
        )

        # 检查是否需要修剪历史消息（保留最近N轮）
        messages = message_repo.get_session_messages(db_session.id, limit=1000)
        # system消息不计入轮数
        system_count = sum(1 for m in messages if m.role == MessageRole.SYSTEM)
        conversation_messages = [m for m in messages if m.role != MessageRole.SYSTEM]

        if len(conversation_messages) > self.max_turns * 2:  # 1轮 = user + assistant
            # 删除最旧的消息（保留system和最近N轮）
            to_delete_count = len(conversation_messages) - self.max_turns * 2
            messages_to_delete = conversation_messages[:to_delete_count]
            for msg in messages_to_delete:
                self.db.delete(msg)
            self.db.commit()

    def get_messages(self, session_id: str) -> List[BaseMessage]:
        """获取会话消息历史，转换为LangChain消息格式"""
        session_repo = SessionRepository(self.db)
        message_repo = MessageRepository(self.db)

        # 获取会话
        db_session = session_repo.get_by_session_id(session_id)
        if db_session is None:
            # 如果会话不存在，返回空列表
            return []

        # 获取最近的消息
        db_messages = message_repo.get_session_messages(db_session.id)

        # 转换为LangChain消息格式
        messages = []
        for db_msg in db_messages:
            if db_msg.role == MessageRole.SYSTEM:
                messages.append(SystemMessage(content=db_msg.content))
            elif db_msg.role == MessageRole.USER:
                messages.append(HumanMessage(content=db_msg.content))
            elif db_msg.role == MessageRole.ASSISTANT:
                messages.append(AIMessage(content=db_msg.content))
            # TOOL类型的消息暂时不转换为LangChain格式

        return messages

    def get_session_info(self, session_id: str):
        """获取会话信息"""
        session_repo = SessionRepository(self.db)
        return session_repo.get_by_session_id(session_id)

    def clear_session(self, session_id: str):
        """清空会话历史，只保留system消息"""
        session_repo = SessionRepository(self.db)
        message_repo = MessageRepository(self.db)

        # 获取会话
        db_session = session_repo.get_by_session_id(session_id)
        if db_session is None:
            raise ValueError(f"Session {session_id} not found")

        # 删除所有非system消息
        messages = message_repo.get_session_messages(db_session.id)
        for msg in messages:
            if msg.role != MessageRole.SYSTEM:
                self.db.delete(msg)
        self.db.commit()

    def delete_session(self, session_id: str):
        """删除整个会话（包括所有消息）"""
        session_repo = SessionRepository(self.db)
        session_repo.delete_session(session_id)

    def get_user_sessions(self, user_id: int, skip: int = 0, limit: int = 100):
        """获取用户的所有会话"""
        session_repo = SessionRepository(self.db)
        return session_repo.get_user_sessions(user_id, skip=skip, limit=limit)
