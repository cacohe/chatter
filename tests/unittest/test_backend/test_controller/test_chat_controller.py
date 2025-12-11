import pytest
from unittest.mock import AsyncMock, Mock, patch
from src.backend.controller.chat_controller import AIChatController


@pytest.fixture
def controller():
    """创建AIChatController实例的fixture"""
    return AIChatController()


@pytest.fixture
def mock_managers(controller):
    """为controller中的manager创建mock对象"""
    # Mock ModelManager
    controller.model_manager = Mock()
    controller.model_manager.generate_response = AsyncMock()
    controller.model_manager.switch_model = Mock()
    controller.model_manager.list_available_models = Mock()
    controller.model_manager.current_model = "qwen"
    
    # Mock ToolManager
    controller.tool_manager = Mock()
    controller.tool_manager.execute_tool = AsyncMock()
    controller.tool_manager.list_tools = Mock()
    
    # Mock ContextManager
    controller.context_manager = Mock()
    controller.context_manager.add_message = Mock()
    controller.context_manager.get_messages = Mock()
    controller.context_manager.clear_session = Mock()
    
    return controller


class TestAIChatController:
    """测试AIChatController类"""

    def test_init(self, controller):
        """测试控制器初始化"""
        assert hasattr(controller, 'model_manager')
        assert hasattr(controller, 'tool_manager')
        assert hasattr(controller, 'context_manager')

    @pytest.mark.asyncio
    async def test_process_message_without_tools(self, mock_managers):
        """测试处理消息但不使用工具的情况"""
        # 设置mock返回值
        mock_managers.context_manager.get_messages.return_value = ["test_message"]
        mock_managers.model_manager.generate_response.return_value = "AI回复"
        
        # 调用方法
        result = await mock_managers.process_message("test_session", "你好", use_tools=False)
        
        # 验证调用
        mock_managers.context_manager.add_message.assert_called_with("test_session", "human", "你好")
        mock_managers.model_manager.generate_response.assert_awaited_once()
        mock_managers.context_manager.add_message.assert_called_with("test_session", "ai", "AI回复")
        
        # 验证返回值
        assert result["response"] == "AI回复"
        assert result["tools_used"] is False
        assert result["tool_result"] == ""
        assert result["model_used"] == "qwen"

    @pytest.mark.asyncio
    async def test_process_message_with_tools(self, mock_managers):
        """测试处理消息并使用工具的情况"""
        # 设置mock返回值
        mock_managers.context_manager.get_messages.return_value = ["test_message"]
        mock_managers.model_manager.generate_response.return_value = "基于工具结果的AI回复"
        mock_managers._needs_tool_assistance = Mock(return_value=True)
        mock_managers._handle_tool_calls = AsyncMock(return_value="工具调用结果")
        
        # 调用方法
        result = await mock_managers.process_message("test_session", "今天天气如何？", use_tools=True)
        
        # 验证调用
        mock_managers.context_manager.add_message.assert_any_call("test_session", "human", "今天天气如何？")
        mock_managers._handle_tool_calls.assert_awaited_once_with("今天天气如何？")
        mock_managers.model_manager.generate_response.assert_awaited_once()
        mock_managers.context_manager.add_message.assert_called_with("test_session", "ai", "基于工具结果的AI回复")
        
        # 验证返回值
        assert result["response"] == "基于工具结果的AI回复"
        assert result["tools_used"] is True
        assert result["tool_result"] == "工具调用结果"
        assert result["model_used"] == "qwen"

    def test_needs_tool_assistance_positive(self, mock_managers):
        """测试需要工具辅助的情况"""
        # 测试中文关键词
        assert mock_managers._needs_tool_assistance("今天天气怎么样？") is True
        assert mock_managers._needs_tool_assistance("请搜索相关信息") is True
        
        # 测试英文关键词
        assert mock_managers._needs_tool_assistance("What's the weather today?") is True
        assert mock_managers._needs_tool_assistance("Search for information") is True

    def test_needs_tool_assistance_negative(self, mock_managers):
        """测试不需要工具辅助的情况"""
        assert mock_managers._needs_tool_assistance("你好") is False
        assert mock_managers._needs_tool_assistance("今天很开心") is False

    @pytest.mark.asyncio
    async def test_handle_tool_calls_weather(self, mock_managers):
        """测试处理天气工具调用"""
        # 设置mock返回值
        mock_managers.tool_manager.execute_tool.return_value = "晴天，25度"
        
        # 调用方法
        result = await mock_managers._handle_tool_calls("今天天气怎么样？")
        
        # 验证调用
        mock_managers.tool_manager.execute_tool.assert_awaited_once_with("weather", "今天天气怎么样？")
        
        # 验证返回值
        assert "天气信息: 晴天，25度" in result

    @pytest.mark.asyncio
    async def test_handle_tool_calls_search(self, mock_managers):
        """测试处理搜索工具调用"""
        # 设置mock返回值
        mock_managers.tool_manager.execute_tool.return_value = "相关搜索结果"
        
        # 调用方法
        result = await mock_managers._handle_tool_calls("请搜索人工智能最新进展")
        
        # 验证调用
        mock_managers.tool_manager.execute_tool.assert_awaited_once_with("web_search", "请搜索人工智能最新进展")
        
        # 验证返回值
        assert "搜索结果: 相关搜索结果" in result

    def test_switch_model_success(self, mock_managers):
        """测试成功切换模型"""
        # 设置mock返回值
        mock_managers.model_manager.switch_model.return_value = True
        
        # 调用方法
        result = mock_managers.switch_model("openai")
        
        # 验证调用和返回值
        mock_managers.model_manager.switch_model.assert_called_once_with("openai")
        assert result is True

    def test_switch_model_failure(self, mock_managers):
        """测试切换模型失败"""
        # 设置mock返回值
        mock_managers.model_manager.switch_model.return_value = False
        
        # 调用方法
        result = mock_managers.switch_model("nonexistent_model")
        
        # 验证调用和返回值
        mock_managers.model_manager.switch_model.assert_called_once_with("nonexistent_model")
        assert result is False

    def test_get_available_models(self, mock_managers):
        """测试获取可用模型列表"""
        # 设置mock返回值
        mock_managers.model_manager.list_available_models.return_value = ["qwen", "openai", "gemini"]
        
        # 调用方法
        result = mock_managers.get_available_models()
        
        # 验证调用和返回值
        mock_managers.model_manager.list_available_models.assert_called_once()
        assert result == ["qwen", "openai", "gemini"]

    def test_get_available_tools(self, mock_managers):
        """测试获取可用工具列表"""
        # 设置mock返回值
        mock_managers.tool_manager.list_tools.return_value = [
            {"name": "web_search", "description": "搜索网络获取最新信息"},
            {"name": "weather", "description": "通过MCP调用weather功能"}
        ]
        
        # 调用方法
        result = mock_managers.get_available_tools()
        
        # 验证调用和返回值
        mock_managers.tool_manager.list_tools.assert_called_once()
        assert len(result) == 2
        assert result[0]["name"] == "web_search"

    def test_clear_conversation(self, mock_managers):
        """测试清空对话"""
        # 调用方法
        mock_managers.clear_conversation("test_session")
        
        # 验证调用
        mock_managers.context_manager.clear_session.assert_called_once_with("test_session")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])