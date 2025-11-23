from typing import Dict, List
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from collections import defaultdict


class ContextManager:
    """管理对话上下文和会话状态"""

    def __init__(self, max_turns: int = 10):
        self.sessions: Dict[str, List[BaseMessage]] = defaultdict(list)
        self.max_turns = max_turns
        self.system_prompt = """你是一个有帮助的AI助手。请根据对话历史和当前问题提供准确、有用的回答。
        如果使用了工具获取了信息，请基于这些信息进行回答。"""

    def initialize_session(self, session_id: str, system_prompt: str = None):
        """初始化会话"""
        if system_prompt is None:
            system_prompt = self.system_prompt

        self.sessions[session_id] = [SystemMessage(content=system_prompt)]

    def add_message(self, session_id: str, role: str, content: str):
        """添加消息到会话"""
        if session_id not in self.sessions:
            self.initialize_session(session_id)

        if role == "human":
            message = HumanMessage(content=content)
        else:
            message = AIMessage(content=content)

        self.sessions[session_id].append(message)
        self._trim_context(session_id)

    def get_messages(self, session_id: str) -> List[BaseMessage]:
        """获取会话消息历史"""
        return self.sessions.get(session_id, [])

    def _trim_context(self, session_id: str):
        """修剪上下文，保持最近对话"""
        if len(self.sessions[session_id]) > self.max_turns * 2 + 1:  # 包括system message
            # 保留system message和最近对话
            self.sessions[session_id] = (
                    [self.sessions[session_id][0]] +
                    self.sessions[session_id][-self.max_turns * 2:]
            )

    def clear_session(self, session_id: str):
        """清空会话历史"""
        if session_id in self.sessions:
            system_msg = self.sessions[session_id][0]
            self.sessions[session_id] = [system_msg]
