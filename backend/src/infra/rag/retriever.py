import re

from infra.config import settings
from infra.rag.store import DocumentChunk, get_knowledge_store


def _tokenize(text: str) -> set[str]:
    # 中英文简单切词：连续中文/字母数字为一 token
    tokens = re.findall(r"[\u4e00-\u9fff]+|[a-zA-Z0-9]+", text.lower())
    result: set[str] = set()
    for token in tokens:
        if re.fullmatch(r"[\u4e00-\u9fff]+", token) and len(token) > 1:
            # 中文再拆成字与 bigram，提高短查询命中率
            result.update(token)
            result.update(token[i : i + 2] for i in range(len(token) - 1))
        else:
            result.add(token)
    return {t for t in result if t}


def _score(query_tokens: set[str], chunk: DocumentChunk) -> float:
    """
    计算查询词与文档内容的相似度
    """
    if not query_tokens:
        return 0.0
    chunk_tokens = _tokenize(chunk.content)
    if not chunk_tokens:
        return 0.0
    overlap = query_tokens & chunk_tokens
    if not overlap:
        # 退化为子串匹配
        q = "".join(sorted(query_tokens, key=len, reverse=True)[:3])
        if q and q in chunk.content.lower():
            return 0.1
        return 0.0
    return len(overlap) / len(query_tokens)


def retrieve(query: str, top_k: int | None = None) -> list[DocumentChunk]:
    store = get_knowledge_store()
    if not store.chunks:
        return []

    k = top_k if top_k is not None else settings.rag_settings.top_k
    query_tokens = _tokenize(query)
    scored = [(_score(query_tokens, chunk), chunk) for chunk in store.chunks]
    scored = [(s, c) for s, c in scored if s > 0]
    scored.sort(key=lambda x: x[0], reverse=True)
    return [c for _, c in scored[:k]]


def format_context(chunks: list[DocumentChunk]) -> str:
    if not chunks:
        return ""
    parts = []
    for i, chunk in enumerate(chunks, start=1):
        parts.append(f"[{i}] 来源: {chunk.doc_name}\n{chunk.content}")
    return "\n\n".join(parts)
