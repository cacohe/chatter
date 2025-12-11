import pytest
from unittest.mock import Mock, patch, MagicMock
import os
from src.backend.manager.model_manager import ModelManager


class TestModelManager:
    """测试ModelManager类"""

    @patch.dict(os.environ, {"DASHSCOPE_API_KEY": "test_key"})
    @patch.dict(os.environ, {"OPENAI_API_KEY": "test_key"})
    @patch.dict(os.environ, {"GOOGLE_API_KEY": "test_key"})
    @patch('src.backend.manager.model_manager.ChatTongyi')
    @patch('src.backend.manager.model_manager.ChatOpenAI')
    @patch('src.backend.manager.model_manager.ChatGoogleGenerativeAI')
    @patch('src.backend.manager.model_manager.ChatOllama')
    def test_setup_models_all_available(self, mock_ollama, mock_gemini, mock_openai, mock_qwen):
        """测试所有模型都可用时的初始化"""
        # 设置mock返回值
        mock_qwen_instance = Mock()
        mock_qwen.return_value = mock_qwen_instance
        
        mock_openai_instance = Mock()
        mock_openai.return_value = mock_openai_instance
        
        mock_gemini_instance = Mock()
        mock_gemini.return_value = mock_gemini_instance
        
        mock_ollama_instance = Mock()
        mock_ollama.return_value = mock_ollama_instance
        
        # 创建ModelManager实例
        manager = ModelManager()
        
        # 验证各模型类被正确调用
        mock_qwen.assert_called_once_with(model="qwen-turbo", temperature=0.7)
        mock_openai.assert_any_call(model_name="gpt-3.5-turbo", temperature=0.7, streaming=True)
        mock_openai.assert_any_call(model_name="gpt-4", temperature=0.7, streaming=True)
        mock_gemini.assert_called_once_with(model="gemini-pro", temperature=0.7)
        assert mock_ollama.call_count == 2  # llama和mistral
        
        # 验证models字典中包含了所有模型
        expected_models = ["qwen", "openai", "openai-4", "gemini", "llama", "mistral"]
        for model in expected_models:
            assert model in manager.models
        
        # 验证默认模型
        assert manager.current_model == "qwen"

    @patch.dict(os.environ, {}, clear=True)  # 清除所有环境变量
    @patch('src.backend.manager.model_manager.ChatOllama')
    def test_setup_models_only_ollama(self, mock_ollama):
        """测试只有Ollama模型可用时的初始化"""
        # 设置mock返回值
        mock_ollama_instance = Mock()
        mock_ollama.return_value = mock_ollama_instance
        
        # 创建ModelManager实例
        manager = ModelManager()
        
        # 验证只调用了Ollama
        assert mock_ollama.call_count == 2
        
        # 验证models字典中只包含Ollama模型
        expected_models = ["llama", "mistral"]
        for model in expected_models:
            assert model in manager.models
            
        # 验证其他模型不存在
        unexpected_models = ["qwen", "openai", "openai-4", "gemini"]
        for model in unexpected_models:
            assert model not in manager.models

    def test_list_available_models(self):
        """测试获取可用模型列表"""
        manager = ModelManager()
        # 手动添加一些测试模型
        manager.models = {
            "qwen": Mock(),
            "openai": Mock(),
            "gemini": Mock()
        }
        
        # 调用方法
        result = manager.list_available_models()
        
        # 验证返回值
        assert isinstance(result, list)
        assert len(result) == 3
        assert "qwen" in result
        assert "openai" in result
        assert "gemini" in result

    def test_switch_model_success(self):
        """测试成功切换模型"""
        manager = ModelManager()
        # 设置测试模型
        manager.models = {
            "qwen": Mock(),
            "openai": Mock()
        }
        
        # 初始模型应为qwen
        assert manager.current_model == "qwen"
        
        # 切换到openai
        result = manager.switch_model("openai")
        
        # 验证切换成功
        assert result is True
        assert manager.current_model == "openai"

    def test_switch_model_failure(self):
        """测试切换到不存在的模型"""
        manager = ModelManager()
        # 设置测试模型
        manager.models = {
            "qwen": Mock(),
            "openai": Mock()
        }
        
        # 尝试切换到不存在的模型
        result = manager.switch_model("nonexistent")
        
        # 验证切换失败
        assert result is False
        # 当前模型应该不变
        assert manager.current_model == "qwen"

    def test_get_model_default(self):
        """测试获取当前模型"""
        manager = ModelManager()
        # 设置测试模型
        mock_model = Mock()
        manager.models = {
            "qwen": mock_model
        }
        manager.current_model = "qwen"
        
        # 获取模型
        result = manager.get_model()
        
        # 验证返回值
        assert result == mock_model

    def test_get_model_specific(self):
        """测试获取指定模型"""
        manager = ModelManager()
        # 设置测试模型
        mock_qwen = Mock()
        mock_openai = Mock()
        manager.models = {
            "qwen": mock_qwen,
            "openai": mock_openai
        }
        
        # 获取指定模型
        result = manager.get_model("openai")
        
        # 验证返回值
        assert result == mock_openai

    def test_get_model_nonexistent(self):
        """测试获取不存在的模型"""
        manager = ModelManager()
        # 设置测试模型
        manager.models = {
            "qwen": Mock()
        }
        
        # 获取不存在的模型
        result = manager.get_model("nonexistent")
        
        # 验证返回值
        assert result is None

    @pytest.mark.asyncio
    async def test_generate_response_success(self):
        """测试成功生成回复"""
        manager = ModelManager()
        # 设置测试模型
        mock_model = AsyncMock()
        mock_model.ainvoke = AsyncMock(return_value=MagicMock(content="AI回复"))
        manager.models = {
            "qwen": mock_model
        }
        manager.current_model = "qwen"
        
        # 调用方法
        result = await manager.generate_response(["测试消息"])
        
        # 验证调用和返回值
        mock_model.ainvoke.assert_awaited_once_with(["测试消息"])
        assert result == "AI回复"

    @pytest.mark.asyncio
    async def test_generate_response_no_model(self):
        """测试没有可用模型时生成回复"""
        manager = ModelManager()
        manager.models = {}  # 清空所有模型
        
        # 调用方法
        result = await manager.generate_response(["测试消息"])
        
        # 验证返回值
        assert result == "错误：没有可用的模型"

    @pytest.mark.asyncio
    async def test_generate_response_model_exception(self):
        """测试模型调用异常时生成回复"""
        manager = ModelManager()
        # 设置测试模型
        mock_model = AsyncMock()
        mock_model.ainvoke = AsyncMock(side_effect=Exception("模型调用失败"))
        mock_model.model_name = "test_model"
        manager.models = {
            "qwen": mock_model
        }
        manager.current_model = "qwen"
        
        # 调用方法
        result = await manager.generate_response(["测试消息"])
        
        # 验证返回值包含错误信息
        assert "模型调用失败" in result
        assert "test_model" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])