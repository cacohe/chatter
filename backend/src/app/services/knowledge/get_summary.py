from app.services.knowledge.shared import snapshot
from domain.models.knowledge import KnowledgeSnapshot


class GetSummary:
    """返回当前知识库快照。"""

    def execute(self) -> KnowledgeSnapshot:
        return snapshot()
