"""知识来源适配：DatabaseReader 与带请求头的 SimpleWebPageReader。"""

import re

from llama_index.core import Document
from llama_index.core.bridge.pydantic import PrivateAttr
from llama_index.readers.database import DatabaseReader
from llama_index.readers.web import SimpleWebPageReader

from infra.logger import logger

_UNSAFE_NAME = re.compile(r"[^0-9A-Za-z\u4e00-\u9fff._-]+")
_WEB_SHELL_HINTS = re.compile(
    r"载入中|加载中|正在加载|请开启\s*javascript|enable javascript|"
    r"just a moment|checking your browser|人机验证|请稍候",
    re.I,
)
_WEB_EMPTY_ERROR = (
    "未能从网页解析出正文。该链接可能需要登录、浏览器渲染，或被站点拦截。"
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
    """
    SimpleWebPageReader 默认不带 UA，部分站点会返回空页或反爬壳；此处补浏览器头。
    """

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
            # requests 对未声明 charset 的 HTML 常误判为 ISO-8859-1
            if not encoding or encoding.lower() == "iso-8859-1":
                response.encoding = response.apparent_encoding or "utf-8"
            return response

        web_base.requests.get = get_with_headers
        try:
            return super().load_data(urls)
        finally:
            web_base.requests.get = original_get


def slug(value: str, fallback: str = "source") -> str:
    """
    把主机名/来源名收成可做文档前缀的短标识。
    """
    cleaned = _UNSAFE_NAME.sub("-", value).strip("-._")
    return cleaned[:80] or fallback


def load_database_documents(uri: str, query: str, *, prefix: str) -> list[Document]:
    """
    用 LlamaIndex DatabaseReader 执行 SQL，每行一篇文档。
    """
    reader = DatabaseReader(uri=uri)
    documents = reader.load_data(query=query)
    named: list[Document] = []
    for index, document in enumerate(documents):
        document.metadata["doc_name"] = f"{prefix}/{index}.md"
        named.append(document)
    logger.info(f"Loaded {len(named)} documents from database")
    return named


def _is_placeholder_page(text: str) -> bool:
    """
    识别反爬/JS 壳页面（避免 HTTP 200 但几乎没有正文）。
    """
    compact = re.sub(r"\s+", "", text)
    if not compact:
        return True
    if not _WEB_SHELL_HINTS.search(text):
        return False
    remainder = _WEB_SHELL_HINTS.sub("", compact)
    return len(remainder) < 80


def load_web_documents(url: str, *, prefix: str) -> list[Document]:
    """
    抓取网页正文；空页或占位页视为失败，避免把「载入中」当知识入库。
    """
    try:
        documents = HeaderWebPageReader(
            html_to_text=True,
            fail_on_error=True,
            headers=_WEB_HEADERS,
        ).load_data([url])
    except Exception as exc:
        logger.warning(f"SimpleWebPageReader failed for {url}: {exc}")
        documents = []

    named: list[Document] = []
    for index, document in enumerate(documents):
        text = (document.get_content() or "").strip()
        if not text or _is_placeholder_page(text):
            continue
        document.metadata["doc_name"] = f"{prefix}/{index}.md"
        named.append(document)
    if not named:
        raise ValueError(_WEB_EMPTY_ERROR)
    logger.info(f"Loaded {len(named)} documents from web page {url}")
    return named
