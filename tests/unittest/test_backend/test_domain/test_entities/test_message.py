"""Tests for Message entity."""
import pytest
from datetime import datetime
from src.backend.domain.entities.message import Message, MessageRole


class TestMessageRole:
    """Tests for MessageRole enum."""

    def test_message_role_user_value(self):
        """Test USER enum value."""
        assert MessageRole.USER == "user"

    def test_message_role_assistant_value(self):
        """Test ASSISTANT enum value."""
        assert MessageRole.ASSISTANT == "assistant"

    def test_message_role_system_value(self):
        """Test SYSTEM enum value."""
        assert MessageRole.SYSTEM == "system"

    def test_message_role_is_string_enum(self):
        """Test MessageRole is a string enum."""
        assert issubclass(MessageRole, str)


class TestMessage:
    """Tests for Message entity."""

    @pytest.fixture
    def sample_message(self):
        """Create a sample message for testing."""
        return Message(
            id=1,
            session_id=1,
            role=MessageRole.USER,
            content="Hello, how are you?",
            created_at=datetime.now()
        )

    def test_message_initialization(self, sample_message):
        """Test message initialization."""
        assert sample_message.id == 1
        assert sample_message.session_id == 1
        assert sample_message.role == MessageRole.USER
        assert sample_message.content == "Hello, how are you?"
        assert isinstance(sample_message.created_at, datetime)

    def test_message_with_assistant_role(self):
        """Test message with assistant role."""
        msg = Message(
            id=2,
            session_id=1,
            role=MessageRole.ASSISTANT,
            content="I'm fine, thank you!",
            created_at=datetime.now()
        )
        assert msg.role == MessageRole.ASSISTANT

    def test_message_with_system_role(self):
        """Test message with system role."""
        msg = Message(
            id=3,
            session_id=1,
            role=MessageRole.SYSTEM,
            content="System prompt",
            created_at=datetime.now()
        )
        assert msg.role == MessageRole.SYSTEM

    def test_is_from_ai_with_assistant_role(self, sample_message):
        """Test is_from_ai property with assistant role."""
        sample_message.role = MessageRole.ASSISTANT
        assert sample_message.is_from_ai is True

    def test_is_from_ai_with_user_role(self, sample_message):
        """Test is_from_ai property with user role."""
        sample_message.role = MessageRole.USER
        assert sample_message.is_from_ai is False

    def test_is_from_ai_with_system_role(self, sample_message):
        """Test is_from_ai property with system role."""
        sample_message.role = MessageRole.SYSTEM
        assert sample_message.is_from_ai is False

    def test_message_model_dump(self, sample_message):
        """Test message model_dump method."""
        data = sample_message.model_dump()
        assert data["id"] == 1
        assert data["session_id"] == 1
        assert data["role"] == "user"
        assert data["content"] == "Hello, how are you?"

    def test_message_model_dump_json(self, sample_message):
        """Test message model_dump_json method."""
        json_str = sample_message.model_dump_json()
        assert "user" in json_str
        assert "Hello, how are you?" in json_str

    def test_message_empty_content(self):
        """Test message with empty content."""
        msg = Message(
            id=1,
            session_id=1,
            role=MessageRole.USER,
            content="",
            created_at=datetime.now()
        )
        assert msg.content == ""

    def test_message_long_content(self):
        """Test message with long content."""
        long_content = "A" * 10000
        msg = Message(
            id=1,
            session_id=1,
            role=MessageRole.USER,
            content=long_content,
            created_at=datetime.now()
        )
        assert len(msg.content) == 10000

    def test_message_unicode_content(self):
        """Test message with unicode content."""
        msg = Message(
            id=1,
            session_id=1,
            role=MessageRole.USER,
            content="Hello 世界 🌍",
            created_at=datetime.now()
        )
        assert msg.content == "Hello 世界 🌍"

    def test_message_session_id_zero(self):
        """Test message with session_id=0."""
        msg = Message(
            id=1,
            session_id=0,
            role=MessageRole.USER,
            content="Test",
            created_at=datetime.now()
        )
        assert msg.session_id == 0

    def test_message_negative_session_id(self):
        """Test message with negative session_id."""
        msg = Message(
            id=1,
            session_id=-1,
            role=MessageRole.USER,
            content="Test",
            created_at=datetime.now()
        )
        assert msg.session_id == -1

    def test_message_model_validation_valid_role_string(self):
        """Test message accepts valid role as string."""
        msg = Message(
            id=1,
            session_id=1,
            role="user",  # String instead of enum
            content="Test",
            created_at=datetime.now()
        )
        assert msg.role == "user"

    def test_message_role_equality(self):
        """Test MessageRole equality."""
        role1 = MessageRole.USER
        role2 = MessageRole("user")
        assert role1 == role2

    def test_message_role_iteration(self):
        """Test iterating over MessageRole enum."""
        roles = list(MessageRole)
        assert len(roles) == 3
        assert MessageRole.USER in roles
        assert MessageRole.ASSISTANT in roles
        assert MessageRole.SYSTEM in roles
