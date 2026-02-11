"""Tests for LLMService."""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from src.backend.app.services.llm import LLMService
from src.backend.domain.exceptions import BusinessException
from src.shared.schemas import llm as llm_schema


class TestLLMService:
    """Tests for LLMService class."""

    @pytest.fixture
    def llm_service(self, mock_session_repository):
        """Create an LLMService instance with mock repository."""
        return LLMService(session_repo=mock_session_repository)

    @pytest.fixture
    def model_switch_request(self):
        """Sample model switch request."""
        return llm_schema.ModelSwitchRequest(
            session_id=1,
            model_id="gpt-4o"
        )

    def test_llm_service_initialization(self, mock_session_repository):
        """Test LLMService initialization."""
        service = LLMService(session_repo=mock_session_repository)
        assert service.session_repo == mock_session_repository

    @pytest.mark.asyncio
    async def test_get_models_success(self, llm_service):
        """Test get_models returns available models."""
        with patch('src.backend.app.services.llm.ModelRegistry') as mock_registry, \
             patch('src.backend.app.services.llm.settings') as mock_settings:
            mock_registry.get_all_model_ids.return_value = ["gpt-4o", "gpt-3.5-turbo", "gemini-1.5-pro"]
            mock_settings.default_llm = "gpt-4o"

            result = await llm_service.get_models()

            # Verify result - models should be LLMInfo objects
            assert isinstance(result, llm_schema.LLMListResponse)
            assert len(result.models) == 3
            assert result.models[0].id == "gpt-4o"
            assert result.models[0].name == "GPT-4O"
            assert result.models[0].provider == llm_schema.ModelProvider.OPENAI
            assert result.models[0].is_active == True
            assert result.current_model_id == "gpt-4o"

    @pytest.mark.asyncio
    async def test_get_models_empty_list(self, llm_service):
        """Test get_models with empty model list."""
        with patch('src.backend.app.services.llm.ModelRegistry') as mock_registry, \
             patch('src.backend.app.services.llm.settings') as mock_settings:
            mock_registry.get_all_model_ids.return_value = []
            mock_settings.default_llm = "gpt-4o"

            result = await llm_service.get_models()

            assert result.models == []
            assert result.current_model_id == "gpt-4o"

    @pytest.mark.asyncio
    async def test_get_models_single_model(self, llm_service):
        """Test get_models with single model."""
        with patch('src.backend.app.services.llm.ModelRegistry') as mock_registry, \
             patch('src.backend.app.services.llm.settings') as mock_settings:
            mock_registry.get_all_model_ids.return_value = ["gpt-4o"]
            mock_settings.default_llm = "gpt-4o"

            result = await llm_service.get_models()

            assert len(result.models) == 1
            first = result.models[0]
            assert first.id == "gpt-4o"
            assert first.name == "GPT-4O"
            assert first.provider == llm_schema.ModelProvider.OPENAI
            assert first.is_active is True
            assert result.current_model_id == "gpt-4o"

    @pytest.mark.asyncio
    async def test_switch_model_success(self, llm_service, model_switch_request):
        """Test switch_model updates session model."""
        with patch('src.backend.app.services.llm.ModelRegistry') as mock_registry:
            mock_registry.exists.return_value = True
            llm_service.session_repo.update_session_model = AsyncMock(return_value=True)

            result = await llm_service.switch_model(model_switch_request)

            # Verify repository was called
            llm_service.session_repo.update_session_model.assert_called_once_with(
                session_id=1,
                model_id="gpt-4o"
            )

            # Verify result
            assert isinstance(result, llm_schema.ModelSwitchResponse)
            assert result.session_id == 1
            assert result.active_model_id == "gpt-4o"
            assert result.success is True

    @pytest.mark.asyncio
    async def test_switch_model_with_invalid_model(self, llm_service, model_switch_request):
        """Test switch_model raises error for invalid model."""
        with patch('src.backend.app.services.llm.ModelRegistry') as mock_registry:
            mock_registry.exists.return_value = False

            with pytest.raises(BusinessException) as exc_info:
                await llm_service.switch_model(model_switch_request)

            assert "不可用" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_switch_model_session_not_found(self, llm_service, model_switch_request):
        """Test switch_model when session doesn't exist."""
        with patch('src.backend.app.services.llm.ModelRegistry') as mock_registry:
            mock_registry.exists.return_value = True
            llm_service.session_repo.update_session_model = AsyncMock(return_value=False)

            with pytest.raises(BusinessException) as exc_info:
                await llm_service.switch_model(model_switch_request)

            assert "会话不存在" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_switch_model_to_different_models(self, llm_service, model_switch_request):
        """Test switch_model to different models."""
        models = ["gpt-4o", "gpt-3.5-turbo", "gemini-1.5-pro"]

        with patch('src.backend.app.services.llm.ModelRegistry') as mock_registry:
            mock_registry.exists.return_value = True
            llm_service.session_repo.update_session_model = AsyncMock(return_value=True)

            for model_id in models:
                model_switch_request.model_id = model_id
                result = await llm_service.switch_model(model_switch_request)

                assert result.active_model_id == model_id

    @pytest.mark.asyncio
    async def test_switch_model_with_repository_exception(self, llm_service, model_switch_request):
        """Test switch_model when repository raises exception."""
        with patch('src.backend.app.services.llm.ModelRegistry') as mock_registry:
            mock_registry.exists.return_value = True
            llm_service.session_repo.update_session_model = AsyncMock(
                side_effect=Exception("Database error")
            )

            # Should handle the exception internally or raise BusinessException
            # Depending on implementation
            with pytest.raises(Exception):
                await llm_service.switch_model(model_switch_request)

    @pytest.mark.asyncio
    async def test_get_models_calls_registry(self, llm_service):
        """Test get_models calls ModelRegistry.get_all_model_ids."""
        with patch('src.backend.app.services.llm.ModelRegistry') as mock_registry, \
             patch('src.backend.app.services.llm.settings') as mock_settings:
            mock_registry.get_all_model_ids.return_value = ["gpt-4o"]
            mock_settings.default_llm = "gpt-4o"

            await llm_service.get_models()

            mock_registry.get_all_model_ids.assert_called_once()

    @pytest.mark.asyncio
    async def test_switch_model_calls_registry_exists(self, llm_service, model_switch_request):
        """Test switch_model calls ModelRegistry.exists."""
        with patch('src.backend.app.services.llm.ModelRegistry') as mock_registry:
            mock_registry.exists.return_value = True
            llm_service.session_repo.update_session_model = AsyncMock(return_value=True)

            await llm_service.switch_model(model_switch_request)

            mock_registry.exists.assert_called_once_with("gpt-4o")

    @pytest.mark.asyncio
    async def test_switch_model_with_session_id_zero(self, llm_service):
        """Test switch_model with session_id=0."""
        request = llm_schema.ModelSwitchRequest(session_id=0, model_id="gpt-4o")

        with patch('src.backend.app.services.llm.ModelRegistry') as mock_registry:
            mock_registry.exists.return_value = True
            llm_service.session_repo.update_session_model = AsyncMock(return_value=True)

            result = await llm_service.switch_model(request)

            assert result.session_id == 0

    @pytest.mark.asyncio
    async def test_switch_model_with_negative_session_id(self, llm_service):
        """Test switch_model with negative session_id."""
        request = llm_schema.ModelSwitchRequest(session_id=-1, model_id="gpt-4o")

        with patch('src.backend.app.services.llm.ModelRegistry') as mock_registry:
            mock_registry.exists.return_value = True
            llm_service.session_repo.update_session_model = AsyncMock(return_value=True)

            result = await llm_service.switch_model(request)

            assert result.session_id == -1

    @pytest.mark.asyncio
    async def test_switch_model_response_success_always_true(self, llm_service, model_switch_request):
        """Test switch_model response success is True on success."""
        with patch('src.backend.app.services.llm.ModelRegistry') as mock_registry:
            mock_registry.exists.return_value = True
            llm_service.session_repo.update_session_model = AsyncMock(return_value=True)

            result = await llm_service.switch_model(model_switch_request)

            assert result.success is True

    @pytest.mark.asyncio
    async def test_get_models_default_model_from_settings(self, llm_service):
        """Test get_models uses default model from settings."""
        with patch('src.backend.app.services.llm.ModelRegistry') as mock_registry, \
             patch('src.backend.app.services.llm.settings') as mock_settings:
            mock_registry.get_all_model_ids.return_value = []
            mock_settings.default_llm = "custom-default-model"

            result = await llm_service.get_models()

            assert result.current_model_id == "custom-default-model"

    @pytest.mark.asyncio
    async def test_switch_model_case_sensitive(self, llm_service):
        """Test switch_model is case sensitive."""
        request = llm_schema.ModelSwitchRequest(session_id=1, model_id="GPT-4O")

        with patch('src.backend.app.services.llm.ModelRegistry') as mock_registry:
            mock_registry.exists.side_effect = lambda x: x == "GPT-4O"
            llm_service.session_repo.update_session_model = AsyncMock(return_value=True)

            result = await llm_service.switch_model(request)

            assert result.active_model_id == "GPT-4O"

    @pytest.mark.asyncio
    async def test_get_models_with_many_models(self, llm_service):
        """Test get_models with large model list."""
        models = [f"model-{i}" for i in range(100)]

        with patch('src.backend.app.services.llm.ModelRegistry') as mock_registry, \
             patch('src.backend.app.services.llm.settings') as mock_settings:
            mock_registry.get_all_model_ids.return_value = models
            mock_settings.default_llm = "model-0"

            result = await llm_service.get_models()

            assert len(result.models) == 100

    @pytest.mark.asyncio
    async def test_switch_model_unicode_model_id(self, llm_service):
        """Test switch_model with unicode model_id."""
        request = llm_schema.ModelSwitchRequest(session_id=1, model_id="模型-中文")

        with patch('src.backend.app.services.llm.ModelRegistry') as mock_registry:
            mock_registry.exists.return_value = True
            llm_service.session_repo.update_session_model = AsyncMock(return_value=True)

            result = await llm_service.switch_model(request)

            assert result.active_model_id == "模型-中文"

    @pytest.mark.asyncio
    async def test_get_models_response_structure(self, llm_service):
        """Test get_models returns correct response structure."""
        with patch('src.backend.app.services.llm.ModelRegistry') as mock_registry, \
             patch('src.backend.app.services.llm.settings') as mock_settings:
            mock_registry.get_all_model_ids.return_value = ["gpt-4o"]
            mock_settings.default_llm = "gpt-4o"

            result = await llm_service.get_models()

            # Has models field
            assert hasattr(result, 'models')
            # Has current_model_id field
            assert hasattr(result, 'current_model_id')
