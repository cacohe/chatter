from app.services.knowledge.common import build_summary
from domain.exceptions import BusinessException
from domain.schemas import knowledge as knowledge_schema
from infra.logger import logger
from infra.rag.loader import delete_stored_document
from infra.rag.store import get_knowledge_store


class DeleteDocument:
    """删除指定文档：内存节点必删，磁盘种子文件若存在则一并删除。"""

    def execute(self, doc_name: str) -> knowledge_schema.KnowledgeSummary:
        name = (doc_name or "").strip()
        if not name:
            raise BusinessException("请指定要删除的文档")
        store = get_knowledge_store()
        if name not in store.document_names:
            raise BusinessException("文档不存在", status_code=404)
        if store.docs_path:
            try:
                delete_stored_document(store.docs_path, name)
            except ValueError as exc:
                raise BusinessException(str(exc)) from exc
        store.remove_document(name)
        logger.info(f"Deleted RAG doc: {name}")
        return build_summary()
