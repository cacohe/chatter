"""向量化模型：DashScope，按配置维度请求，与 Qdrant collection 对齐。"""

from http import HTTPStatus

from llama_index.core import Settings
from llama_index.core.embeddings import BaseEmbedding
from llama_index.embeddings.dashscope import DashScopeEmbedding

from infra.config import settings

Settings.llm = None


class _DashScopeEmbedding(DashScopeEmbedding):
    """按配置维度请求向量，避免模型默认维度与 Qdrant collection 不一致。"""

    def _embed(self, text: str | list[str], *, text_type: str) -> list[list[float]]:
        import dashscope

        inputs = [text] if isinstance(text, str) else text
        response = dashscope.TextEmbedding.call(
            model=self.model_name,
            input=inputs,
            api_key=self._api_key,
            text_type=text_type,
            dimension=settings.rag_settings.embed_dim,
        )
        if response.status_code != HTTPStatus.OK:
            raise RuntimeError(f"DashScope embedding failed: {response}")
        by_index = {
            item["text_index"]: item["embedding"]
            for item in response.output["embeddings"]
        }
        try:
            return [by_index[i] for i in range(len(inputs))]
        except KeyError as exc:
            raise RuntimeError(
                "DashScope embedding returned incomplete results"
            ) from exc

    def _get_query_embedding(self, query: str) -> list[float]:
        return self._embed(query, text_type="query")[0]

    def _get_text_embedding(self, text: str) -> list[float]:
        return self._embed(text, text_type=self._text_type or "document")[0]

    def _get_text_embeddings(self, texts: list[str]) -> list[list[float]]:
        return self._embed(texts, text_type=self._text_type or "document")


def get_embed_model() -> BaseEmbedding:
    return _DashScopeEmbedding(
        model_name=(settings.rag_settings.embed_model or "").strip(),
        api_key=settings.llm_settings.dashscope_api_key or None,
    )


def configure_embeddings() -> BaseEmbedding:
    embed_model = get_embed_model()
    Settings.llm = None
    Settings.embed_model = embed_model
    return embed_model
