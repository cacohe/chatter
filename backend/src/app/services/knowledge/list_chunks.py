from domain.schemas import knowledge as knowledge_schema
from infra.rag.store import get_knowledge_store


class ListChunks:
    """按文档列出分块预览，供侧边栏折叠展示。"""

    def execute(
        self,
        *,
        doc_name: str | None = None,
        limit: int = 50,
    ) -> list[knowledge_schema.ChunkPreview]:
        store = get_knowledge_store()
        previews: list[knowledge_schema.ChunkPreview] = []
        for node in store.nodes:
            node_name = str(node.metadata.get("doc_name") or "")
            if doc_name and node_name != doc_name:
                continue
            previews.append(
                knowledge_schema.ChunkPreview(
                    doc_name=node_name,
                    chunk_index=int(node.metadata.get("chunk_index") or 0),
                    content=node.get_content(),
                )
            )
            if len(previews) >= limit:
                break
        return previews
