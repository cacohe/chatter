"""BM25 检索：中文按字、英文按词，不走向量 embedding。"""

from llama_index.core.schema import BaseNode
from llama_index.retrievers.bm25 import BM25Retriever

from infra.config import settings
from infra.logger import logger
from infra.rag.store import get_knowledge_store

# rank-bm25 默认英文词边界切不出汉字，按「单字 / 字母数字串」分词
_BM25_TOKEN_PATTERN = r"(?u)[\u4e00-\u9fff]|[a-zA-Z0-9]+"


def retrieve(query: str, top_k: int | None = None) -> list[BaseNode]:
    """
    对当前知识库做 BM25 检索，返回检索结果。
    """
    store = get_knowledge_store()
    if not store.nodes:
        return []

    k = top_k if top_k is not None else settings.rag_settings.top_k
    try:
        retriever = BM25Retriever.from_defaults(
            nodes=store.nodes,
            similarity_top_k=k,
            skip_stemming=True,
            language="zh",
            token_pattern=_BM25_TOKEN_PATTERN,
        )
        results = retriever.retrieve(query)
    except Exception:
        logger.exception("LlamaIndex BM25 retrieve failed")
        return []

    return [result.node for result in results]


def format_context(nodes: list[BaseNode]) -> str:
    """
    把命中分块格式化进 LLM 的参考文档段落。
    """
    if not nodes:
        return ""
    parts = []
    for i, node in enumerate(nodes, start=1):
        doc_name = node.metadata.get("doc_name") or ""
        parts.append(f"[{i}] 来源: {doc_name}\n{node.get_content()}")
    return "\n\n".join(parts)
