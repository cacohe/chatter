"""Tests for API lifespan."""

from unittest.mock import MagicMock, patch

import pytest

from api.lifespan import lifespan


class TestLifespan:
    @pytest.mark.asyncio
    async def test_lifespan_loads_docs(self):
        mock_app = MagicMock()
        mock_store = MagicMock(document_count=2, nodes=[1, 2])

        with patch("api.lifespan.load_docs", return_value=mock_store) as mock_load:
            async with lifespan(mock_app):
                pass
            mock_load.assert_called_once()
