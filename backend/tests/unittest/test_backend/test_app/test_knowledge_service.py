"""Tests for knowledge service and domain ingest rules."""

from pathlib import Path
from unittest.mock import patch

import pytest
from llama_index.core import Document

from app.services.knowledge.delete_document import DeleteDocument
from app.services.knowledge.ingest_web import IngestWeb
from app.services.knowledge.list_chunks import ListChunks
from app.services.knowledge.shared import ingest_documents, list_chunks, snapshot
from app.services.knowledge.sync_database import SyncDatabase
from app.services.knowledge.upload_files import UploadFiles
from domain.exceptions import BusinessException
from domain.models.knowledge import validate_chunk_params
from infra.config import settings
from infra.rag.sources import WebLoader


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
    source_id = WebLoader().source_id(url)
    return [Document(text=text, doc_id=source_id, metadata={"source_id": source_id})]


def _set_rag_limits(monkeypatch, **updates) -> None:
    monkeypatch.setattr(
        settings,
        "rag_settings",
        settings.rag_settings.model_copy(update=updates),
    )


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

    def test_upload_rejects_too_many_files(self, monkeypatch):
        _set_rag_limits(monkeypatch, max_upload_files=1)
        with pytest.raises(BusinessException, match="最多上传 1 个文件"):
            UploadFiles().execute(
                [
                    ("a.md", "a".encode("utf-8")),
                    ("b.md", "b".encode("utf-8")),
                ]
            )

    def test_upload_rejects_large_single_file(self, monkeypatch):
        _set_rag_limits(monkeypatch, max_upload_file_bytes=4)
        with pytest.raises(BusinessException, match="超过大小上限"):
            UploadFiles().execute([("a.md", "hello".encode("utf-8"))])

    def test_upload_rejects_large_total_size(self, monkeypatch):
        _set_rag_limits(monkeypatch, max_upload_total_bytes=5)
        with pytest.raises(BusinessException, match="总大小超过上限"):
            UploadFiles().execute(
                [
                    ("a.md", "abc".encode("utf-8")),
                    ("b.md", "def".encode("utf-8")),
                ]
            )

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

    def test_sync_database_rejects_non_select(self, tmp_path: Path):
        db_path = tmp_path / "hr.db"
        with pytest.raises(BusinessException, match="仅允许执行 SELECT 查询"):
            SyncDatabase().execute(
                f"sqlite:///{db_path}",
                "DELETE FROM policy",
                chunk_size=80,
            )

    def test_sync_database_rejects_multiple_statements(self, tmp_path: Path):
        db_path = tmp_path / "hr.db"
        with pytest.raises(BusinessException, match="仅允许执行单条 SELECT 查询"):
            SyncDatabase().execute(
                f"sqlite:///{db_path}",
                "SELECT 1; SELECT 2",
                chunk_size=80,
            )

    def test_sync_database_rejects_too_many_rows(self, tmp_path: Path, monkeypatch):
        import sqlite3

        _set_rag_limits(monkeypatch, db_max_rows=1)
        db_path = tmp_path / "hr.db"
        conn = sqlite3.connect(db_path)
        conn.execute("CREATE TABLE policy (body TEXT)")
        conn.execute("INSERT INTO policy VALUES ('年假 10 天。')")
        conn.execute("INSERT INTO policy VALUES ('病假 5 天。')")
        conn.commit()
        conn.close()

        with pytest.raises(BusinessException, match="超过行数上限"):
            SyncDatabase().execute(
                f"sqlite:///{db_path}",
                "SELECT body FROM policy",
                chunk_size=80,
            )

    def test_sync_database_rejects_too_long_row(self, tmp_path: Path, monkeypatch):
        import sqlite3

        _set_rag_limits(monkeypatch, db_max_chars_per_row=5)
        db_path = tmp_path / "hr.db"
        conn = sqlite3.connect(db_path)
        conn.execute("CREATE TABLE policy (body TEXT)")
        conn.execute("INSERT INTO policy VALUES (?)", ("这是一条很长的制度文本。",))
        conn.commit()
        conn.close()

        with pytest.raises(BusinessException, match="单行数据库记录超过长度上限"):
            SyncDatabase().execute(
                f"sqlite:///{db_path}",
                "SELECT body FROM policy",
                chunk_size=80,
            )

    def test_ingest_web_stays_in_memory(self):
        url = "https://example.com/leave"
        with patch(
            "infra.rag.sources.WebLoader.load",
            return_value=_web_doc(url, "公司年假 10 天。"),
        ):
            status = IngestWeb().execute(url, chunk_size=80, overlap=10)

        assert any(
            name.startswith("web/") for name in [d.name for d in status.documents]
        )

    def test_ingest_web_rejects_non_http_scheme(self):
        with pytest.raises(BusinessException, match="仅支持 http/https"):
            IngestWeb().execute("ftp://example.com/file.txt", chunk_size=80)

    def test_ingest_web_rejects_localhost(self):
        with pytest.raises(BusinessException, match="不允许抓取内网或本机地址"):
            IngestWeb().execute("http://localhost:8000/health", chunk_size=80)

    def test_ingest_web_rejects_loopback_ip(self):
        with pytest.raises(BusinessException, match="不允许抓取内网或本机地址"):
            IngestWeb().execute("http://127.0.0.1/health", chunk_size=80)

    def test_ingest_web_rejects_too_long_content(self, monkeypatch):
        _set_rag_limits(monkeypatch, web_max_content_chars=10)
        with (
            patch(
                "infra.rag.sources.socket.getaddrinfo",
                return_value=[(0, 0, 0, "", ("93.184.216.34", 0))],
            ),
            patch(
                "infra.rag.sources.WebLoader._HeaderWebPageReader.load_data",
                return_value=[
                    Document(text="x" * 11, metadata={"url": "https://example.com"})
                ],
            ),
        ):
            with pytest.raises(BusinessException, match="网页正文超过长度上限"):
                IngestWeb().execute("https://example.com/leave", chunk_size=80)

    def test_list_chunks_preview(self):
        _ingest("a.md", "hello world", chunk_size=100, overlap=10)
        previews = ListChunks().execute(limit=5)
        assert len(previews) == 1
        assert previews[0].get_content() == "hello world"

    def test_ingest_web_empty_keeps_existing_docs(self):
        _ingest("old.md", "existing policy")
        with patch(
            "infra.rag.sources.WebLoader.load",
            return_value=[
                Document(
                    text="   ", doc_id="web/empty", metadata={"source_id": "web/empty"}
                )
            ],
        ):
            with pytest.raises(BusinessException, match="没有可导入的知识内容"):
                IngestWeb().execute("https://example.com", chunk_size=80)

        assert [item.name for item in snapshot().documents] == ["old.md"]

    def test_ingest_web_keeps_other_urls(self):
        def fake_load(url: str):
            return _web_doc(url, f"正文 {url}")

        with patch("infra.rag.sources.WebLoader.load", side_effect=fake_load):
            IngestWeb().execute("https://example.com/a", chunk_size=80)
            status = IngestWeb().execute("https://example.com/b", chunk_size=80)

        names = [doc.name for doc in status.documents]
        assert status.document_count == 2
        assert WebLoader().source_id("https://example.com/a") in names
        assert WebLoader().source_id("https://example.com/b") in names

    def test_ingest_web_same_url_overwrites(self):
        url = "https://example.com/leave"
        with patch(
            "infra.rag.sources.WebLoader.load",
            return_value=_web_doc(url, "第一版年假政策。"),
        ):
            IngestWeb().execute(url, chunk_size=80)
        with patch(
            "infra.rag.sources.WebLoader.load",
            return_value=_web_doc(url, "第二版年假政策。"),
        ):
            status = IngestWeb().execute(url, chunk_size=80)

        joined = _chunk_text(WebLoader().source_id(url))
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
