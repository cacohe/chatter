import pytest
from unittest.mock import patch, Mock
import sys
import os

# 将src目录添加到Python路径中，以便正确导入
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'src'))

from src.frontend.routes import get_available_models, switch_model, send_message


class TestFrontendRoutes:
    """测试前端路由函数"""

    @patch('src.frontend.routes.requests.get')
    def test_get_available_models_success(self, mock_get):
        """测试成功获取可用模型列表"""
        # 设置mock返回值
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"models": ["qwen", "openai", "gemini"]}
        mock_get.return_value = mock_response
        
        # 调用函数
        result = get_available_models()
        
        # 验证调用和返回值
        mock_get.assert_called_once()
        assert result == ["qwen", "openai", "gemini"]

    @patch('src.frontend.routes.requests.get')
    def test_get_available_models_failure(self, mock_get):
        """测试获取可用模型列表失败时返回默认值"""
        # 设置mock抛出异常
        mock_get.side_effect = Exception("网络错误")
        
        # 调用函数
        result = get_available_models()
        
        # 验证返回默认值
        assert result == ["openai", "gemini", "llama", "qwen"]

    @patch('src.frontend.routes.requests.get')
    def test_get_available_models_status_error(self, mock_get):
        """测试获取可用模型列表时HTTP状态码错误"""
        # 设置mock返回值
        mock_response = Mock()
        mock_response.status_code = 500  # 服务器错误
        mock_get.return_value = mock_response
        
        # 调用函数
        result = get_available_models()
        
        # 验证返回默认值
        assert result == ["openai", "gemini", "llama", "qwen"]

    @patch('src.frontend.routes.requests.post')
    def test_switch_model_success(self, mock_post):
        """测试成功切换模型"""
        # 设置mock返回值
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        # 调用函数
        result = switch_model("openai")
        
        # 验证调用和返回值
        mock_post.assert_called_once()
        assert result is True

    @patch('src.frontend.routes.requests.post')
    def test_switch_model_failure(self, mock_post):
        """测试切换模型失败"""
        # 设置mock返回值
        mock_response = Mock()
        mock_response.status_code = 500  # 服务器错误
        mock_post.return_value = mock_response
        
        # 调用函数
        result = switch_model("openai")
        
        # 验证返回值
        assert result is False

    @patch('src.frontend.routes.requests.post')
    def test_switch_model_exception(self, mock_post):
        """测试切换模型时发生异常"""
        # 设置mock抛出异常
        mock_post.side_effect = Exception("网络错误")
        
        # 调用函数
        result = switch_model("openai")
        
        # 验证返回值
        assert result is False

    @patch('src.frontend.routes.st')
    @patch('src.frontend.routes.requests.post')
    def test_send_message_success(self, mock_post, mock_st):
        """测试成功发送消息"""
        # 设置mock返回值
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "response": "AI回复",
            "session_id": "test_session",
            "tools_used": False,
            "model_used": "qwen"
        }
        mock_post.return_value = mock_response
        
        # 设置session_state
        class MockSessionState:
            def __init__(self):
                self.session_id = "test_session"
                
        mock_st.session_state = MockSessionState()
        
        # 调用函数
        result = send_message("你好", use_tools=True)
        
        # 验证调用和返回值
        mock_post.assert_called_once()
        assert result["response"] == "AI回复"
        assert result["session_id"] == "test_session"

    @patch('src.frontend.routes.st')
    @patch('src.frontend.routes.requests.post')
    def test_send_message_failure(self, mock_post, mock_st):
        """测试发送消息失败"""
        # 设置mock返回值
        mock_response = Mock()
        mock_response.status_code = 500  # 服务器错误
        mock_post.return_value = mock_response
        
        # 设置session_state
        class MockSessionState:
            def __init__(self):
                self.session_id = "test_session"
                
        mock_st.session_state = MockSessionState()
        
        # 调用函数
        result = send_message("你好", use_tools=True)
        
        # 验证返回值
        assert result is None

    @patch('src.frontend.routes.st')
    @patch('src.frontend.routes.requests.post')
    def test_send_message_exception(self, mock_post, mock_st):
        """测试发送消息时发生异常"""
        # 设置mock抛出异常
        mock_post.side_effect = Exception("网络错误")
        
        # 设置session_state
        class MockSessionState:
            def __init__(self):
                self.session_id = "test_session"
                
        mock_st.session_state = MockSessionState()
        
        # 调用函数
        result = send_message("你好", use_tools=True)
        
        # 验证返回值包含错误信息
        assert "error" in result
        assert "Failed to send message to API" in result["error"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])