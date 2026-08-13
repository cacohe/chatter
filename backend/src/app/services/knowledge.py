from pathlib import Path

from domain.exceptions import BusinessException
from domain.schemas import knowledge as knowledge_schema
from infra.rag.loader import (
    ingest_text,
    reload_docs,
    save_uploaded_file,
)
from infra.rag.store import get_knowledge_store


class KnowledgeService:
    def get_status(self) -> knowledge_schema.KnowledgeStatus:
        store = get_knowledge_store()
        doc_chunk_counts: dict[str, int] = {}
        for chunk in store.chunks:
            doc_chunk_counts[chunk.doc_name] = (
                doc_chunk_counts.get(chunk.doc_name, 0) + 1
            )

        documents = [
            knowledge_schema.DocumentInfo(
                name=name, chunk_count=doc_chunk_counts.get(name, 0)
            )
            for name in store.document_names
        ]
        return knowledge_schema.KnowledgeStatus(
            document_count=store.document_count,
            chunk_count=len(store.chunks),
            chunk_size=store.chunk_size,
            chunk_overlap=store.chunk_overlap,
            docs_path=store.docs_path,
            documents=documents,
        )

    def reload(self, request: knowledge_schema.ReloadKnowledgeRequest):
        reload_docs(chunk_size=request.chunk_size, overlap=request.chunk_overlap)
        return self.get_status()

    def upload_files(
        self,
        files: list[tuple[str, bytes]],
        *,
        chunk_size: int | None = None,
        overlap: int | None = None,
    ):
        if not files:
            raise BusinessException("请至少上传一个文件")

        store = get_knowledge_store()
        size = chunk_size if chunk_size is not None else store.chunk_size
        overlap = overlap if overlap is not None else store.chunk_overlap

        from infra.config import settings
        from infra.rag.loader import validate_chunk_params

        validate_chunk_params(size, overlap)

        docs_path = (
            Path(store.docs_path or settings.rag_settings.docs_path)
            .expanduser()
            .resolve()
        )
        store.docs_path = str(docs_path)
        store.chunk_size = size
        store.chunk_overlap = overlap

        for filename, content in files:
            file_path = save_uploaded_file(filename, content, str(docs_path))
            text = content.decode("utf-8", errors="ignore")
            doc_name = file_path.name
            ingest_text(store, doc_name, text, chunk_size=size, overlap=overlap)

        return self.get_status()

    def list_chunks(
        self,
        *,
        doc_name: str | None = None,
        limit: int = 50,
    ) -> list[knowledge_schema.ChunkPreview]:
        store = get_knowledge_store()
        previews: list[knowledge_schema.ChunkPreview] = []
        for chunk in store.chunks:
            if doc_name and chunk.doc_name != doc_name:
                continue
            previews.append(
                knowledge_schema.ChunkPreview(
                    doc_name=chunk.doc_name,
                    chunk_index=chunk.chunk_index,
                    content=chunk.content,
                )
            )
            if len(previews) >= limit:
                break
        return previews
