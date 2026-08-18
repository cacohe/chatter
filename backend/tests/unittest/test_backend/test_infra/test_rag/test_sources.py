"""Tests for database / web knowledge sources."""

from pathlib import Path
from unittest.mock import patch

import pytest
from llama_index.core import Document

from app.services.knowledge.shared import ingest_documents, list_chunks
from infra.rag.sources import DatabaseLoader, UploadFileLoader, WebLoader


def _public_dns():
    return [(0, 0, 0, "", ("93.184.216.34", 0))]


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
    documents = DatabaseLoader().load(uri, query)
    assert len(documents) == 1
    assert "年假" in documents[0].text or "10" in documents[0].text
    source_id = DatabaseLoader().source_id(uri, query)
    assert documents[0].doc_id.startswith(source_id)
    assert documents[0].metadata.get("source_id") == source_id


def test_load_web_documents():
    page = Document(text="公司年假 10 天。")
    with (
        patch(
            "infra.rag.sources.socket.getaddrinfo",
            return_value=_public_dns(),
        ),
        patch(
            "infra.rag.sources.WebLoader._HeaderWebPageReader.load_data",
            return_value=[page],
        ),
    ):
        documents = WebLoader().load("https://example.com/leave")

    assert len(documents) == 1
    assert "年假" in documents[0].text
    assert documents[0].doc_id == WebLoader().source_id("https://example.com/leave")


def test_load_web_documents_rejects_loading_shell():
    shell = Document(text="豆瓣 douban\n\n载入中 ...\n")
    with (
        patch(
            "infra.rag.sources.socket.getaddrinfo",
            return_value=_public_dns(),
        ),
        patch(
            "infra.rag.sources.WebLoader._HeaderWebPageReader.load_data",
            return_value=[shell],
        ),
    ):
        with pytest.raises(ValueError, match="未能从网页解析出正文"):
            WebLoader().load("https://movie.douban.com/subject/1/")


def test_load_web_documents_rejects_empty():
    with (
        patch(
            "infra.rag.sources.socket.getaddrinfo",
            return_value=_public_dns(),
        ),
        patch(
            "infra.rag.sources.WebLoader._HeaderWebPageReader.load_data",
            return_value=[Document(text="   ")],
        ),
    ):
        with pytest.raises(ValueError, match="未能从网页解析出正文"):
            WebLoader().load("https://example.com")


def test_load_web_documents_reader_failure():
    with (
        patch(
            "infra.rag.sources.socket.getaddrinfo",
            return_value=_public_dns(),
        ),
        patch(
            "infra.rag.sources.WebLoader._HeaderWebPageReader.load_data",
            side_effect=RuntimeError("blocked"),
        ),
    ):
        with pytest.raises(ValueError, match="未能从网页解析出正文"):
            WebLoader().load("https://example.com/leave")


def test_web_source_id_is_url_not_host():
    loader = WebLoader()
    leave = loader.source_id("https://example.com/leave")
    policy = loader.source_id("https://example.com/policy")
    same = loader.source_id("https://EXAMPLE.com/leave/#section")
    assert leave != policy
    assert leave == same
    assert loader.source_uri("https://example.com/a/?b=1&a=2") == loader.source_uri(
        "https://example.com/a?a=2&b=1"
    )


def test_database_source_id_is_uri_and_query():
    loader = DatabaseLoader()
    uri = "sqlite:///./a.db"
    first = loader.source_id(uri, "SELECT body FROM policy")
    second = loader.source_id(uri, "SELECT title FROM policy")
    same = loader.source_id(uri, "SELECT   body FROM policy")
    other_db = loader.source_id("sqlite:///./b.db", "SELECT body FROM policy")
    assert first != second
    assert first == same
    assert first != other_db


def test_web_rejects_loopback_and_private_ips():
    loader = WebLoader()
    for url in (
        "http://127.0.0.1/health",
        "http://10.0.0.1/docs",
        "http://[::ffff:127.0.0.1]/",
    ):
        with pytest.raises(ValueError, match="不允许抓取内网或本机地址"):
            loader.load(url)


def test_web_rejects_missing_host():
    with pytest.raises(ValueError, match="网页地址缺少主机名"):
        WebLoader().load("https:///path-only")


def test_database_source_uri_hides_password():
    loader = DatabaseLoader()
    uri = "postgresql://user:secret@db.example.com:5432/app"
    hidden = loader.source_uri(uri)
    assert "secret" not in hidden
    assert ":***@" in hidden
    assert loader.source_id(uri, "SELECT 1") == loader.source_id(
        "postgresql://user:other@db.example.com:5432/app", "SELECT 1"
    )


def test_database_rejects_empty_uri_and_non_select():
    loader = DatabaseLoader()
    with pytest.raises(ValueError, match="请提供数据库连接串"):
        loader.load("  ", "SELECT 1")
    with pytest.raises(ValueError, match="仅允许执行 SELECT 查询"):
        loader.load("sqlite:///./a.db", "WITH x AS (SELECT 1) SELECT * FROM x")


def test_file_source_id_rejects_invalid_name():
    with pytest.raises(ValueError, match="无效的文件名"):
        UploadFileLoader().source_id("..")


def test_ingest_documents():
    ingest_documents(
        [Document(text="hello world", doc_id="a.md")],
        chunk_size=100,
        overlap=10,
    )
    previews = list_chunks(doc_id="a.md", limit=5)
    assert len(previews) == 1
    assert previews[0].get_content() == "hello world"
