from app.services.knowledge.common import build_summary
from domain.schemas import knowledge as knowledge_schema


class GetSummary:
    """返回当前进程内知识库快照。"""

    def execute(self) -> knowledge_schema.KnowledgeSummary:
        return build_summary()
