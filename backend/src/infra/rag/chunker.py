"""LlamaIndex SentenceSplitter：把原文切成 TextNode。"""

from llama_index.core import Document
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.node_parser.text.sentence import CHUNKING_REGEX
from llama_index.core.node_parser.text.utils import split_by_regex
from llama_index.core.schema import NodeRelationship, RelatedNodeInfo, TextNode

from domain.models.knowledge import ChunkParams

_PAYLOAD_TEXT_KEY = "text"


class SentenceChunker:
    def split(self, document: Document, params: ChunkParams) -> list[TextNode]:
        splitter = SentenceSplitter(
            chunk_size=params.size,
            chunk_overlap=params.overlap,
            chunking_tokenizer_fn=split_by_regex(CHUNKING_REGEX),
        )
        nodes = splitter.get_nodes_from_documents([document])
        result: list[TextNode] = []
        for index, node in enumerate(nodes):
            text = node.get_content().strip()
            if not text:
                continue
            node.metadata["doc_id"] = document.doc_id
            node.metadata["doc_name"] = document.doc_id
            node.metadata["chunk_index"] = index
            # 顶层 payload 需要正文；排除出 embedding / LLM metadata，避免重复计入。
            node.metadata[_PAYLOAD_TEXT_KEY] = text
            if _PAYLOAD_TEXT_KEY not in node.excluded_embed_metadata_keys:
                node.excluded_embed_metadata_keys.append(_PAYLOAD_TEXT_KEY)
            if _PAYLOAD_TEXT_KEY not in node.excluded_llm_metadata_keys:
                node.excluded_llm_metadata_keys.append(_PAYLOAD_TEXT_KEY)
            # 透传来源元信息，便于问答阶段生成结构化引用。
            for key in ("source_uri", "source_type", "source_id"):
                value = document.metadata.get(key)
                if value:
                    node.metadata[key] = value
            node.relationships[NodeRelationship.SOURCE] = RelatedNodeInfo(
                node_id=document.doc_id
            )
            result.append(node)
        return result
