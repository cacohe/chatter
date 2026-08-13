from app.services.knowledge.common import build_summary
from domain.schemas import knowledge as knowledge_schema
from infra.rag.loader import reload_docs


class ReloadKnowledge:
    """按新的分块大小/重叠重切：磁盘种子 + 仍在内存中的上传/网页/库表。"""

    def execute(
        self, request: knowledge_schema.ReloadKnowledgeRequest
    ) -> knowledge_schema.KnowledgeSummary:
        reload_docs(chunk_size=request.chunk_size, overlap=request.chunk_overlap)
        return build_summary()
