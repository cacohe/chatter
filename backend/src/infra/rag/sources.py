"""知识来源适配：上传文件、网页、数据库。"""

import hashlib
import json
import re
from io import BytesIO
from pathlib import Path
from typing import Any

import pypdf
from llama_index.core import Document
from llama_index.core.bridge.pydantic import PrivateAttr
from llama_index.readers.database import DatabaseReader
from llama_index.readers.web import SimpleWebPageReader

from infra.logger import logger
from infra.rag.identity import database_source_id, slug, web_source_id

SUPPORTED_SUFFIXES = {".txt", ".md", ".markdown", ".pdf"}

_WEB_EMPTY_ERROR = (
    "未能从网页解析出正文。该链接可能需要登录、浏览器渲染，或被站点拦截。"
)
_WEB_SHELL_HINTS = re.compile(
    r"载入中|加载中|正在加载|请开启\s*javascript|enable javascript|"
    r"just a moment|checking your browser|人机验证|请稍候",
    re.I,
)
_WEB_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
}


class HeaderWebPageReader(SimpleWebPageReader):
    """SimpleWebPageReader 默认不带 UA；此处补浏览器头。"""

    _headers: dict[str, str] = PrivateAttr(default_factory=dict)

    def __init__(self, headers: dict[str, str] | None = None, **kwargs) -> None:
        super().__init__(**kwargs)
        self._headers = headers or {}

    def load_data(self, urls: list[str]) -> list[Document]:
        import llama_index.readers.web.simple_web.base as web_base

        original_get = web_base.requests.get
        headers = self._headers

        def get_with_headers(url: str, **kwargs):
            merged = {**headers, **(kwargs.pop("headers", None) or {})}
            response = original_get(url, headers=merged or None, **kwargs)
            encoding = response.encoding
            if not encoding or encoding.lower() == "iso-8859-1":
                response.encoding = response.apparent_encoding or "utf-8"
            return response

        web_base.requests.get = get_with_headers
        try:
            return super().load_data(urls)
        finally:
            web_base.requests.get = original_get


def _is_placeholder_page(text: str) -> bool:
    compact = re.sub(r"\s+", "", text)
    if not compact:
        return True
    if not _WEB_SHELL_HINTS.search(text):
        return False
    remainder = _WEB_SHELL_HINTS.sub("", compact)
    return len(remainder) < 80


def _row_key(row: dict[str, Any], index: int) -> str:
    lowered = {str(key).lower(): value for key, value in row.items()}
    for key in ("id", "pk", "uuid", "guid"):
        value = lowered.get(key)
        if value is not None and str(value).strip():
            return slug(str(value), fallback=str(index))
    payload = json.dumps(row, default=str, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:12]


def _to_documents(
    items: list[tuple[str, str, str]],
) -> list[Document]:
    return [
        Document(text=text, doc_id=doc_id, metadata={"source_id": source_id})
        for doc_id, text, source_id in items
    ]


class UploadFileLoader:
    def load(self, filename: str, content: bytes) -> Document:
        suffix = Path(filename).suffix.lower()
        if suffix not in SUPPORTED_SUFFIXES:
            raise ValueError(f"不支持的文件类型: {suffix or '(无扩展名)'}")
        safe_name = Path(filename).name
        if not safe_name or safe_name in {".", ".."}:
            raise ValueError("无效的文件名")

        text = _extract_text(suffix, content).strip()
        if not text:
            raise ValueError("未能从文件中读取到文本内容")
        return Document(text=text, doc_id=safe_name)


def _extract_text(suffix: str, content: bytes) -> str:
    if suffix == ".pdf":
        try:
            reader = pypdf.PdfReader(BytesIO(content))
        except Exception as exc:
            raise ValueError("无法解析 PDF 文件") from exc
        if reader.is_encrypted:
            raise ValueError("不支持加密的 PDF 文件")
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    try:
        return content.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise ValueError("文本文件必须是 UTF-8 编码") from exc


class LlamaWebLoader:
    def load(self, url: str) -> list[Document]:
        source_id = web_source_id(url)
        try:
            documents = HeaderWebPageReader(
                html_to_text=True,
                fail_on_error=True,
                headers=_WEB_HEADERS,
            ).load_data([url])
        except Exception as exc:
            logger.warning(f"SimpleWebPageReader failed for {url}: {exc}")
            documents = []

        usable: list[tuple[str, str, str]] = []
        for document in documents:
            text = (document.get_content() or "").strip()
            if not text or _is_placeholder_page(text):
                continue
            usable.append(("", text, source_id))
        if not usable:
            raise ValueError(_WEB_EMPTY_ERROR)
        if len(usable) == 1:
            named = [(source_id, usable[0][1], source_id)]
        else:
            named = [
                (f"{source_id}/{index}", text, source_id)
                for index, (_, text, _) in enumerate(usable)
            ]
        logger.info(f"Loaded {len(named)} documents from web page {url}")
        return _to_documents(named)


class LlamaDatabaseLoader:
    def load(self, uri: str, query: str) -> list[Document]:
        source_id = database_source_id(uri, query)
        used: dict[str, int] = {}

        def document_id(row: dict[str, Any]) -> str:
            key = _row_key(row, len(used))
            count = used.get(key, 0)
            used[key] = count + 1
            row_id = key if count == 0 else f"{key}-{count}"
            return f"{source_id}/{row_id}"

        reader = DatabaseReader(uri=uri)
        documents = reader.load_data(query=query, document_id=document_id)
        named: list[Document] = []
        for document in documents:
            name = str(document.id_ or document.doc_id or "")
            if not name.startswith(source_id):
                name = f"{source_id}/{len(named)}"
            document.doc_id = name
            document.metadata["source_id"] = source_id
            named.append(document)
        logger.info(f"Loaded {len(named)} documents from database")
        return named
