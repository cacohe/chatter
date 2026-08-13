from app.services.knowledge.common import ingest_source
from domain.exceptions import BusinessException
from domain.schemas import knowledge as knowledge_schema
from infra.rag.sources import load_database_documents, slug


class SyncDatabase:
    """用 DatabaseReader 拉 SQL 结果并入库，同样只保留在内存。"""

    def execute(
        self, request: knowledge_schema.SyncDatabaseRequest
    ) -> knowledge_schema.KnowledgeSummary:
        name = slug(request.name or "database")
        prefix = f"db/{name}"
        try:
            documents = load_database_documents(
                request.uri, request.query, prefix=prefix
            )
        except Exception as exc:
            raise BusinessException(f"数据库同步失败: {exc}") from exc
        return ingest_source(
            documents,
            prefix=prefix,
            chunk_size=request.chunk_size,
            overlap=request.chunk_overlap,
        )
