from app.services.knowledge.shared import delete_document
from domain.models.knowledge import KnowledgeSnapshot
from infra.logger import logger


class DeleteDocument:
    """删除知识库中的指定文档。"""

    def execute(self, doc_name: str) -> KnowledgeSnapshot:
        snapshot = delete_document(doc_name)
        logger.info(f"Deleted RAG doc: {doc_name}")
        return snapshot
