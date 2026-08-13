import requests

from config import settings


class KnowledgeClient:
    def __init__(self):
        self.base_url = settings.backend_api_url.rstrip("/")

    def get_status(self) -> dict:
        response = requests.get(f"{self.base_url}/knowledge/status", timeout=30)
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
            ("files", (filename, content, "text/plain")) for filename, content in files
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
