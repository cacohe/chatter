"""LlamaIndex SentenceSplitter：把原文切成 TextNode。"""

from llama_index.core import Document
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.node_parser.text.sentence import CHUNKING_REGEX
from llama_index.core.node_parser.text.utils import split_by_regex
from llama_index.core.schema import NodeRelationship, RelatedNodeInfo, TextNode

from domain.models.knowledge import ChunkParams


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
            if not node.get_content().strip():
                continue
            node.metadata["doc_name"] = document.doc_id
            node.metadata["chunk_index"] = index
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
