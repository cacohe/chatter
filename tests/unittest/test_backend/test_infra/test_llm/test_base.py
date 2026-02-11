"""Tests for LLM base class."""
import pytest
from abc import ABC
from src.backend.infra.llm.base import BaseLLM


class TestBaseLLM:
    """Tests for BaseLLM abstract class."""

    @pytest.fixture
    def concrete_llm(self):
        """Create a concrete implementation of BaseLLM for testing."""
        class ConcreteLLM(BaseLLM):
            async def chat(self, messages, params):
                return "Response"

            async def stream_chat(self, messages, params):
                yield "Stream"

        return ConcreteLLM(model_id="test-model", api_key="test-key")

    def test_base_llm_is_abstract(self):
        """Test BaseLLM is an abstract class."""
        assert issubclass(BaseLLM, ABC)

    def test_base_llm_initialization(self, concrete_llm):
        """Test BaseLLM initialization."""
        assert concrete_llm.model_id == "test-model"
        assert concrete_llm.api_key == "test-key"
        assert concrete_llm.base_url is None

    def test_base_llm_initialization_with_base_url(self):
        """Test BaseLLM initialization with base_url."""
        class ConcreteLLM(BaseLLM):
            async def chat(self, messages, params):
                return "Response"

            async def stream_chat(self, messages, params):
                yield "Stream"

        llm = ConcreteLLM(
            model_id="test-model",
            api_key="test-key",
            base_url="https://api.example.com"
        )
        assert llm.base_url == "https://api.example.com"

    def test_concrete_llm_chat_method(self, concrete_llm):
        """Test concrete LLM implements chat method."""
        assert hasattr(concrete_llm, 'chat')
        assert callable(concrete_llm.chat)

    def test_concrete_llm_stream_chat_method(self, concrete_llm):
        """Test concrete LLM implements stream_chat method."""
        assert hasattr(concrete_llm, 'stream_chat')
        assert callable(concrete_llm.stream_chat)

    @pytest.mark.asyncio
    async def test_concrete_llm_chat_returns_string(self, concrete_llm):
        """Test chat method returns string."""
        result = await concrete_llm.chat([], None)
        assert isinstance(result, str)

    @pytest.mark.asyncio
    async def test_concrete_llm_stream_chat_is_generator(self, concrete_llm):
        """Test stream_chat is async generator."""
        result = concrete_llm.stream_chat([], None)
        # Should be async generator
        assert hasattr(result, '__aiter__')
        async for chunk in result:
            assert isinstance(chunk, str)
            break

    def test_base_llm_cannot_be_instantiated(self):
        """Test BaseLLM cannot be instantiated directly."""
        with pytest.raises(TypeError):
            BaseLLM(model_id="test", api_key="key")

    def test_base_llm_has_chat_abstract_method(self):
        """Test BaseLLM has abstract chat method."""
        assert 'chat' in BaseLLM.__abstractmethods__

    def test_base_llm_has_stream_chat_abstract_method(self):
        """Test BaseLLM has abstract stream_chat method."""
        assert 'stream_chat' in BaseLLM.__abstractmethods__

    def test_concrete_llm_can_be_instantiated(self):
        """Test concrete implementation can be instantiated."""
        class ConcreteLLM(BaseLLM):
            async def chat(self, messages, params):
                return "Response"

            async def stream_chat(self, messages, params):
                yield "Stream"

        llm = ConcreteLLM(model_id="test", api_key="key")
        assert llm is not None

    def test_concrete_llm_with_different_model_ids(self):
        """Test concrete LLM with different model IDs."""
        class ConcreteLLM(BaseLLM):
            async def chat(self, messages, params):
                return "Response"

            async def stream_chat(self, messages, params):
                yield "Stream"

        llm1 = ConcreteLLM(model_id="model-1", api_key="key-1")
        llm2 = ConcreteLLM(model_id="model-2", api_key="key-2")
        assert llm1.model_id != llm2.model_id

    def test_concrete_llm_with_empty_api_key(self):
        """Test concrete LLM with empty API key."""
        class ConcreteLLM(BaseLLM):
            async def chat(self, messages, params):
                return "Response"

            async def stream_chat(self, messages, params):
                yield "Stream"

        llm = ConcreteLLM(model_id="test", api_key="")
        assert llm.api_key == ""

    def test_concrete_llm_with_unicode_model_id(self):
        """Test concrete LLM with unicode model ID."""
        class ConcreteLLM(BaseLLM):
            async def chat(self, messages, params):
                return "Response"

            async def stream_chat(self, messages, params):
                yield "Stream"

        llm = ConcreteLLM(model_id="模型-中文", api_key="key")
        assert llm.model_id == "模型-中文"

    def test_concrete_llm_with_long_model_id(self):
        """Test concrete LLM with long model ID."""
        class ConcreteLLM(BaseLLM):
            async def chat(self, messages, params):
                return "Response"

            async def stream_chat(self, messages, params):
                yield "Stream"

        long_id = "x" * 1000
        llm = ConcreteLLM(model_id=long_id, api_key="key")
        assert len(llm.model_id) == 1000

    @pytest.mark.asyncio
    async def test_concrete_llm_chat_with_empty_messages(self, concrete_llm):
        """Test chat with empty messages."""
        result = await concrete_llm.chat([], None)
        assert result == "Response"

    @pytest.mark.asyncio
    async def test_concrete_llm_stream_chat_with_empty_messages(self, concrete_llm):
        """Test stream_chat with empty messages."""
        result = concrete_llm.stream_chat([], None)
        count = 0
        async for _ in result:
            count += 1
            if count >= 1:
                break
        assert count >= 1
