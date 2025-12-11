import pytest
from src.backend.manager.context_manager import ContextManager
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage


class TestContextManager:
    """测试ContextManager类"""

    def test_init(self):
        """测试初始化"""
        manager = ContextManager()
        assert manager.max_turns == 10
        assert isinstance(manager.sessions, dict)
        assert manager.system_prompt is not None

    def test_initialize_session_default_prompt(self):
        """测试使用默认系统提示初始化会话"""
        manager = ContextManager()
        session_id = "test_session"
        
        manager.initialize_session(session_id)
        
        # 验证会话已创建
        assert session_id in manager.sessions
        # 验证系统消息已添加
        messages = manager.sessions[session_id]
        assert len(messages) == 1
        assert isinstance(messages[0], SystemMessage)
        assert messages[0].content == manager.system_prompt

    def test_initialize_session_custom_prompt(self):
        """测试使用自定义系统提示初始化会话"""
        manager = ContextManager()
        session_id = "test_session"
        custom_prompt = "自定义系统提示"
        
        manager.initialize_session(session_id, custom_prompt)
        
        # 验证会话已创建
        assert session_id in manager.sessions
        # 验证自定义系统消息已添加
        messages = manager.sessions[session_id]
        assert len(messages) == 1
        assert isinstance(messages[0], SystemMessage)
        assert messages[0].content == custom_prompt

    def test_add_message_human(self):
        """测试添加人类消息"""
        manager = ContextManager()
        session_id = "test_session"
        message_content = "你好，AI！"
        
        # 先初始化会话
        manager.initialize_session(session_id)
        # 添加人类消息
        manager.add_message(session_id, "human", message_content)
        
        # 验证消息已添加
        messages = manager.sessions[session_id]
        assert len(messages) == 2  # 系统消息 + 人类消息
        assert isinstance(messages[1], HumanMessage)
        assert messages[1].content == message_content

    def test_add_message_ai(self):
        """测试添加AI消息"""
        manager = ContextManager()
        session_id = "test_session"
        message_content = "你好，人类！"
        
        # 先初始化会话
        manager.initialize_session(session_id)
        # 添加AI消息
        manager.add_message(session_id, "ai", message_content)
        
        # 验证消息已添加
        messages = manager.sessions[session_id]
        assert len(messages) == 2  # 系统消息 + AI消息
        assert isinstance(messages[1], AIMessage)
        assert messages[1].content == message_content

    def test_add_message_auto_initialize(self):
        """测试添加消息时自动初始化会话"""
        manager = ContextManager()
        session_id = "test_session"
        message_content = "你好，AI！"
        
        # 不手动初始化会话，直接添加消息
        manager.add_message(session_id, "human", message_content)
        
        # 验证会话已自动创建
        assert session_id in manager.sessions
        messages = manager.sessions[session_id]
        assert len(messages) == 2  # 系统消息 + 人类消息
        assert isinstance(messages[0], SystemMessage)
        assert isinstance(messages[1], HumanMessage)
        assert messages[1].content == message_content

    def test_get_messages(self):
        """测试获取会话消息"""
        manager = ContextManager()
        session_id = "test_session"
        
        # 初始化会话并添加消息
        manager.initialize_session(session_id)
        manager.add_message(session_id, "human", "你好")
        manager.add_message(session_id, "ai", "你好，有什么可以帮助你的吗？")
        
        # 获取消息
        messages = manager.get_messages(session_id)
        
        # 验证返回的消息
        assert len(messages) == 3  # 系统消息 + 人类消息 + AI消息
        assert isinstance(messages[0], SystemMessage)
        assert isinstance(messages[1], HumanMessage)
        assert isinstance(messages[2], AIMessage)

    def test_get_messages_nonexistent_session(self):
        """测试获取不存在会话的消息"""
        manager = ContextManager()
        session_id = "nonexistent_session"
        
        # 获取不存在会话的消息
        messages = manager.get_messages(session_id)
        
        # 应该返回空列表
        assert messages == []

    def test_trim_context_not_exceeded(self):
        """测试未超过最大轮数时不会修剪上下文"""
        manager = ContextManager(max_turns=3)
        session_id = "test_session"
        
        # 初始化会话
        manager.initialize_session(session_id)
        
        # 添加少量消息（未超过限制）
        for i in range(3):
            manager.add_message(session_id, "human", f"消息{i}")
            manager.add_message(session_id, "ai", f"回复{i}")
        
        # 验证消息数量
        messages = manager.sessions[session_id]
        assert len(messages) == 7  # 系统消息 + 3轮对话（每轮2条消息）

    def test_trim_context_exceeded(self):
        """测试超过最大轮数时修剪上下文"""
        manager = ContextManager(max_turns=2)
        session_id = "test_session"
        
        # 初始化会话
        manager.initialize_session(session_id)
        
        # 添加超过限制的消息
        for i in range(5):
            manager.add_message(session_id, "human", f"消息{i}")
            manager.add_message(session_id, "ai", f"回复{i}")
        
        # 验证消息数量是否被修剪到限制范围内
        messages = manager.sessions[session_id]
        # 应该保留系统消息 + 最近2轮对话（每轮2条消息）= 5条消息
        assert len(messages) == 5
        # 验证保留的是最近的消息
        assert messages[0].content == manager.system_prompt  # 系统消息
        assert messages[1].content == "消息3"  # 第4条人类消息
        assert messages[2].content == "回复3"  # 第4条AI回复
        assert messages[3].content == "消息4"  # 第5条人类消息
        assert messages[4].content == "回复4"  # 第5条AI回复

    def test_clear_session(self):
        """测试清空会话"""
        manager = ContextManager()
        session_id = "test_session"
        
        # 初始化会话并添加消息
        manager.initialize_session(session_id)
        manager.add_message(session_id, "human", "你好")
        manager.add_message(session_id, "ai", "你好，有什么可以帮助你的吗？")
        
        # 验证消息存在
        assert len(manager.sessions[session_id]) == 3
        
        # 清空会话
        manager.clear_session(session_id)
        
        # 验证只剩下系统消息
        messages = manager.sessions[session_id]
        assert len(messages) == 1
        assert isinstance(messages[0], SystemMessage)

    def test_clear_session_nonexistent(self):
        """测试清空不存在的会话"""
        manager = ContextManager()
        session_id = "nonexistent_session"
        
        # 尝试清空不存在的会话不应抛出异常
        manager.clear_session(session_id)
        
        # 会话不应被创建
        assert session_id not in manager.sessions


if __name__ == "__main__":
    pytest.main([__file__, "-v"])