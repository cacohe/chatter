from app.services.knowledge.shared import ingest_documents
from domain.exceptions import BusinessException
from domain.models.knowledge import KnowledgeSnapshot
from infra.rag.sources import DatabaseLoader


class SyncDatabase:
    """同步 SQL 查询结果：原文不落盘，分块写入知识库。"""

    def execute(
        self,
        uri: str,
        query: str,
        *,
        chunk_size: int | None = None,
        overlap: int | None = None,
    ) -> KnowledgeSnapshot:
        try:
            documents = DatabaseLoader().load(uri, query)
        except BusinessException:
            raise
        except ValueError as exc:
            raise BusinessException(str(exc)) from exc
        except Exception as exc:
            raise BusinessException(f"数据库同步失败: {exc}") from exc
        source_id = next(
            (
                str(doc.metadata["source_id"])
                for doc in documents
                if doc.metadata.get("source_id")
            ),
            None,
        )
        return ingest_documents(
            documents,
            chunk_size=chunk_size,
            overlap=overlap,
            replace_source=source_id,
            default_id=source_id or "document",
        )
