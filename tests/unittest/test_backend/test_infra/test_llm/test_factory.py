"""Tests for LLM Factory."""
import pytest
from unittest.mock import Mock, patch, MagicMock
from src.backend.infra.llm.factory import LLMFactory


class TestLLMFactory:
    """Tests for LLMFactory class."""

    def test_get_instance_with_gpt_model(self):
        """Test get_instance with GPT model."""
        with patch('src.backend.infra.llm.factory.ModelRegistry') as mock_registry, \
             patch('src.backend.infra.llm.factory.settings') as mock_settings:
            mock_adapter_cls = Mock(return_value=MagicMock())
            mock_registry.get_class.return_value = mock_adapter_cls
            mock_settings.openai = MagicMock()
            mock_settings.openai.api_key = "openai-key"

            result = LLMFactory.get_instance("gpt-4o")

            assert result is not None
            mock_adapter_cls.assert_called_once_with(
                model_id="gpt-4o",
                api_key="openai-key"
            )

    def test_get_instance_with_gemini_model(self):
        """Test get_instance with Gemini model."""
        with patch('src.backend.infra.llm.factory.ModelRegistry') as mock_registry, \
             patch('src.backend.infra.llm.factory.settings') as mock_settings:
            mock_adapter_cls = Mock(return_value=MagicMock())
            mock_registry.get_class.return_value = mock_adapter_cls
            mock_settings.gemini = MagicMock()
            mock_settings.gemini.api_key = "gemini-key"

            result = LLMFactory.get_instance("gemini-1.5-pro")

            assert result is not None
            mock_adapter_cls.assert_called_once_with(
                model_id="gemini-1.5-pro",
                api_key="gemini-key"
            )

    def test_get_instance_with_unknown_model(self):
        """Test get_instance with unknown model uses default API key."""
        with patch('src.backend.infra.llm.factory.ModelRegistry') as mock_registry, \
             patch('src.backend.infra.llm.factory.settings') as mock_settings:
            mock_adapter_cls = Mock(return_value=MagicMock())
            mock_registry.get_class.return_value = mock_adapter_cls
            mock_settings.default_api_key = "default-key"

            result = LLMFactory.get_instance("unknown-model")

            assert result is not None
            mock_adapter_cls.assert_called_once_with(
                model_id="unknown-model",
                api_key="default-key"
            )

    def test_get_instance_calls_registry(self):
        """Test get_instance calls ModelRegistry.get_class."""
        with patch('src.backend.infra.llm.factory.ModelRegistry') as mock_registry, \
             patch('src.backend.infra.llm.factory.settings') as mock_settings:
            mock_adapter_cls = Mock(return_value=MagicMock())
            mock_registry.get_class.return_value = mock_adapter_cls
            mock_settings.openai = MagicMock()
            mock_settings.openai.api_key = "key"

            LLMFactory.get_instance("gpt-4o")

            mock_registry.get_class.assert_called_once_with("gpt-4o")

    def test_get_instance_is_classmethod(self):
        """Test get_instance is a class method."""
        assert hasattr(LLMFactory, 'get_instance')
        import inspect
        assert isinstance(inspect.getattr_static(LLMFactory, 'get_instance'), classmethod)

    def test_get_instance_gpt_35_turbo(self):
        """Test get_instance with gpt-3.5-turbo."""
        with patch('src.backend.infra.llm.factory.ModelRegistry') as mock_registry, \
             patch('src.backend.infra.llm.factory.settings') as mock_settings:
            mock_adapter_cls = Mock(return_value=MagicMock())
            mock_registry.get_class.return_value = mock_adapter_cls
            mock_settings.openai = MagicMock()
            mock_settings.openai.api_key = "key"

            result = LLMFactory.get_instance("gpt-3.5-turbo")

            assert result is not None

    def test_get_instance_gpt_case_sensitive(self):
        """Test get_instance is case sensitive."""
        with patch('src.backend.infra.llm.factory.ModelRegistry') as mock_registry, \
             patch('src.backend.infra.llm.factory.settings') as mock_settings:
            mock_adapter_cls = Mock(return_value=MagicMock())
            mock_registry.get_class.return_value = mock_adapter_cls
            mock_settings.default_api_key = "default-key"

            result = LLMFactory.get_instance("GPT-4O")

            assert result is not None
            mock_adapter_cls.assert_called_once_with(
                model_id="GPT-4O",
                api_key="default-key"
            )

    def test_get_instance_gemini_1_5_flash(self):
        """Test get_instance with gemini-1.5-flash."""
        with patch('src.backend.infra.llm.factory.ModelRegistry') as mock_registry, \
             patch('src.backend.infra.llm.factory.settings') as mock_settings:
            mock_adapter_cls = Mock(return_value=MagicMock())
            mock_registry.get_class.return_value = mock_adapter_cls
            mock_settings.gemini = MagicMock()
            mock_settings.gemini.api_key = "key"

            result = LLMFactory.get_instance("gemini-1.5-flash")

            assert result is not None

    def test_get_instance_deepseek_model(self):
        """Test get_instance with deepseek model."""
        with patch('src.backend.infra.llm.factory.ModelRegistry') as mock_registry, \
             patch('src.backend.infra.llm.factory.settings') as mock_settings:
            mock_adapter_cls = Mock(return_value=MagicMock())
            mock_registry.get_class.return_value = mock_adapter_cls
            mock_settings.default_api_key = "default-key"

            result = LLMFactory.get_instance("deepseek-chat")

            assert result is not None

    def test_get_instance_with_unicode_model_id(self):
        """Test get_instance with unicode model ID."""
        with patch('src.backend.infra.llm.factory.ModelRegistry') as mock_registry, \
             patch('src.backend.infra.llm.factory.settings') as mock_settings:
            mock_adapter_cls = Mock(return_value=MagicMock())
            mock_registry.get_class.return_value = mock_adapter_cls
            mock_settings.default_api_key = "default-key"

            result = LLMFactory.get_instance("模型-中文")

            assert result is not None

    def test_get_instance_with_empty_model_id(self):
        """Test get_instance with empty model ID."""
        with patch('src.backend.infra.llm.factory.ModelRegistry') as mock_registry, \
             patch('src.backend.infra.llm.factory.settings') as mock_settings:
            mock_adapter_cls = Mock(return_value=MagicMock())
            mock_registry.get_class.return_value = mock_adapter_cls
            mock_settings.default_api_key = "default-key"

            result = LLMFactory.get_instance("")

            assert result is not None

    def test_get_instance_with_long_model_id(self):
        """Test get_instance with long model ID."""
        with patch('src.backend.infra.llm.factory.ModelRegistry') as mock_registry, \
             patch('src.backend.infra.llm.factory.settings') as mock_settings:
            mock_adapter_cls = Mock(return_value=MagicMock())
            mock_registry.get_class.return_value = mock_adapter_cls
            mock_settings.default_api_key = "default-key"

            long_id = "x" * 1000
            result = LLMFactory.get_instance(long_id)

            assert result is not None

    def test_get_instance_returns_different_instances(self):
        """Test get_instance returns different instances for different calls."""
        with patch('src.backend.infra.llm.factory.ModelRegistry') as mock_registry, \
             patch('src.backend.infra.llm.factory.settings') as mock_settings:
            # Create new MagicMock instance each time the mock is called
            mock_adapter_cls = Mock(side_effect=lambda *args, **kwargs: MagicMock())
            mock_registry.get_class.return_value = mock_adapter_cls
            mock_settings.openai = MagicMock()
            mock_settings.openai.api_key = "key"

            result1 = LLMFactory.get_instance("gpt-4o")
            result2 = LLMFactory.get_instance("gpt-4o")

            # Should be different instances (factory pattern)
            assert result1 is not result2

    def test_get_instance_passes_model_id_to_adapter(self):
        """Test get_instance passes correct model_id to adapter."""
        with patch('src.backend.infra.llm.factory.ModelRegistry') as mock_registry, \
             patch('src.backend.infra.llm.factory.settings') as mock_settings:
            mock_adapter_cls = Mock(return_value=MagicMock())
            mock_registry.get_class.return_value = mock_adapter_cls
            mock_settings.openai = MagicMock()
            mock_settings.openai.api_key = "key"

            LLMFactory.get_instance("custom-model-id")

            call_kwargs = mock_adapter_cls.call_args[1]
            assert call_kwargs['model_id'] == "custom-model-id"
