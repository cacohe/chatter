import pytest
from unittest.mock import patch, Mock, MagicMock
import sys
import os

# 将src目录添加到Python路径中，以便正确导入
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'src'))

from src.frontend.main import initialize_session, main


class TestFrontendMain:
    """测试前端主应用"""

    @patch('src.frontend.main.st')
    def test_initialize_session(self, mock_st):
        """测试初始化会话状态"""
        # 设置初始session_state为空
        mock_st.session_state = {}
        
        # 调用函数
        initialize_session()
        
        # 验证session_state被正确初始化
        assert "session_id" in mock_st.session_state
        assert "messages" in mock_st.session_state
        assert "current_model" in mock_st.session_state
        assert mock_st.session_state["session_id"] is None
        assert mock_st.session_state["messages"] == []
        assert mock_st.session_state["current_model"] == "qwen"

    @patch('src.frontend.main.st')
    def test_initialize_session_partial_state(self, mock_st):
        """测试部分初始化的会话状态"""
        # 设置初始session_state包含部分键
        mock_st.session_state = {
            "session_id": "test_session"
        }
        
        # 调用函数
        initialize_session()
        
        # 验证已有键保持不变，缺失键被添加
        assert mock_st.session_state["session_id"] == "test_session"
        assert "messages" in mock_st.session_state
        assert "current_model" in mock_st.session_state
        assert mock_st.session_state["messages"] == []
        assert mock_st.session_state["current_model"] == "qwen"

    @patch('src.frontend.main.st')
    @patch('src.frontend.main.get_available_models')
    @patch('src.frontend.main.switch_model')
    @patch('src.frontend.main.send_message')
    def test_main_function_basic_flow(self, mock_send_message, mock_switch_model, mock_get_available_models, mock_st):
        """测试主函数基本执行流程"""
        # 设置mock返回值
        mock_get_available_models.return_value = ["qwen", "openai"]
        mock_switch_model.return_value = True
        mock_send_message.return_value = {
            "response": "AI回复",
            "tools_used": False,
            "model_used": "qwen",
            "session_id": "test_session"
        }
        
        # 设置st组件的mock
        mock_st.selectbox = Mock(return_value="qwen")  # 选择相同模型，不触发切换
        mock_st.checkbox = Mock(return_value=True)
        mock_st.button = Mock(return_value=False)  # 不点击清空按钮
        mock_st.chat_input = Mock(return_value=None)  # 没有用户输入
        
        # 设置session_state
        mock_st.session_state = {}
        
        # 调用main函数
        main()
        
        # 验证各函数被正确调用
        mock_get_available_models.assert_called_once()
        mock_st.set_page_config.assert_called_once()
        mock_st.title.assert_called_once()
        mock_st.selectbox.assert_called_once()
        mock_st.chat_input.assert_called_once()

    @patch('src.frontend.main.st')
    @patch('src.frontend.main.get_available_models')
    @patch('src.frontend.main.switch_model')
    def test_main_function_model_switch(self, mock_switch_model, mock_get_available_models, mock_st):
        """测试主函数中的模型切换功能"""
        # 设置mock返回值
        mock_get_available_models.return_value = ["qwen", "openai"]
        mock_switch_model.return_value = True
        
        # 设置st组件的mock
        mock_st.selectbox = Mock(return_value="openai")  # 选择不同模型，触发切换
        mock_st.checkbox = Mock(return_value=True)
        mock_st.button = Mock(return_value=False)
        mock_st.chat_input = Mock(return_value=None)
        mock_st.success = Mock()  # 成功提示
        
        # 设置session_state
        mock_st.session_state = {"current_model": "qwen"}
        
        # 调用main函数
        main()
        
        # 验证模型切换被调用
        mock_switch_model.assert_called_once_with("openai")
        mock_st.success.assert_called_once()

    @patch('src.frontend.main.st')
    @patch('src.frontend.main.get_available_models')
    @patch('src.frontend.main.switch_model')
    def test_main_function_model_switch_failure(self, mock_switch_model, mock_get_available_models, mock_st):
        """测试主函数中模型切换失败的情况"""
        # 设置mock返回值
        mock_get_available_models.return_value = ["qwen", "openai"]
        mock_switch_model.return_value = False  # 切换失败
        
        # 设置st组件的mock
        mock_st.selectbox = Mock(return_value="openai")
        mock_st.checkbox = Mock(return_value=True)
        mock_st.button = Mock(return_value=False)
        mock_st.error = Mock()  # 错误提示
        
        # 设置session_state
        mock_st.session_state = {"current_model": "qwen"}
        
        # 调用main函数
        main()
        
        # 验证错误提示被调用
        mock_st.error.assert_called_once()

    @patch('src.frontend.main.st')
    @patch('src.frontend.main.get_available_models')
    @patch('src.frontend.main.switch_model')
    @patch('src.frontend.main.requests.post')
    def test_main_function_clear_history(self, mock_requests_post, mock_switch_model, mock_get_available_models, mock_st):
        """测试主函数中的清空对话历史功能"""
        # 设置mock返回值
        mock_get_available_models.return_value = ["qwen", "openai"]
        mock_switch_model.return_value = True
        
        # 设置st组件的mock
        mock_st.selectbox = Mock(return_value="qwen")
        mock_st.checkbox = Mock(return_value=True)
        mock_st.button = Mock(return_value=True)  # 点击清空按钮
        mock_st.chat_input = Mock(return_value=None)
        mock_st.rerun = Mock()  # 重运行应用
        
        # 设置session_state
        mock_st.session_state = {
            "session_id": "test_session",
            "messages": [{"role": "user", "content": "你好"}],
            "current_model": "qwen"
        }
        
        # 调用main函数
        main()
        
        # 验证清空操作被执行
        mock_requests_post.assert_called_once()
        assert mock_st.session_state["messages"] == []
        assert mock_st.session_state["session_id"] is None
        mock_st.rerun.assert_called_once()

    @patch('src.frontend.main.st')
    @patch('src.frontend.main.get_available_models')
    @patch('src.frontend.main.switch_model')
    @patch('src.frontend.main.send_message')
    def test_main_function_user_input_processing(self, mock_send_message, mock_switch_model, mock_get_available_models, mock_st):
        """测试主函数中的用户输入处理"""
        # 设置mock返回值
        mock_get_available_models.return_value = ["qwen", "openai"]
        mock_switch_model.return_value = True
        mock_send_message.return_value = {
            "response": "AI回复",
            "tools_used": False,
            "model_used": "qwen",
            "session_id": "test_session"
        }
        
        # 设置st组件的mock
        mock_st.selectbox = Mock(return_value="qwen")
        mock_st.checkbox = Mock(return_value=True)
        mock_st.button = Mock(return_value=False)
        mock_st.chat_input = Mock(return_value="你好")  # 用户输入
        mock_st.spinner = Mock()
        mock_st.spinner.return_value.__enter__ = Mock()
        mock_st.spinner.return_value.__exit__ = Mock()
        
        # 设置session_state
        mock_st.session_state = {
            "messages": [],
            "session_id": None,
            "current_model": "qwen"
        }
        
        # 调用main函数
        main()
        
        # 验证消息处理流程
        mock_send_message.assert_called_once_with("你好", use_tools=True)
        # 验证消息被添加到历史中
        assert len(mock_st.session_state["messages"]) == 2  # 用户消息 + AI回复
        assert mock_st.session_state["messages"][0]["role"] == "user"
        assert mock_st.session_state["messages"][0]["content"] == "你好"
        assert mock_st.session_state["messages"][1]["role"] == "assistant"
        assert mock_st.session_state["messages"][1]["content"] == "AI回复"
        # 验证会话ID被设置
        assert mock_st.session_state["session_id"] == "test_session"

    @patch('src.frontend.main.st')
    @patch('src.frontend.main.get_available_models')
    @patch('src.frontend.main.switch_model')
    @patch('src.frontend.main.send_message')
    def test_main_function_send_message_failure(self, mock_send_message, mock_switch_model, mock_get_available_models, mock_st):
        """测试主函数中发送消息失败的情况"""
        # 设置mock返回值
        mock_get_available_models.return_value = ["qwen", "openai"]
        mock_switch_model.return_value = True
        mock_send_message.return_value = None  # 发送失败
        
        # 设置st组件的mock
        mock_st.selectbox = Mock(return_value="qwen")
        mock_st.checkbox = Mock(return_value=True)
        mock_st.button = Mock(return_value=False)
        mock_st.chat_input = Mock(return_value="你好")
        mock_st.spinner = Mock()
        mock_st.spinner.return_value.__enter__ = Mock()
        mock_st.spinner.return_value.__exit__ = Mock()
        mock_st.error = Mock()  # 错误提示
        
        # 设置session_state
        mock_st.session_state = {
            "messages": [],
            "session_id": None,
            "current_model": "qwen"
        }
        
        # 调用main函数
        main()
        
        # 验证错误提示被调用
        mock_st.error.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])