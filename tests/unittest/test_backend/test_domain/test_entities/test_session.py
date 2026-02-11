"""Tests for Session entity."""
import pytest
from datetime import datetime, timedelta
from src.backend.domain.entities.session import Session


class TestSession:
    """Tests for Session entity."""

    @pytest.fixture
    def sample_session(self):
        """Create a sample session for testing."""
        now = datetime.now()
        return Session(
            id=1,
            user_id="user-uuid-123",
            title="Test Session",
            active_model_id="gpt-4o",
            created_at=now,
            updated_at=now
        )

    def test_session_initialization(self, sample_session):
        """Test session initialization."""
        assert sample_session.id == 1
        assert sample_session.user_id == "user-uuid-123"
        assert sample_session.title == "Test Session"
        assert sample_session.active_model_id == "gpt-4o"
        assert isinstance(sample_session.created_at, datetime)
        assert isinstance(sample_session.updated_at, datetime)

    def test_session_is_owned_by_true(self, sample_session):
        """Test is_owned_by returns True when user_id matches."""
        result = sample_session.is_owned_by("user-uuid-123")
        assert result is True

    def test_session_is_owned_by_false(self, sample_session):
        """Test is_owned_by returns False when user_id does not match."""
        result = sample_session.is_owned_by("other-user-uuid")
        assert result is False

    def test_session_is_owned_by_empty_string(self, sample_session):
        """Test is_owned_by returns False with empty string."""
        result = sample_session.is_owned_by("")
        assert result is False

    def test_session_is_owned_by_case_sensitive(self, sample_session):
        """Test is_owned_by is case sensitive."""
        result = sample_session.is_owned_by("USER-UUID-123")
        assert result is False

    def test_session_get_display_title_with_title(self, sample_session):
        """Test get_display_title returns title when set."""
        result = sample_session.get_display_title()
        assert result == "Test Session"

    def test_session_get_display_title_without_title(self):
        """Test get_display_title returns default when title is empty."""
        now = datetime.now()
        session = Session(
            id=1,
            user_id="user-uuid-123",
            title="",
            active_model_id="gpt-4o",
            created_at=now,
            updated_at=now
        )
        result = session.get_display_title()
        assert result == "未命名会话"

    def test_session_get_display_title_with_none_title(self):
        """Test get_display_title returns default when title is None."""
        # Skip this test - Pydantic model doesn't allow None for title field
        # The Session model has title as a required string field
        pytest.skip("Session title field doesn't accept None")

    def test_session_get_display_title_with_whitespace(self):
        """Test get_display_title with whitespace title."""
        now = datetime.now()
        session = Session(
            id=1,
            user_id="user-uuid-123",
            title="   ",
            active_model_id="gpt-4o",
            created_at=now,
            updated_at=now
        )
        result = session.get_display_title()
        assert result == "   "

    def test_session_different_model_ids(self, sample_session):
        """Test session with different model IDs."""
        sample_session.active_model_id = "gpt-3.5-turbo"
        assert sample_session.active_model_id == "gpt-3.5-turbo"

    def test_session_created_and_updated_times(self, sample_session):
        """Test created_at and updated_at can be different."""
        sample_session.updated_at = sample_session.created_at + timedelta(hours=1)
        assert sample_session.updated_at > sample_session.created_at

    def test_session_model_dump(self, sample_session):
        """Test session model_dump method."""
        data = sample_session.model_dump()
        assert data["id"] == 1
        assert data["user_id"] == "user-uuid-123"
        assert data["title"] == "Test Session"
        assert data["active_model_id"] == "gpt-4o"

    def test_session_model_dump_json(self, sample_session):
        """Test session model_dump_json method."""
        json_str = sample_session.model_dump_json()
        assert "user-uuid-123" in json_str
        assert "Test Session" in json_str

    def test_session_unicode_title(self):
        """Test session with unicode title."""
        now = datetime.now()
        session = Session(
            id=1,
            user_id="user-uuid-123",
            title="测试会话",
            active_model_id="gpt-4o",
            created_at=now,
            updated_at=now
        )
        assert session.title == "测试会话"

    def test_session_long_title(self):
        """Test session with long title."""
        now = datetime.now()
        long_title = "A" * 500
        session = Session(
            id=1,
            user_id="user-uuid-123",
            title=long_title,
            active_model_id="gpt-4o",
            created_at=now,
            updated_at=now
        )
        assert len(session.title) == 500

    def test_session_zero_id(self):
        """Test session with id=0."""
        now = datetime.now()
        session = Session(
            id=0,
            user_id="user-uuid-123",
            title="Test",
            active_model_id="gpt-4o",
            created_at=now,
            updated_at=now
        )
        assert session.id == 0

    def test_session_negative_id(self):
        """Test session with negative id."""
        now = datetime.now()
        session = Session(
            id=-1,
            user_id="user-uuid-123",
            title="Test",
            active_model_id="gpt-4o",
            created_at=now,
            updated_at=now
        )
        assert session.id == -1

    def test_session_different_user_ids(self):
        """Test session with different user IDs."""
        now = datetime.now()
        session1 = Session(
            id=1,
            user_id="user-1",
            title="Test",
            active_model_id="gpt-4o",
            created_at=now,
            updated_at=now
        )
        session2 = Session(
            id=2,
            user_id="user-2",
            title="Test",
            active_model_id="gpt-4o",
            created_at=now,
            updated_at=now
        )
        assert session1.user_id == "user-1"
        assert session2.user_id == "user-2"

    def test_session_is_pydantic_model(self, sample_session):
        """Test session is a Pydantic BaseModel."""
        assert hasattr(sample_session, 'model_dump')
        assert hasattr(sample_session, 'model_dump_json')

    def test_session_timestamps_datetime_type(self, sample_session):
        """Test timestamps are datetime objects."""
        assert isinstance(sample_session.created_at, datetime)
        assert isinstance(sample_session.updated_at, datetime)

    def test_session_comparison_by_id(self):
        """Test sessions can be compared by id."""
        now = datetime.now()
        session1 = Session(
            id=1,
            user_id="user-1",
            title="Test1",
            active_model_id="gpt-4o",
            created_at=now,
            updated_at=now
        )
        session2 = Session(
            id=2,
            user_id="user-1",
            title="Test2",
            active_model_id="gpt-4o",
            created_at=now,
            updated_at=now
        )
        assert session1.id < session2.id
