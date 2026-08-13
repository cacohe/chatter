"""Tests for knowledge service and loader helpers."""

from pathlib import Path

import pytest
from llama_index.core import Document

from app.services.knowledge.delete_document import DeleteDocument
from app.services.knowledge.ingest_web import IngestWeb
from app.services.knowledge.list_chunks import ListChunks
from app.services.knowledge.reload import ReloadKnowledge
from app.services.knowledge.sync_database import SyncDatabase
from app.services.knowledge.upload_files import UploadFiles
from domain.exceptions import BusinessException
from domain.schemas.knowledge import ReloadKnowledgeRequest
from infra.rag.loader import (
    ingest_llama_documents,
    load_docs,
    validate_chunk_params,
)
from infra.rag.store import (
    KnowledgeStore,
    get_knowledge_store,
    set_knowledge_store,
)


@pytest.fixture(autouse=True)
def reset_store():
    set_knowledge_store(KnowledgeStore())
    yield
    set_knowledge_store(KnowledgeStore())


class TestChunkHelpers:
    def test_validate_chunk_params_rejects_large_overlap(self):
        with pytest.raises(ValueError, match="chunk_overlap"):
            validate_chunk_params(100, 100)


class TestKnowledgeUseCases:
    def test_reload_with_custom_chunk_params(self, tmp_path: Path):
        doc = tmp_path / "demo.md"
        doc.write_text("年假政策说明。" * 30, encoding="utf-8")
        load_docs(str(tmp_path), chunk_size=200, overlap=20)

        status = ReloadKnowledge().execute(
            ReloadKnowledgeRequest(chunk_size=80, chunk_overlap=10)
        )

        assert status.document_count == 1
        assert status.chunk_size == 80
        assert status.chunk_overlap == 10
        assert status.chunk_count >= 2

    def test_upload_files(self, tmp_path: Path, monkeypatch):
        monkeypatch.setattr(
            "infra.config.settings.rag_settings.docs_path",
            str(tmp_path),
        )
        content = "上传测试文档内容。" * 20
        status = UploadFiles().execute(
            [("upload.md", content.encode("utf-8"))],
            chunk_size=60,
            overlap=10,
        )

        assert status.document_count == 1
        assert status.chunk_count >= 1
        assert not (tmp_path / "upload.md").exists()

    def test_reload_keeps_memory_upload(self, tmp_path: Path, monkeypatch):
        monkeypatch.setattr(
            "infra.config.settings.rag_settings.docs_path",
            str(tmp_path),
        )
        (tmp_path / "disk.md").write_text("磁盘文档内容。" * 10, encoding="utf-8")
        load_docs(str(tmp_path), chunk_size=80, overlap=10)

        UploadFiles().execute(
            [("memory.md", ("内存文档内容。" * 10).encode("utf-8"))],
            chunk_size=80,
            overlap=10,
        )
        status = ReloadKnowledge().execute(
            ReloadKnowledgeRequest(chunk_size=80, chunk_overlap=10)
        )
        names = [doc.name for doc in status.documents]
        assert "disk.md" in names
        assert "memory.md" in names
        assert not (tmp_path / "memory.md").exists()

    def test_upload_empty_files_raises(self):
        with pytest.raises(BusinessException):
            UploadFiles().execute([])

    def test_sync_database(self, tmp_path: Path, monkeypatch):
        import sqlite3

        monkeypatch.setattr(
            "infra.config.settings.rag_settings.docs_path",
            str(tmp_path),
        )
        db_path = tmp_path / "hr.db"
        conn = sqlite3.connect(db_path)
        conn.execute("CREATE TABLE policy (body TEXT)")
        conn.execute("INSERT INTO policy VALUES (?)", ("公司年假 10 天。",))
        conn.commit()
        conn.close()

        from domain.schemas.knowledge import SyncDatabaseRequest

        status = SyncDatabase().execute(
            SyncDatabaseRequest(
                uri=f"sqlite:///{db_path}",
                query="SELECT body FROM policy",
                name="hr",
                chunk_size=80,
                chunk_overlap=10,
            )
        )
        assert status.document_count >= 1
        assert any(
            name.startswith("db/hr/") for name in [d.name for d in status.documents]
        )
        assert not (tmp_path / "db").exists()

    def test_ingest_web_stays_in_memory(self, tmp_path: Path, monkeypatch):
        from unittest.mock import patch

        from llama_index.core import Document

        from domain.schemas.knowledge import IngestWebRequest

        monkeypatch.setattr(
            "infra.config.settings.rag_settings.docs_path",
            str(tmp_path),
        )
        with patch(
            "app.services.knowledge.ingest_web.load_web_documents",
            return_value=[
                Document(
                    text="公司年假 10 天。",
                    metadata={"doc_name": "web/example/0.md"},
                )
            ],
        ):
            status = IngestWeb().execute(
                IngestWebRequest(
                    url="https://example.com/leave",
                    chunk_size=80,
                    chunk_overlap=10,
                )
            )

        assert any(
            name.startswith("web/") for name in [d.name for d in status.documents]
        )
        assert not (tmp_path / "web").exists()

    def test_list_chunks_preview(self):
        store = get_knowledge_store()
        store.chunk_size = 100
        store.chunk_overlap = 10
        ingest_llama_documents(
            store,
            [Document(text="hello world", metadata={"doc_name": "a.md"})],
            chunk_size=100,
            overlap=10,
        )

        previews = ListChunks().execute(limit=5)
        assert len(previews) == 1
        assert previews[0].content == "hello world"

    def test_ingest_web_empty_keeps_existing_docs(self, tmp_path: Path, monkeypatch):
        from unittest.mock import patch

        from domain.schemas.knowledge import IngestWebRequest

        monkeypatch.setattr(
            "infra.config.settings.rag_settings.docs_path",
            str(tmp_path),
        )
        store = get_knowledge_store()
        store.docs_path = str(tmp_path)
        ingest_llama_documents(
            store,
            [Document(text="existing policy", metadata={"doc_name": "old.md"})],
            chunk_size=80,
            overlap=10,
        )

        with patch(
            "app.services.knowledge.ingest_web.load_web_documents",
            return_value=[Document(text="   ")],
        ):
            with pytest.raises(BusinessException, match="没有可导入的知识内容"):
                IngestWeb().execute(
                    IngestWebRequest(url="https://example.com", chunk_size=80)
                )

        assert get_knowledge_store().document_names == ["old.md"]

    def test_delete_document_removes_file_and_chunks(self, tmp_path: Path):
        nested = tmp_path / "web" / "example"
        nested.mkdir(parents=True)
        (nested / "0.md").write_text("网页正文内容。", encoding="utf-8")
        (tmp_path / "keep.md").write_text("保留文档内容。", encoding="utf-8")
        load_docs(str(tmp_path), chunk_size=80, overlap=10)

        status = DeleteDocument().execute("web/example/0.md")

        assert "web/example/0.md" not in [doc.name for doc in status.documents]
        assert any(doc.name == "keep.md" for doc in status.documents)
        assert not (tmp_path / "web" / "example" / "0.md").exists()
        assert not (tmp_path / "web").exists()
        assert (tmp_path / "keep.md").exists()

    def test_delete_missing_document_raises(self):
        with pytest.raises(BusinessException, match="文档不存在"):
            DeleteDocument().execute("missing.md")
