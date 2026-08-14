from llama_index.core.schema import TextNode

from app.services.knowledge.operations import list_chunks


class ListChunks:
    """列出当前知识库中的文档分块。"""

    def execute(
        self,
        *,
        doc_name: str | None = None,
        limit: int = 50,
    ) -> list[TextNode]:
        return list_chunks(doc_id=doc_name, limit=limit)
