from llama_index.core import Document

from app.services.knowledge.common import build_summary, prepare_store
from domain.exceptions import BusinessException
from domain.schemas import knowledge as knowledge_schema
from infra.rag.loader import documents_from_upload, ingest_llama_documents


class UploadFiles:
    """上传 PDF/Markdown/TXT：经 LlamaIndex 解析后写入进程内知识库。"""

    def execute(
        self,
        files: list[tuple[str, bytes]],
        *,
        chunk_size: int | None = None,
        overlap: int | None = None,
    ) -> knowledge_schema.KnowledgeSummary:
        if not files:
            raise BusinessException("请至少上传一个文件")

        store, size, ov = prepare_store(chunk_size=chunk_size, overlap=overlap)
        documents: list[Document] = []
        for filename, content in files:
            try:
                documents.extend(documents_from_upload(filename, content))
            except ValueError as exc:
                raise BusinessException(str(exc)) from exc
        if not documents:
            raise BusinessException("未能从文件中读取到文本内容")
        ingest_llama_documents(
            store, documents, chunk_size=size, overlap=ov, default_name="upload"
        )
        return build_summary()
