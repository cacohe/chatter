"""Tests for API lifespan."""

from unittest.mock import MagicMock

import pytest

from api.lifespan import lifespan


class TestLifespan:
    @pytest.mark.asyncio
    async def test_lifespan_starts(self):
        mock_app = MagicMock()
        async with lifespan(mock_app):
            pass
