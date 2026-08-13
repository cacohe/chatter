"""Tests for KnowledgeClient."""

from unittest.mock import MagicMock, patch

import pytest

from services.knowledge import KnowledgeClient


class TestKnowledgeClient:
    @pytest.fixture
    def client(self):
        knowledge = KnowledgeClient()
        knowledge.base_url = "http://backend.test/api/v1.0"
        return knowledge

    def test_get_status(self, client):
        mock_response = MagicMock()
        mock_response.json.return_value = {"doc_count": 1}

        with patch(
            "services.knowledge.requests.get", return_value=mock_response
        ) as get:
            result = client.get_status()

        assert result == {"doc_count": 1}
        get.assert_called_once_with(
            "http://backend.test/api/v1.0/knowledge/status", timeout=30
        )
        mock_response.raise_for_status.assert_called_once()

    def test_reload(self, client):
        mock_response = MagicMock()
        mock_response.json.return_value = {"ok": True}

        with patch(
            "services.knowledge.requests.post", return_value=mock_response
        ) as post:
            result = client.reload(chunk_size=400, chunk_overlap=40)

        assert result == {"ok": True}
        post.assert_called_once_with(
            "http://backend.test/api/v1.0/knowledge/reload",
            json={"chunk_size": 400, "chunk_overlap": 40},
            timeout=60,
        )

    def test_upload_files_with_chunk_params(self, client):
        mock_response = MagicMock()
        mock_response.json.return_value = {"uploaded": 1}

        with patch(
            "services.knowledge.requests.post", return_value=mock_response
        ) as post:
            result = client.upload_files(
                [("leave.md", "年假 10 天".encode())],
                chunk_size=500,
                chunk_overlap=50,
            )

        assert result == {"uploaded": 1}
        kwargs = post.call_args.kwargs
        assert post.call_args.args[0] == "http://backend.test/api/v1.0/knowledge/upload"
        assert kwargs["data"] == {"chunk_size": "500", "chunk_overlap": "50"}
        assert kwargs["files"] == [
            ("files", ("leave.md", "年假 10 天".encode(), "text/plain"))
        ]
        assert kwargs["timeout"] == 60

    def test_list_chunks_with_doc_name(self, client):
        mock_response = MagicMock()
        mock_response.json.return_value = [{"doc_name": "leave.md"}]

        with patch(
            "services.knowledge.requests.get", return_value=mock_response
        ) as get:
            result = client.list_chunks(doc_name="leave.md", limit=5)

        assert result == [{"doc_name": "leave.md"}]
        get.assert_called_once_with(
            "http://backend.test/api/v1.0/knowledge/chunks",
            params={"limit": 5, "doc_name": "leave.md"},
            timeout=30,
        )

    def test_list_chunks_without_doc_name(self, client):
        mock_response = MagicMock()
        mock_response.json.return_value = []

        with patch(
            "services.knowledge.requests.get", return_value=mock_response
        ) as get:
            client.list_chunks()

        get.assert_called_once_with(
            "http://backend.test/api/v1.0/knowledge/chunks",
            params={"limit": 20},
            timeout=30,
        )
