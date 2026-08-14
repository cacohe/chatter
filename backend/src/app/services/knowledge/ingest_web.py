from app.services.knowledge.operations import ingest_documents
from domain.exceptions import BusinessException
from domain.models.knowledge import KnowledgeSnapshot
from infra.rag.sources import LlamaWebLoader


class IngestWeb:
    """从网页导入知识内容。"""

    def execute(
        self,
        url: str,
        *,
        chunk_size: int | None = None,
        overlap: int | None = None,
    ) -> KnowledgeSnapshot:
        try:
            documents = LlamaWebLoader().load(url)
        except BusinessException:
            raise
        except ValueError as exc:
            raise BusinessException(str(exc)) from exc
        except Exception as exc:
            raise BusinessException(f"网页导入失败: {exc}") from exc
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
