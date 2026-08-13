"""Tests for database / web knowledge sources."""

from pathlib import Path
from unittest.mock import patch

import pytest
from llama_index.core import Document

from infra.rag.loader import delete_stored_document, ingest_llama_documents, load_docs
from infra.rag.sources import (
    load_database_documents,
    load_web_documents,
)
from infra.rag.store import KnowledgeStore, set_knowledge_store


@pytest.fixture(autouse=True)
def reset_store():
    set_knowledge_store(KnowledgeStore())
    yield
    set_knowledge_store(KnowledgeStore())


def test_sync_sqlite_database(tmp_path: Path):
    db_path = tmp_path / "source.db"
    import sqlite3

    conn = sqlite3.connect(db_path)
    conn.execute("CREATE TABLE articles (title TEXT, body TEXT)")
    conn.execute(
        "INSERT INTO articles VALUES (?, ?)",
        ("年假", "公司年假 10 天。"),
    )
    conn.commit()
    conn.close()

    documents = load_database_documents(
        f"sqlite:///{db_path}",
        "SELECT title, body FROM articles",
        prefix="db/articles",
    )
    assert len(documents) == 1
    assert "年假" in documents[0].get_content() or "10" in documents[0].get_content()
    assert documents[0].metadata["doc_name"].startswith("db/articles/")


def test_load_web_documents():
    page = Document(text="公司年假 10 天。")
    with patch(
        "infra.rag.sources.HeaderWebPageReader.load_data",
        return_value=[page],
    ):
        documents = load_web_documents(
            "https://example.com/leave",
            prefix="web/example",
        )

    assert len(documents) == 1
    assert "年假" in documents[0].get_content()
    assert documents[0].metadata["doc_name"].startswith("web/example/")


def test_load_web_documents_rejects_loading_shell():
    shell = Document(text="豆瓣 douban\n\n载入中 ...\n")
    with patch(
        "infra.rag.sources.HeaderWebPageReader.load_data",
        return_value=[shell],
    ):
        with pytest.raises(ValueError, match="未能从网页解析出正文"):
            load_web_documents(
                "https://movie.douban.com/subject/1/",
                prefix="web/movie",
            )


def test_load_web_documents_rejects_empty():
    with patch(
        "infra.rag.sources.HeaderWebPageReader.load_data",
        return_value=[Document(text="   ")],
    ):
        with pytest.raises(ValueError, match="未能从网页解析出正文"):
            load_web_documents("https://example.com", prefix="web/empty")


def test_load_web_documents_reader_failure():
    with patch(
        "infra.rag.sources.HeaderWebPageReader.load_data",
        side_effect=RuntimeError("blocked"),
    ):
        with pytest.raises(ValueError, match="未能从网页解析出正文"):
            load_web_documents(
                "https://example.com/leave",
                prefix="web/example",
            )


def test_load_docs_reads_markdown(tmp_path: Path):
    (tmp_path / "leave.md").write_text("公司年假 10 天。", encoding="utf-8")
    store = load_docs(str(tmp_path), chunk_size=100, overlap=10)
    assert store.document_count >= 1


def test_ingest_llama_documents():
    store = KnowledgeStore()
    ingest_llama_documents(
        store,
        [Document(text="hello world", metadata={"doc_name": "a.md"})],
        chunk_size=100,
        overlap=10,
    )
    assert store.document_count == 1
    assert store.nodes[0].get_content() == "hello world"


def test_delete_stored_document_rejects_path_escape(tmp_path: Path):
    docs = tmp_path / "docs"
    docs.mkdir()
    secret = tmp_path / "secret.md"
    secret.write_text("secret", encoding="utf-8")
    with pytest.raises(ValueError, match="无效的文档路径"):
        delete_stored_document(str(docs), "../secret.md")
    assert secret.exists()
