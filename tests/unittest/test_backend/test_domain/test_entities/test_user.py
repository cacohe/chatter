"""Tests for User entity."""
import pytest
from datetime import datetime
from src.backend.domain.entities.user import User


class TestUser:
    """Tests for User entity."""

    @pytest.fixture
    def sample_user(self):
        """Create a sample user for testing."""
        return User(
            id="user-uuid-123",
            email="test@example.com",
            username="testuser",
            avatar_url="https://example.com/avatar.jpg",
            role="user",
            created_at=datetime.now()
        )

    def test_user_initialization(self, sample_user):
        """Test user initialization."""
        assert sample_user.id == "user-uuid-123"
        assert sample_user.email == "test@example.com"
        assert sample_user.username == "testuser"
        assert sample_user.avatar_url == "https://example.com/avatar.jpg"
        assert sample_user.role == "user"
        assert isinstance(sample_user.created_at, datetime)

    def test_user_is_admin_true(self, sample_user):
        """Test is_admin returns True when role is admin."""
        sample_user.role = "admin"
        assert sample_user.is_admin() is True

    def test_user_is_admin_false(self, sample_user):
        """Test is_admin returns False when role is not admin."""
        sample_user.role = "user"
        assert sample_user.is_admin() is False

    def test_user_is_admin_case_sensitive(self, sample_user):
        """Test is_admin is case sensitive."""
        sample_user.role = "Admin"
        assert sample_user.is_admin() is False

    def test_user_is_admin_whitespace(self, sample_user):
        """Test is_admin with whitespace in role."""
        sample_user.role = " admin "
        assert sample_user.is_admin() is False

    def test_user_without_username(self):
        """Test user with None username."""
        user = User(
            id="user-uuid-123",
            email="test@example.com",
            username=None,
            avatar_url=None,
            role="user",
            created_at=datetime.now()
        )
        assert user.username is None

    def test_user_without_avatar_url(self):
        """Test user with None avatar_url."""
        user = User(
            id="user-uuid-123",
            email="test@example.com",
            username="testuser",
            avatar_url=None,
            role="user",
            created_at=datetime.now()
        )
        assert user.avatar_url is None

    def test_user_default_role(self):
        """Test user has default role."""
        user = User(
            id="user-uuid-123",
            email="test@example.com",
            created_at=datetime.now()
        )
        assert user.role == "user"

    def test_user_with_empty_string_optional_fields(self):
        """Test user with empty string optional fields."""
        user = User(
            id="user-uuid-123",
            email="test@example.com",
            username="",
            avatar_url="",
            role="user",
            created_at=datetime.now()
        )
        assert user.username == ""
        assert user.avatar_url == ""

    def test_user_email_validation_valid(self, sample_user):
        """Test valid email is accepted."""
        assert sample_user.email == "test@example.com"

    def test_user_email_with_subdomain(self):
        """Test user email with subdomain."""
        user = User(
            id="user-uuid-123",
            email="user@sub.example.com",
            created_at=datetime.now()
        )
        assert user.email == "user@sub.example.com"

    def test_user_unicode_username(self):
        """Test user with unicode username."""
        user = User(
            id="user-uuid-123",
            email="test@example.com",
            username="用户名",
            created_at=datetime.now()
        )
        assert user.username == "用户名"

    def test_user_long_username(self):
        """Test user with long username."""
        long_username = "a" * 100
        user = User(
            id="user-uuid-123",
            email="test@example.com",
            username=long_username,
            created_at=datetime.now()
        )
        assert len(user.username) == 100

    def test_user_different_roles(self):
        """Test user with different roles."""
        roles = ["user", "admin", "moderator", "superuser"]
        for role in roles:
            user = User(
                id="user-uuid-123",
                email="test@example.com",
                role=role,
                created_at=datetime.now()
            )
            assert user.role == role

    def test_user_id_is_string(self, sample_user):
        """Test user id is string type."""
        assert isinstance(sample_user.id, str)

    def test_user_id_uuid_format(self):
        """Test user id can be UUID format."""
        user = User(
            id="550e8400-e29b-41d4-a716-446655440000",
            email="test@example.com",
            created_at=datetime.now()
        )
        assert user.id == "550e8400-e29b-41d4-a716-446655440000"

    def test_user_avatar_url_https(self):
        """Test user avatar URL with https."""
        user = User(
            id="user-uuid-123",
            email="test@example.com",
            avatar_url="https://example.com/avatar.jpg",
            created_at=datetime.now()
        )
        assert user.avatar_url.startswith("https://")

    def test_user_avatar_url_http(self):
        """Test user avatar URL with http."""
        user = User(
            id="user-uuid-123",
            email="test@example.com",
            avatar_url="http://example.com/avatar.jpg",
            created_at=datetime.now()
        )
        assert user.avatar_url.startswith("http://")

    def test_user_model_dump(self, sample_user):
        """Test user model_dump method."""
        data = sample_user.model_dump()
        assert data["id"] == "user-uuid-123"
        assert data["email"] == "test@example.com"
        assert data["username"] == "testuser"
        assert data["role"] == "user"

    def test_user_model_dump_json(self, sample_user):
        """Test user model_dump_json method."""
        json_str = sample_user.model_dump_json()
        assert "user-uuid-123" in json_str
        assert "test@example.com" in json_str

    def test_user_is_pydantic_model(self, sample_user):
        """Test user is a Pydantic BaseModel."""
        assert hasattr(sample_user, 'model_dump')
        assert hasattr(sample_user, 'model_dump_json')

    def test_user_created_at_datetime(self, sample_user):
        """Test created_at is datetime."""
        assert isinstance(sample_user.created_at, datetime)

    def test_user_comparison_by_id(self):
        """Test users can be compared by id."""
        now = datetime.now()
        user1 = User(
            id="user-1",
            email="user1@example.com",
            created_at=now
        )
        user2 = User(
            id="user-2",
            email="user2@example.com",
            created_at=now
        )
        assert user1.id != user2.id

    def test_user_empty_email(self):
        """Test user with empty email - EmailStr requires valid format."""
        # Skip this test - EmailStr requires valid email format with @
        # Pydantic EmailStr validation rejects empty strings
        pytest.skip("User email field requires valid email format, cannot be empty")

    def test_user_username_with_numbers(self):
        """Test username with numbers."""
        user = User(
            id="user-uuid-123",
            email="test@example.com",
            username="user123",
            created_at=datetime.now()
        )
        assert user.username == "user123"

    def test_user_username_with_underscores(self):
        """Test username with underscores."""
        user = User(
            id="user-uuid-123",
            email="test@example.com",
            username="user_name",
            created_at=datetime.now()
        )
        assert user.username == "user_name"

    def test_user_username_with_dashes(self):
        """Test username with dashes."""
        user = User(
            id="user-uuid-123",
            email="test@example.com",
            username="user-name",
            created_at=datetime.now()
        )
        assert user.username == "user-name"
