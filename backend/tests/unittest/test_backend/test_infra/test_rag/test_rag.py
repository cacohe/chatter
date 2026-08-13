"""Tests for RAG loader and retriever."""

from pathlib import Path

from infra.rag.loader import load_docs
from infra.rag.retriever import format_context, retrieve
from infra.rag.store import DocumentChunk


def test_load_docs_from_sample_dir():
    docs_path = Path(__file__).resolve().parents[5] / "data" / "docs"
    # parents: test_rag -> test_infra -> test_backend -> unittest -> tests -> project root
    # Wait: test file at tests/unittest/test_backend/test_infra/test_rag/test_rag.py
    # parents[0]=test_rag, [1]=test_infra, [2]=test_backend, [3]=unittest, [4]=tests, [5]=root
    store = load_docs(str(docs_path))
    assert store.document_count >= 1
    assert len(store.chunks) >= 1


def test_retrieve_leave_policy():
    docs_path = Path(__file__).resolve().parents[5] / "data" / "docs"
    load_docs(str(docs_path))
    chunks = retrieve("年假有几天", top_k=3)
    assert len(chunks) >= 1
    joined = "\n".join(c.content for c in chunks)
    assert "年假" in joined or "10" in joined


def test_format_context():
    text = format_context(
        [DocumentChunk(doc_id="1", doc_name="a.md", content="hello", chunk_index=0)]
    )
    assert "a.md" in text
    assert "hello" in text
