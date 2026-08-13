from urllib.parse import urlparse

from app.services.knowledge.common import ingest_source
from domain.exceptions import BusinessException
from domain.schemas import knowledge as knowledge_schema
from infra.rag.sources import load_web_documents, slug


class IngestWeb:
    """从网页导入：正文只进内存，不落盘。"""

    def execute(
        self, request: knowledge_schema.IngestWebRequest
    ) -> knowledge_schema.KnowledgeSummary:
        host = urlparse(request.url).netloc or "web"
        name = slug(request.name or host)
        prefix = f"web/{name}"
        try:
            documents = load_web_documents(request.url, prefix=prefix)
        except BusinessException:
            raise
        except Exception as exc:
            raise BusinessException(f"网页导入失败: {exc}") from exc
        return ingest_source(
            documents,
            prefix=prefix,
            chunk_size=request.chunk_size,
            overlap=request.chunk_overlap,
        )
