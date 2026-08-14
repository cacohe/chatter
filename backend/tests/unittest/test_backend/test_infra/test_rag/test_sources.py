"""Tests for database / web knowledge sources."""

from pathlib import Path
from unittest.mock import patch

import pytest
from llama_index.core import Document

from app.services.knowledge.operations import ingest_documents, list_chunks
from infra.rag.identity import canonicalize_url, database_source_id, web_source_id
from infra.rag.sources import LlamaDatabaseLoader, LlamaWebLoader


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

    uri = f"sqlite:///{db_path}"
    query = "SELECT title, body FROM articles"
    documents = LlamaDatabaseLoader().load(uri, query)
    assert len(documents) == 1
    assert "年假" in documents[0].text or "10" in documents[0].text
    source_id = database_source_id(uri, query)
    assert documents[0].doc_id.startswith(source_id)
    assert documents[0].metadata.get("source_id") == source_id


def test_load_web_documents():
    page = Document(text="公司年假 10 天。")
    with patch(
        "infra.rag.sources.HeaderWebPageReader.load_data",
        return_value=[page],
    ):
        documents = LlamaWebLoader().load("https://example.com/leave")

    assert len(documents) == 1
    assert "年假" in documents[0].text
    assert documents[0].doc_id == web_source_id("https://example.com/leave")


def test_load_web_documents_rejects_loading_shell():
    shell = Document(text="豆瓣 douban\n\n载入中 ...\n")
    with patch(
        "infra.rag.sources.HeaderWebPageReader.load_data",
        return_value=[shell],
    ):
        with pytest.raises(ValueError, match="未能从网页解析出正文"):
            LlamaWebLoader().load("https://movie.douban.com/subject/1/")


def test_load_web_documents_rejects_empty():
    with patch(
        "infra.rag.sources.HeaderWebPageReader.load_data",
        return_value=[Document(text="   ")],
    ):
        with pytest.raises(ValueError, match="未能从网页解析出正文"):
            LlamaWebLoader().load("https://example.com")


def test_load_web_documents_reader_failure():
    with patch(
        "infra.rag.sources.HeaderWebPageReader.load_data",
        side_effect=RuntimeError("blocked"),
    ):
        with pytest.raises(ValueError, match="未能从网页解析出正文"):
            LlamaWebLoader().load("https://example.com/leave")


def test_web_source_id_is_url_not_host():
    leave = web_source_id("https://example.com/leave")
    policy = web_source_id("https://example.com/policy")
    same = web_source_id("https://EXAMPLE.com/leave/#section")
    assert leave != policy
    assert leave == same
    assert canonicalize_url("https://example.com/a/?b=1&a=2") == canonicalize_url(
        "https://example.com/a?a=2&b=1"
    )


def test_database_source_id_is_uri_and_query():
    uri = "sqlite:///./a.db"
    first = database_source_id(uri, "SELECT body FROM policy")
    second = database_source_id(uri, "SELECT title FROM policy")
    same = database_source_id(uri, "SELECT   body FROM policy")
    other_db = database_source_id("sqlite:///./b.db", "SELECT body FROM policy")
    assert first != second
    assert first == same
    assert first != other_db


def test_ingest_documents():
    ingest_documents(
        [Document(text="hello world", doc_id="a.md")],
        chunk_size=100,
        overlap=10,
    )
    previews = list_chunks(doc_id="a.md", limit=5)
    assert len(previews) == 1
    assert previews[0].get_content() == "hello world"
