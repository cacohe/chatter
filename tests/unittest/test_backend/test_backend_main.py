import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from src.backend.main import app, ChatRequest, ChatResponse


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def mock_controller():
    with patch('src.backend.main.AIChatController') as mock:
        yield mock


class TestMainApp:
    """测试主应用入口和API端点"""

    def test_app_initialization(self):
        """测试FastAPI应用是否正确初始化"""
        assert app is not None
        assert hasattr(app, 'title')
        assert app.title == "多模型AI聊天机器人"

    def test_chat_endpoint_success(self, client, mock_controller):
        """测试聊天端点成功响应"""
        # 设置mock返回值
        mock_instance = mock_controller.return_value
        mock_instance.process_message.return_value = {
            "response": "测试回复",
            "tools_used": False,
            "tool_result": "",
            "model_used": "qwen"
        }

        # 发送请求
        request_data = {
            "message": "你好",
            "session_id": "test_session",
            "use_tools": True
        }
        
        response = client.post("/chat", json=request_data)
        
        # 验证响应
        assert response.status_code == 200
        data = response.json()
        assert "response" in data
        assert "session_id" in data
        assert data["response"] == "测试回复"
        assert data["session_id"] == "test_session"

    def test_chat_endpoint_validation_error(self, client):
        """测试聊天端点输入验证错误"""
        # 发送不完整的请求数据
        request_data = {
            "message": "你好"
            # 缺少session_id和use_tools字段
        }
        
        response = client.post("/chat", json=request_data)
        
        # 验证响应状态码为422 (Unprocessable Entity)
        assert response.status_code == 422

    def test_models_endpoint(self, client, mock_controller):
        """测试获取模型列表端点"""
        # 设置mock返回值
        mock_instance = mock_controller.return_value
        mock_instance.get_available_models.return_value = ["qwen", "openai", "gemini"]

        response = client.get("/models")
        
        # 验证响应
        assert response.status_code == 200
        data = response.json()
        assert "models" in data
        assert data["models"] == ["qwen", "openai", "gemini"]

    def test_switch_model_endpoint_success(self, client, mock_controller):
        """测试切换模型端点成功响应"""
        # 设置mock返回值
        mock_instance = mock_controller.return_value
        mock_instance.switch_model.return_value = True

        response = client.post("/models/switch", json={"model_name": "openai"})
        
        # 验证响应
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_switch_model_endpoint_failure(self, client, mock_controller):
        """测试切换模型端点失败响应"""
        # 设置mock返回值
        mock_instance = mock_controller.return_value
        mock_instance.switch_model.return_value = False

        response = client.post("/models/switch", json={"model_name": "nonexistent_model"})
        
        # 验证响应
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False

    def test_tools_endpoint(self, client, mock_controller):
        """测试获取工具列表端点"""
        # 设置mock返回值
        mock_instance = mock_controller.return_value
        mock_instance.get_available_tools.return_value = [
            {"name": "web_search", "description": "搜索网络获取最新信息"},
            {"name": "weather", "description": "通过MCP调用weather功能"}
        ]

        response = client.get("/tools")
        
        # 验证响应
        assert response.status_code == 200
        data = response.json()
        assert "tools" in data
        assert len(data["tools"]) == 2
        assert data["tools"][0]["name"] == "web_search"

    def test_clear_session_endpoint(self, client, mock_controller):
        """测试清空会话端点"""
        # 设置mock返回值
        mock_instance = mock_controller.return_value
        # clear_conversation不返回任何值，所以不需要设置return_value

        response = client.post("/sessions/test_session/clear")
        
        # 验证响应
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_main_function(self):
        """测试main函数执行"""
        # 这个测试主要是确保main函数可以导入和执行而不抛出异常
        from src.backend.main import main
        # 使用mock来避免实际启动服务器
        with patch('src.backend.main.uvicorn.run') as mock_run:
            main()
            # 验证uvicorn.run被调用
            mock_run.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
