"""Qdrant 向量检索，返回 TextNode。"""

from llama_index.core.schema import TextNode

from infra.logger import logger
from infra.rag.vectorstore import collection_ready, get_index


class QdrantRetriever:
    def retrieve(self, query: str, top_k: int) -> list[TextNode]:
        if not collection_ready():
            return []
        try:
            results = get_index().as_retriever(similarity_top_k=top_k).retrieve(query)
        except Exception:
            logger.exception("LlamaIndex Qdrant retrieve failed")
            return []
        return [result.node for result in results]
