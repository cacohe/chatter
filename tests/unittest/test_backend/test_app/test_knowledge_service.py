"""Tests for knowledge service and loader helpers."""

from pathlib import Path

import pytest

from src.backend.app.services.knowledge import KnowledgeService
from src.backend.domain.exceptions import BusinessException
from src.backend.infra.rag.loader import (
    chunk_text,
    ingest_text,
    load_docs,
    validate_chunk_params,
)
from src.backend.infra.rag.store import (
    KnowledgeStore,
    get_knowledge_store,
    set_knowledge_store,
)
from src.shared.schemas.knowledge import ReloadKnowledgeRequest


@pytest.fixture(autouse=True)
def reset_store():
    set_knowledge_store(KnowledgeStore())
    yield
    set_knowledge_store(KnowledgeStore())


class TestChunkHelpers:
    def test_chunk_text_with_overlap(self):
        text = "a" * 100
        chunks = chunk_text(text, chunk_size=40, overlap=10)
        assert len(chunks) >= 2
        assert all(len(chunk) <= 40 for chunk in chunks)

    def test_validate_chunk_params_rejects_large_overlap(self):
        with pytest.raises(ValueError, match="chunk_overlap"):
            validate_chunk_params(100, 100)


class TestKnowledgeService:
    def test_reload_with_custom_chunk_params(self, tmp_path: Path):
        doc = tmp_path / "demo.md"
        doc.write_text("年假政策说明。" * 30, encoding="utf-8")
        load_docs(str(tmp_path), chunk_size=200, overlap=20)

        service = KnowledgeService()
        status = service.reload(
            ReloadKnowledgeRequest(chunk_size=80, chunk_overlap=10)
        )

        assert status.document_count == 1
        assert status.chunk_size == 80
        assert status.chunk_overlap == 10
        assert status.chunk_count >= 2

    def test_upload_files(self, tmp_path: Path, monkeypatch):
        monkeypatch.setattr(
            "src.shared.config.settings.rag_settings.docs_path",
            str(tmp_path),
        )
        service = KnowledgeService()
        content = "上传测试文档内容。" * 20
        status = service.upload_files(
            [("upload.md", content.encode("utf-8"))],
            chunk_size=60,
            overlap=10,
        )

        assert status.document_count == 1
        assert status.chunk_count >= 1
        assert (tmp_path / "upload.md").exists()

    def test_upload_empty_files_raises(self):
        service = KnowledgeService()
        with pytest.raises(BusinessException):
            service.upload_files([])

    def test_list_chunks_preview(self):
        store = get_knowledge_store()
        store.chunk_size = 100
        store.chunk_overlap = 10
        ingest_text(store, "a.md", "hello world", chunk_size=100, overlap=10)

        previews = KnowledgeService().list_chunks(limit=5)
        assert len(previews) == 1
        assert previews[0].content == "hello world"
