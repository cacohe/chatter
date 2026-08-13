"""Tests for RAG loader and retriever."""

from pathlib import Path

from llama_index.core.schema import TextNode

from infra.rag.loader import documents_from_upload, load_docs
from infra.rag.retriever import format_context, retrieve


def test_load_docs_from_sample_dir():
    docs_path = Path(__file__).resolve().parents[5] / "data" / "docs"
    store = load_docs(str(docs_path))
    assert store.document_count >= 1
    assert len(store.nodes) >= 1


def test_documents_from_upload_markdown():
    documents = documents_from_upload(
        "policy.md", b"# Leave\n\nCompany leave is 10 days."
    )
    assert len(documents) == 1
    assert documents[0].metadata["doc_name"] == "policy.md"
    assert "10 days" in documents[0].get_content()


def test_retrieve_leave_policy():
    docs_path = Path(__file__).resolve().parents[5] / "data" / "docs"
    load_docs(str(docs_path))
    nodes = retrieve("年假有几天", top_k=3)
    assert len(nodes) >= 1
    joined = "\n".join(node.get_content() for node in nodes)
    assert "年假" in joined or "10" in joined


def test_format_context():
    text = format_context([TextNode(text="hello", metadata={"doc_name": "a.md"})])
    assert "a.md" in text
    assert "hello" in text
