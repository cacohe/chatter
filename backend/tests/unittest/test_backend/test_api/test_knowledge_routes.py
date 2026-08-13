"""Tests for knowledge API routes."""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from infra.rag.loader import load_docs
from main import app


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture(autouse=True)
def setup_docs(tmp_path: Path):
    doc = tmp_path / "policy.md"
    doc.write_text("公司年假 10 天。", encoding="utf-8")
    load_docs(str(tmp_path), chunk_size=100, overlap=10)
    yield


class TestKnowledgeRoutes:
    def test_get_status(self, client: TestClient):
        response = client.get("/api/v1.0/knowledge/status")
        assert response.status_code == 200
        data = response.json()
        assert data["document_count"] == 1
        assert data["chunk_count"] >= 1
        assert data["chunk_size"] == 100

    def test_reload(self, client: TestClient):
        response = client.post(
            "/api/v1.0/knowledge/reload",
            json={"chunk_size": 50, "chunk_overlap": 5},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["chunk_size"] == 50
        assert data["chunk_overlap"] == 5

    def test_upload(self, client: TestClient, tmp_path: Path, monkeypatch):
        monkeypatch.setattr(
            "infra.config.settings.rag_settings.docs_path",
            str(tmp_path),
        )
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
