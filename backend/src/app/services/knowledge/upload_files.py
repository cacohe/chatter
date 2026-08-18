from app.services.knowledge.shared import ingest_documents
from domain.exceptions import BusinessException
from domain.models.knowledge import KnowledgeSnapshot
from infra.config import settings
from infra.rag.sources import UploadFileLoader


class UploadFiles:
    """上传 PDF/Markdown/TXT，解析后分块写入知识库。"""

    def execute(
        self,
        files: list[tuple[str, bytes]],
        *,
        chunk_size: int | None = None,
        overlap: int | None = None,
    ) -> KnowledgeSnapshot:
        if not files:
            raise BusinessException("请至少上传一个文件")
        limits = settings.rag_settings
        if len(files) > limits.max_upload_files:
            raise BusinessException(f"单次最多上传 {limits.max_upload_files} 个文件")
        total_bytes = 0
        loader = UploadFileLoader()
        documents = []
        for filename, content in files:
            size = len(content)
            if size > limits.max_upload_file_bytes:
                raise BusinessException(
                    f"文件 {filename} 超过大小上限（{limits.max_upload_file_bytes} 字节）"
                )
            total_bytes += size
            if total_bytes > limits.max_upload_total_bytes:
                raise BusinessException(
                    f"上传文件总大小超过上限（{limits.max_upload_total_bytes} 字节）"
                )
            try:
                documents.append(loader.load(filename, content))
            except ValueError as exc:
                raise BusinessException(str(exc)) from exc
        return ingest_documents(
            documents,
            chunk_size=chunk_size,
            overlap=overlap,
            default_id="upload",
        )
