"""Tests for LLM schema."""
import pytest
from pydantic import ValidationError
from src.backend.infra.llm.schema import LLMParameters, ChatMessage


class TestLLMParameters:
    """Tests for LLMParameters schema."""

    def test_llm_parameters_initialization_with_defaults(self):
        """Test LLMParameters with default values."""
        params = LLMParameters()
        assert params.temperature == 0.7
        assert params.top_p == 1.0
        assert params.max_tokens == 2048
        assert params.stream is False
        assert params.extra_body == {}

    def test_llm_parameters_custom_temperature(self):
        """Test LLMParameters with custom temperature."""
        params = LLMParameters(temperature=1.5)
        assert params.temperature == 1.5

    def test_llm_parameters_custom_top_p(self):
        """Test LLMParameters with custom top_p."""
        params = LLMParameters(top_p=0.9)
        assert params.top_p == 0.9

    def test_llm_parameters_custom_max_tokens(self):
        """Test LLMParameters with custom max_tokens."""
        params = LLMParameters(max_tokens=4096)
        assert params.max_tokens == 4096

    def test_llm_parameters_custom_stream(self):
        """Test LLMParameters with custom stream."""
        params = LLMParameters(stream=True)
        assert params.stream is True

    def test_llm_parameters_custom_extra_body(self):
        """Test LLMParameters with custom extra_body."""
        extra = {"custom_param": "value"}
        params = LLMParameters(extra_body=extra)
        assert params.extra_body == extra

    def test_llm_parameters_temperature_minimum(self):
        """Test temperature minimum value."""
        params = LLMParameters(temperature=0.0)
        assert params.temperature == 0.0

    def test_llm_parameters_temperature_maximum(self):
        """Test temperature maximum value."""
        params = LLMParameters(temperature=2.0)
        assert params.temperature == 2.0

    def test_llm_parameters_temperature_below_minimum_raises_error(self):
        """Test temperature below minimum raises ValidationError."""
        with pytest.raises(ValidationError):
            LLMParameters(temperature=-0.1)

    def test_llm_parameters_temperature_above_maximum_raises_error(self):
        """Test temperature above maximum raises ValidationError."""
        with pytest.raises(ValidationError):
            LLMParameters(temperature=2.1)

    def test_llm_parameters_max_tokens_none(self):
        """Test max_tokens can be None."""
        params = LLMParameters(max_tokens=None)
        assert params.max_tokens is None

    def test_llm_parameters_max_tokens_zero(self):
        """Test max_tokens can be 0."""
        params = LLMParameters(max_tokens=0)
        assert params.max_tokens == 0

    def test_llm_parameters_max_tokens_negative(self):
        """Test max_tokens can be negative (implementation dependent)."""
        # Pydantic doesn't have ge constraint on max_tokens
        params = LLMParameters(max_tokens=-1)
        assert params.max_tokens == -1

    def test_llm_parameters_extra_body_dict(self):
        """Test extra_body is a dict."""
        params = LLMParameters(extra_body={"key": "value"})
        assert isinstance(params.extra_body, dict)

    def test_llm_parameters_extra_body_default_factory(self):
        """Test extra_body uses default_factory."""
        params1 = LLMParameters()
        params2 = LLMParameters()
        # Default factory should create new dict each time
        assert params1.extra_body is not params2.extra_body

    def test_llm_parameters_model_dump(self):
        """Test model_dump method."""
        params = LLMParameters(temperature=1.0, max_tokens=4096)
        data = params.model_dump()
        assert data["temperature"] == 1.0
        assert data["max_tokens"] == 4096

    def test_llm_parameters_model_dump_json(self):
        """Test model_dump_json method."""
        params = LLMParameters()
        json_str = params.model_dump_json()
        assert "temperature" in json_str

    def test_llm_parameters_is_pydantic_model(self):
        """Test LLMParameters is a Pydantic BaseModel."""
        from pydantic import BaseModel
        assert issubclass(LLMParameters, BaseModel)


class TestChatMessage:
    """Tests for ChatMessage schema."""

    def test_chat_message_initialization(self):
        """Test ChatMessage initialization."""
        message = ChatMessage(role="user", content="Hello")
        assert message.role == "user"
        assert message.content == "Hello"

    def test_chat_message_with_user_role(self):
        """Test ChatMessage with user role."""
        message = ChatMessage(role="user", content="Test")
        assert message.role == "user"

    def test_chat_message_with_assistant_role(self):
        """Test ChatMessage with assistant role."""
        message = ChatMessage(role="assistant", content="Test")
        assert message.role == "assistant"

    def test_chat_message_with_system_role(self):
        """Test ChatMessage with system role."""
        message = ChatMessage(role="system", content="Test")
        assert message.role == "system"

    def test_chat_message_with_empty_content(self):
        """Test ChatMessage with empty content."""
        message = ChatMessage(role="user", content="")
        assert message.content == ""

    def test_chat_message_with_long_content(self):
        """Test ChatMessage with long content."""
        long_content = "A" * 10000
        message = ChatMessage(role="user", content=long_content)
        assert len(message.content) == 10000

    def test_chat_message_with_unicode_content(self):
        """Test ChatMessage with unicode content."""
        message = ChatMessage(role="user", content="你好 世界 🌍")
        assert message.content == "你好 世界 🌍"

    def test_chat_message_with_custom_role(self):
        """Test ChatMessage with custom role."""
        message = ChatMessage(role="custom", content="Test")
        assert message.role == "custom"

    def test_chat_message_model_dump(self):
        """Test model_dump method."""
        message = ChatMessage(role="user", content="Hello")
        data = message.model_dump()
        assert data["role"] == "user"
        assert data["content"] == "Hello"

    def test_chat_message_model_dump_json(self):
        """Test model_dump_json method."""
        message = ChatMessage(role="user", content="Hello")
        json_str = message.model_dump_json()
        assert "user" in json_str
        assert "Hello" in json_str

    def test_chat_message_is_pydantic_model(self):
        """Test ChatMessage is a Pydantic BaseModel."""
        from pydantic import BaseModel
        assert issubclass(ChatMessage, BaseModel)

    def test_chat_message_with_multiline_content(self):
        """Test ChatMessage with multiline content."""
        content = "Line 1\nLine 2\nLine 3"
        message = ChatMessage(role="user", content=content)
        assert "\n" in message.content

    def test_chat_message_with_special_characters(self):
        """Test ChatMessage with special characters."""
        content = "<script>alert('test')</script>"
        message = ChatMessage(role="user", content=content)
        assert message.content == content

    def test_chat_message_with_json_content(self):
        """Test ChatMessage with JSON content."""
        content = '{"key": "value"}'
        message = ChatMessage(role="user", content=content)
        assert message.content == content

    def test_chat_message_with_code_content(self):
        """Test ChatMessage with code content."""
        content = "```python\nprint('hello')\n```"
        message = ChatMessage(role="user", content=content)
        assert "```" in message.content

    def test_chat_message_role_string(self):
        """Test role is a string."""
        message = ChatMessage(role="user", content="Test")
        assert isinstance(message.role, str)

    def test_chat_message_content_string(self):
        """Test content is a string."""
        message = ChatMessage(role="user", content="Test")
        assert isinstance(message.content, str)

    def test_chat_message_with_whitespace_content(self):
        """Test ChatMessage with whitespace content."""
        message = ChatMessage(role="user", content="   ")
        assert message.content == "   "

    def test_chat_message_with_newlines_only(self):
        """Test ChatMessage with newlines only."""
        message = ChatMessage(role="user", content="\n\n\n")
        assert message.content == "\n\n\n"
