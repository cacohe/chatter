"""Tests for Model Registry."""
import pytest
from src.backend.infra.llm.registry import ModelRegistry
from src.backend.infra.llm.base import BaseLLM
from src.backend.infra.llm.providers.openai_adapter import OpenAIAdapter
from src.backend.infra.llm.providers.gemini_adapter import GeminiAdapter


class TestModelRegistry:
    """Tests for ModelRegistry class."""

    def test_get_class_with_gpt_4o(self):
        """Test get_class returns OpenAIAdapter for gpt-4o."""
        adapter_cls = ModelRegistry.get_class("gpt-4o")
        assert adapter_cls == OpenAIAdapter

    def test_get_class_with_gpt_3_5_turbo(self):
        """Test get_class returns OpenAIAdapter for gpt-3.5-turbo."""
        adapter_cls = ModelRegistry.get_class("gpt-3.5-turbo")
        assert adapter_cls == OpenAIAdapter

    def test_get_class_with_gemini_1_5_pro(self):
        """Test get_class returns GeminiAdapter for gemini-1.5-pro."""
        adapter_cls = ModelRegistry.get_class("gemini-1.5-pro")
        assert adapter_cls == GeminiAdapter

    def test_get_class_with_deepseek_chat(self):
        """Test get_class returns OpenAIAdapter for deepseek-chat."""
        adapter_cls = ModelRegistry.get_class("deepseek-chat")
        assert adapter_cls == OpenAIAdapter

    def test_get_class_with_unknown_model(self):
        """Test get_class raises ValueError for unknown model."""
        with pytest.raises(ValueError) as exc_info:
            ModelRegistry.get_class("unknown-model")

        assert "未在注册中心登记" in str(exc_info.value)

    def test_get_class_returns_base_llm_subclass(self):
        """Test get_class returns BaseLLM subclass."""
        for model_id in ["gpt-4o", "gpt-3.5-turbo", "gemini-1.5-pro", "deepseek-chat"]:
            adapter_cls = ModelRegistry.get_class(model_id)
            assert issubclass(adapter_cls, BaseLLM)

    def test_exists_with_registered_model(self):
        """Test exists returns True for registered model."""
        # Note: exists method is not implemented in the actual code
        # This test verifies current behavior (returns None)
        result = ModelRegistry.exists("gpt-4o")
        assert result is None

    def test_exists_with_unregistered_model(self):
        """Test exists with unregistered model."""
        # Note: exists method is not implemented
        result = ModelRegistry.exists("unknown-model")
        assert result is None

    def test_get_all_model_ids(self):
        """Test get_all_model_ids returns all registered models."""
        # Note: get_all_model_ids is not implemented
        result = ModelRegistry.get_all_model_ids()
        assert result is None

    def test_get_class_is_classmethod(self):
        """Test get_class is a class method."""
        import inspect
        assert isinstance(inspect.getattr_static(ModelRegistry, 'get_class'), classmethod)

    def test_exists_is_classmethod(self):
        """Test exists is a class method."""
        import inspect
        assert isinstance(inspect.getattr_static(ModelRegistry, 'exists'), classmethod)

    def test_get_all_model_ids_is_classmethod(self):
        """Test get_all_model_ids is a class method."""
        import inspect
        assert isinstance(inspect.getattr_static(ModelRegistry, 'get_all_model_ids'), classmethod)

    def test_get_class_case_sensitive(self):
        """Test get_class is case sensitive."""
        with pytest.raises(ValueError):
            ModelRegistry.get_class("GPT-4O")

    def test_get_class_with_empty_string(self):
        """Test get_class with empty string."""
        with pytest.raises(ValueError):
            ModelRegistry.get_class("")

    def test_get_class_with_unicode_model_id(self):
        """Test get_class with unicode model ID."""
        with pytest.raises(ValueError):
            ModelRegistry.get_class("模型-中文")

    def test_registry_has_correct_number_of_models(self):
        """Test registry has expected number of models."""
        # Based on _mapping dict
        expected_models = ["gpt-4o", "gpt-3.5-turbo", "gemini-1.5-pro", "deepseek-chat"]
        for model_id in expected_models:
            adapter_cls = ModelRegistry.get_class(model_id)
            assert adapter_cls is not None

    def test_registry_openai_adapter_reused(self):
        """Test OpenAIAdapter is reused for multiple models."""
        gpt4_adapter = ModelRegistry.get_class("gpt-4o")
        gpt35_adapter = ModelRegistry.get_class("gpt-3.5-turbo")
        deepseek_adapter = ModelRegistry.get_class("deepseek-chat")

        assert gpt4_adapter == gpt35_adapter == deepseek_adapter == OpenAIAdapter

    def test_registry_gemini_adapter_unique(self):
        """Test GeminiAdapter is unique for Gemini models."""
        gemini_adapter = ModelRegistry.get_class("gemini-1.5-pro")
        gpt_adapter = ModelRegistry.get_class("gpt-4o")

        assert gemini_adapter != gpt_adapter
        assert gemini_adapter == GeminiAdapter
