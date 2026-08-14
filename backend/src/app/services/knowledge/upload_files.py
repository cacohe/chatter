from app.services.knowledge.operations import ingest_documents
from domain.exceptions import BusinessException
from domain.models.knowledge import KnowledgeSnapshot
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
        loader = UploadFileLoader()
        documents = []
        for filename, content in files:
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
