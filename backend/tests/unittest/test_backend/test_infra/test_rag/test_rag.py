"""Tests for RAG ingest, file parsing, and retrieval."""

import pytest
from llama_index.core import Document

from app.services.knowledge.shared import ingest_documents
from infra.rag.runtime import get_retriever
from infra.rag.sources import UploadFileLoader


def test_ingest_markdown_into_knowledge_base():
    snapshot = ingest_documents(
        [Document(text="公司年假 10 天。", doc_id="leave.md")],
        chunk_size=100,
        overlap=10,
    )
    assert snapshot.document_count >= 1
    assert snapshot.chunk_count >= 1


def test_load_upload_document_markdown():
    document = UploadFileLoader().load(
        "policy.md", b"# Leave\n\nCompany leave is 10 days."
    )
    assert document.doc_id == "policy.md"
    assert document.metadata["source_id"] == "policy.md"
    assert document.metadata["source_uri"] == "file://policy.md"
    assert "10 days" in document.text


def test_load_upload_document_pdf():
    pdf = (
        b"%PDF-1.4\n"
        b"1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
        b"2 0 obj<</Type/Pages/Count 1/Kids[3 0 R]>>endobj\n"
        b"3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 200 200]"
        b"/Contents 4 0 R/Resources<</Font<</F1 5 0 R>>>>>>endobj\n"
        b"4 0 obj<</Length 51>>stream\n"
        b"BT /F1 12 Tf 10 100 Td (Company leave 10 days) Tj ET\n"
        b"endstream\nendobj\n"
        b"5 0 obj<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>endobj\n"
        b"xref\n0 6\n0000000000 65535 f \n0000000009 00000 n \n"
        b"0000000052 00000 n \n0000000101 00000 n \n0000000229 00000 n \n"
        b"0000000328 00000 n \ntrailer<</Size 6/Root 1 0 R>>\n"
        b"startxref\n406\n%%EOF\n"
    )
    document = UploadFileLoader().load("leave.pdf", pdf)
    assert document.doc_id == "leave.pdf"
    assert "10 days" in document.text


def test_load_upload_document_rejects_unknown_type():
    with pytest.raises(ValueError, match="不支持的文件类型"):
        UploadFileLoader().load("notes.docx", b"hello")


def test_load_upload_document_rejects_empty():
    with pytest.raises(ValueError, match="未能从文件中读取到文本内容"):
        UploadFileLoader().load("empty.md", b"   ")


def test_retrieve_leave_policy():
    ingest_documents(
        [Document(text="公司年假 10 天。", doc_id="leave.md")],
        chunk_size=100,
        overlap=10,
    )
    chunks = get_retriever().retrieve("年假有几天", 3)
    assert len(chunks) >= 1
    joined = "\n".join(chunk.get_content() for chunk in chunks)
    assert "年假" in joined or "10" in joined
