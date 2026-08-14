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

    def test_get_summary(self, client):
        mock_response = MagicMock()
        mock_response.json.return_value = {"doc_count": 1}

        with patch(
            "services.knowledge.requests.get", return_value=mock_response
        ) as get:
            result = client.get_summary()

        assert result == {"doc_count": 1}
        get.assert_called_once_with(
            "http://backend.test/api/v1.0/knowledge/summary", timeout=30
        )
        mock_response.raise_for_status.assert_called_once()

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
            ("files", ("leave.md", "年假 10 天".encode(), "text/markdown"))
        ]
        assert kwargs["timeout"] == 60

    def test_sync_database(self, client):
        mock_response = MagicMock()
        mock_response.json.return_value = {"ok": True}

        with patch(
            "services.knowledge.requests.post", return_value=mock_response
        ) as post:
            result = client.sync_database(
                "sqlite:///./data.db",
                "SELECT body FROM policy",
                name="hr",
                chunk_size=80,
                chunk_overlap=10,
            )

        assert result == {"ok": True}
        post.assert_called_once_with(
            "http://backend.test/api/v1.0/knowledge/sync/database",
            json={
                "uri": "sqlite:///./data.db",
                "query": "SELECT body FROM policy",
                "name": "hr",
                "chunk_size": 80,
                "chunk_overlap": 10,
            },
            timeout=60,
        )

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

    def test_delete_document(self, client):
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.json.return_value = {"document_count": 0}

        with patch(
            "services.knowledge.requests.delete", return_value=mock_response
        ) as delete:
            result = client.delete_document("web/example/0.md")

        assert result == {"document_count": 0}
        delete.assert_called_once_with(
            "http://backend.test/api/v1.0/knowledge/documents",
            params={"doc_name": "web/example/0.md"},
            timeout=30,
        )

    def test_ingest_web_surfaces_backend_detail(self, client):
        mock_response = MagicMock()
        mock_response.ok = False
        mock_response.status_code = 400
        mock_response.json.return_value = {"detail": "未能从网页解析出正文"}

        with patch("services.knowledge.requests.post", return_value=mock_response):
            with pytest.raises(RuntimeError, match="未能从网页解析出正文"):
                client.ingest_web("https://example.com/leave")
