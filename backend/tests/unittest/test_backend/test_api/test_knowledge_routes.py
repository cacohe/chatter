"""Tests for knowledge API routes."""

import pytest
from fastapi.testclient import TestClient
from llama_index.core import Document

from app.services.knowledge.shared import ingest_documents
from main import app


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture(autouse=True)
def setup_docs():
    ingest_documents(
        [Document(text="公司年假 10 天。", doc_id="policy.md")],
        chunk_size=100,
        overlap=10,
    )
    yield


class TestKnowledgeRoutes:
    def test_get_summary(self, client: TestClient):
        response = client.get("/api/v1.0/knowledge/summary")
        assert response.status_code == 200
        data = response.json()
        assert data["document_count"] == 1
        assert data["chunk_count"] >= 1
        assert data["chunk_size"] == 100

    def test_upload(self, client: TestClient):
        response = client.post(
            "/api/v1.0/knowledge/upload",
            files=[
                ("files", ("new.md", "new upload content".encode(), "text/markdown"))
            ],
            data={"chunk_size": "80", "chunk_overlap": "10"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["document_count"] >= 1

    def test_list_chunks(self, client: TestClient):
        response = client.get("/api/v1.0/knowledge/chunks", params={"limit": 5})
        assert response.status_code == 200
        chunks = response.json()
        assert len(chunks) >= 1
        assert "content" in chunks[0]

    def test_delete_document(self, client: TestClient):
        response = client.delete(
            "/api/v1.0/knowledge/documents",
            params={"doc_name": "policy.md"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["document_count"] == 0

    def test_delete_missing_document(self, client: TestClient):
        response = client.delete(
            "/api/v1.0/knowledge/documents",
            params={"doc_name": "missing.md"},
        )
        assert response.status_code == 404
