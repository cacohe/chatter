"""Tests for knowledge service and domain ingest rules."""

from pathlib import Path
from unittest.mock import patch

import pytest
from llama_index.core import Document

from app.services.knowledge.delete_document import DeleteDocument
from app.services.knowledge.ingest_web import IngestWeb
from app.services.knowledge.list_chunks import ListChunks
from app.services.knowledge.operations import ingest_documents, list_chunks, snapshot
from app.services.knowledge.sync_database import SyncDatabase
from app.services.knowledge.upload_files import UploadFiles
from domain.exceptions import BusinessException
from domain.models.knowledge import validate_chunk_params
from infra.rag.identity import web_source_id


def _ingest(doc_id: str, text: str, *, chunk_size: int = 80, overlap: int = 10):
    ingest_documents(
        [Document(text=text, doc_id=doc_id)],
        chunk_size=chunk_size,
        overlap=overlap,
    )


def _chunk_text(doc_name: str) -> str:
    return "".join(
        item.get_content() for item in list_chunks(doc_id=doc_name, limit=1000)
    )


def _web_doc(url: str, text: str) -> list[Document]:
    source_id = web_source_id(url)
    return [Document(text=text, doc_id=source_id, metadata={"source_id": source_id})]


class TestChunkHelpers:
    def test_validate_chunk_params_rejects_large_overlap(self):
        with pytest.raises(ValueError, match="chunk_overlap"):
            validate_chunk_params(100, 100)


class TestKnowledgeUseCases:
    def test_new_ingest_does_not_rechunk_existing(self):
        _ingest("demo.md", "年假政策说明。" * 30, chunk_size=200, overlap=20)
        before = _chunk_text("demo.md")

        status = UploadFiles().execute(
            [("later.md", ("后续上传文档内容。" * 20).encode("utf-8"))],
            chunk_size=60,
            overlap=10,
        )

        assert _chunk_text("demo.md") == before
        assert status.chunk_params.size == 60
        assert status.chunk_params.overlap == 10
        assert any(doc.name == "later.md" for doc in status.documents)

    def test_upload_files(self):
        content = "上传测试文档内容。" * 20
        status = UploadFiles().execute(
            [("upload.md", content.encode("utf-8"))],
            chunk_size=60,
            overlap=10,
        )

        assert status.document_count == 1
        assert status.chunk_count >= 1

    def test_upload_empty_files_raises(self):
        with pytest.raises(BusinessException):
            UploadFiles().execute([])

    def test_sync_database(self, tmp_path: Path):
        import sqlite3

        db_path = tmp_path / "hr.db"
        conn = sqlite3.connect(db_path)
        conn.execute("CREATE TABLE policy (body TEXT)")
        conn.execute("INSERT INTO policy VALUES (?)", ("公司年假 10 天。",))
        conn.commit()
        conn.close()

        status = SyncDatabase().execute(
            f"sqlite:///{db_path}",
            "SELECT body FROM policy",
            chunk_size=80,
            overlap=10,
        )
        assert status.document_count >= 1
        assert any(
            name.startswith("db/") for name in [d.name for d in status.documents]
        )

    def test_ingest_web_stays_in_memory(self):
        url = "https://example.com/leave"
        with patch(
            "infra.rag.sources.LlamaWebLoader.load",
            return_value=_web_doc(url, "公司年假 10 天。"),
        ):
            status = IngestWeb().execute(url, chunk_size=80, overlap=10)

        assert any(
            name.startswith("web/") for name in [d.name for d in status.documents]
        )

    def test_list_chunks_preview(self):
        _ingest("a.md", "hello world", chunk_size=100, overlap=10)
        previews = ListChunks().execute(limit=5)
        assert len(previews) == 1
        assert previews[0].get_content() == "hello world"

    def test_ingest_web_empty_keeps_existing_docs(self):
        _ingest("old.md", "existing policy")
        with patch(
            "infra.rag.sources.LlamaWebLoader.load",
            return_value=[
                Document(text="   ", doc_id="web/empty", metadata={"source_id": "web/empty"})
            ],
        ):
            with pytest.raises(BusinessException, match="没有可导入的知识内容"):
                IngestWeb().execute("https://example.com", chunk_size=80)

        assert [item.name for item in snapshot().documents] == ["old.md"]

    def test_ingest_web_keeps_other_urls(self):
        def fake_load(url: str):
            return _web_doc(url, f"正文 {url}")

        with patch("infra.rag.sources.LlamaWebLoader.load", side_effect=fake_load):
            IngestWeb().execute("https://example.com/a", chunk_size=80)
            status = IngestWeb().execute("https://example.com/b", chunk_size=80)

        names = [doc.name for doc in status.documents]
        assert status.document_count == 2
        assert web_source_id("https://example.com/a") in names
        assert web_source_id("https://example.com/b") in names

    def test_ingest_web_same_url_overwrites(self):
        url = "https://example.com/leave"
        with patch(
            "infra.rag.sources.LlamaWebLoader.load",
            return_value=_web_doc(url, "第一版年假政策。"),
        ):
            IngestWeb().execute(url, chunk_size=80)
        with patch(
            "infra.rag.sources.LlamaWebLoader.load",
            return_value=_web_doc(url, "第二版年假政策。"),
        ):
            status = IngestWeb().execute(url, chunk_size=80)

        joined = _chunk_text(web_source_id(url))
        assert status.document_count == 1
        assert "第二版" in joined
        assert "第一版" not in joined

    def test_sync_database_keeps_other_queries(self, tmp_path: Path):
        import sqlite3

        db_path = tmp_path / "hr.db"
        conn = sqlite3.connect(db_path)
        conn.execute("CREATE TABLE policy (id INTEGER, body TEXT)")
        conn.execute("INSERT INTO policy VALUES (1, '年假 10 天。')")
        conn.execute("INSERT INTO policy VALUES (2, '病假 5 天。')")
        conn.commit()
        conn.close()

        uri = f"sqlite:///{db_path}"
        SyncDatabase().execute(
            uri,
            "SELECT id, body FROM policy WHERE id = 1",
            chunk_size=80,
            overlap=10,
        )
        status = SyncDatabase().execute(
            uri,
            "SELECT id, body FROM policy WHERE id = 2",
            chunk_size=80,
            overlap=10,
        )
        assert status.document_count == 2

    def test_sync_database_same_query_replaces_rows(self, tmp_path: Path):
        import sqlite3

        db_path = tmp_path / "hr.db"
        conn = sqlite3.connect(db_path)
        conn.execute("CREATE TABLE policy (id INTEGER, body TEXT)")
        conn.execute("INSERT INTO policy VALUES (1, '年假 10 天。')")
        conn.execute("INSERT INTO policy VALUES (2, '病假 5 天。')")
        conn.commit()
        conn.close()

        uri = f"sqlite:///{db_path}"
        query = "SELECT id, body FROM policy"
        first = SyncDatabase().execute(uri, query, chunk_size=80, overlap=10)
        assert first.document_count == 2

        conn = sqlite3.connect(db_path)
        conn.execute("DELETE FROM policy WHERE id = 2")
        conn.commit()
        conn.close()

        second = SyncDatabase().execute(uri, query, chunk_size=80, overlap=10)
        assert second.document_count == 1
        assert "年假" in _chunk_text(second.documents[0].name)

    def test_delete_document_removes_chunks(self):
        ingest_documents(
            [
                Document(text="网页正文内容。", doc_id="remove.md"),
                Document(text="保留文档内容。", doc_id="keep.md"),
            ],
            chunk_size=80,
            overlap=10,
        )
        status = DeleteDocument().execute("remove.md")
        assert "remove.md" not in [doc.name for doc in status.documents]
        assert any(doc.name == "keep.md" for doc in status.documents)

    def test_delete_missing_document_raises(self):
        with pytest.raises(BusinessException, match="文档不存在"):
            DeleteDocument().execute("missing.md")
