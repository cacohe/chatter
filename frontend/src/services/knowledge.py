"""知识库 API 封装；ingest/delete 走 _raise_for_api，以便展示后端 detail。"""

import requests

from config import settings


def _raise_for_api(response: requests.Response) -> None:
    """把 FastAPI 的 detail 抽成 RuntimeError，供侧边栏直接展示。"""
    if response.ok:
        return
    detail = None
    try:
        payload = response.json()
        detail = payload.get("detail")
    except ValueError:
        detail = (response.text or "").strip() or None
    if isinstance(detail, list):
        detail = "; ".join(
            item.get("msg", str(item)) if isinstance(item, dict) else str(item)
            for item in detail
        )
    raise RuntimeError(detail or f"请求失败（HTTP {response.status_code}）")


def _file_content_type(filename: str) -> str:
    suffix = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if suffix == "pdf":
        return "application/pdf"
    if suffix in {"md", "markdown"}:
        return "text/markdown"
    return "text/plain"


class KnowledgeClient:
    """知识库 REST 客户端，方法与 /api/v1.0/knowledge 一一对应。"""

    def __init__(self):
        self.base_url = settings.backend_api_url.rstrip("/")

    def get_summary(self) -> dict:
        response = requests.get(f"{self.base_url}/knowledge/summary", timeout=30)
        response.raise_for_status()
        return response.json()

    def reload(self, chunk_size: int, chunk_overlap: int) -> dict:
        response = requests.post(
            f"{self.base_url}/knowledge/reload",
            json={"chunk_size": chunk_size, "chunk_overlap": chunk_overlap},
            timeout=60,
        )
        response.raise_for_status()
        return response.json()

    def upload_files(
        self,
        files: list[tuple[str, bytes]],
        *,
        chunk_size: int | None = None,
        chunk_overlap: int | None = None,
    ) -> dict:
        multipart_files = [
            ("files", (filename, content, _file_content_type(filename)))
            for filename, content in files
        ]
        data = {}
        if chunk_size is not None:
            data["chunk_size"] = str(chunk_size)
        if chunk_overlap is not None:
            data["chunk_overlap"] = str(chunk_overlap)

        response = requests.post(
            f"{self.base_url}/knowledge/upload",
            files=multipart_files,
            data=data,
            timeout=60,
        )
        response.raise_for_status()
        return response.json()

    def sync_database(
        self,
        uri: str,
        query: str,
        *,
        name: str | None = None,
        chunk_size: int | None = None,
        chunk_overlap: int | None = None,
    ) -> dict:
        payload: dict = {"uri": uri, "query": query}
        if name:
            payload["name"] = name
        if chunk_size is not None:
            payload["chunk_size"] = chunk_size
        if chunk_overlap is not None:
            payload["chunk_overlap"] = chunk_overlap
        response = requests.post(
            f"{self.base_url}/knowledge/sync/database",
            json=payload,
            timeout=60,
        )
        response.raise_for_status()
        return response.json()

    def ingest_web(
        self,
        url: str,
        *,
        name: str | None = None,
        chunk_size: int | None = None,
        chunk_overlap: int | None = None,
    ) -> dict:
        payload: dict = {"url": url}
        if name:
            payload["name"] = name
        if chunk_size is not None:
            payload["chunk_size"] = chunk_size
        if chunk_overlap is not None:
            payload["chunk_overlap"] = chunk_overlap
        response = requests.post(
            f"{self.base_url}/knowledge/ingest/web",
            json=payload,
            timeout=60,
        )
        _raise_for_api(response)
        return response.json()

    def delete_document(self, doc_name: str) -> dict:
        response = requests.delete(
            f"{self.base_url}/knowledge/documents",
            params={"doc_name": doc_name},
            timeout=30,
        )
        _raise_for_api(response)
        return response.json()

    def list_chunks(self, doc_name: str | None = None, limit: int = 20) -> list[dict]:
        params: dict[str, str | int] = {"limit": limit}
        if doc_name:
            params["doc_name"] = doc_name
        response = requests.get(
            f"{self.base_url}/knowledge/chunks",
            params=params,
            timeout=30,
        )
        response.raise_for_status()
        return response.json()


knowledge_client = KnowledgeClient()
