"""知识来源适配：上传文件、网页、数据库。"""

import hashlib
import ipaddress
import json
import re
import socket
from io import BytesIO
from pathlib import Path
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

import html2text
import pypdf
import requests
from llama_index.core import Document
from llama_index.readers.database import DatabaseReader

from infra.config import settings
from infra.logger import logger

_UNSAFE_NAME = re.compile(r"[^0-9A-Za-z\u4e00-\u9fff._-]+")


def _slug(value: str, fallback: str = "source") -> str:
    """将字符串转成可读短名，用于拼进 source_id。"""
    cleaned = _UNSAFE_NAME.sub("-", value).strip("-._")
    return cleaned[:80] or fallback


def _fingerprint(*parts: str) -> str:
    """对若干字段做短哈希，保证来源 ID 稳定且不会过长。"""
    payload = "\n".join(parts)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:12]


def _is_blocked_ip(address: str) -> bool:
    """判断是否为不可抓取地址；IPv4 映射的 IPv6 按对应 IPv4 检查。"""
    try:
        ip = ipaddress.ip_address(address)
    except ValueError:
        return False
    mapped = getattr(ip, "ipv4_mapped", None)
    if mapped is not None:
        ip = mapped
    return (
        ip.is_private
        or ip.is_loopback
        or ip.is_link_local
        or ip.is_unspecified
        or ip.is_reserved
        or ip.is_multicast
    )


class UploadFileLoader:
    """从上传字节流解析 PDF/Markdown/TXT。"""

    _SUPPORTED_SUFFIXES = {".txt", ".md", ".markdown", ".pdf"}

    def source_id(self, filename: str) -> str:
        """文件来源以文件名为稳定 ID。"""
        safe_name = Path(filename).name
        if not safe_name or safe_name in {".", ".."}:
            raise ValueError("无效的文件名")
        return safe_name

    def source_uri(self, doc_id: str) -> str:
        return f"file://{doc_id}"

    def load(self, filename: str, content: bytes) -> Document:
        suffix = Path(filename).suffix.lower()
        if suffix not in self._SUPPORTED_SUFFIXES:
            raise ValueError(f"不支持的文件类型: {suffix or '(无扩展名)'}")
        doc_id = self.source_id(filename)
        source_uri = self.source_uri(doc_id)

        text = self._extract_text(suffix, content).strip()
        if not text:
            raise ValueError("未能从文件中读取到文本内容")
        return Document(
            text=text,
            doc_id=doc_id,
            metadata={
                "source_type": "file",
                "source_id": doc_id,
                "source_uri": source_uri,
            },
        )

    def _extract_text(self, suffix: str, content: bytes) -> str:
        """按扩展名抽出纯文本；PDF 加密或不完整时直接拒绝。"""
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


class WebLoader:
    """抓取网页正文，并补齐稳定来源 ID。"""

    _EMPTY_ERROR = (
        "未能从网页解析出正文。该链接可能需要登录、浏览器渲染，或被站点拦截。"
    )
    _PRIVATE_HOST_ERROR = "不允许抓取内网或本机地址"
    _SHELL_HINTS = re.compile(
        r"载入中|加载中|正在加载|请开启\s*javascript|enable javascript|"
        r"just a moment|checking your browser|人机验证|请稍候",
        re.I,
    )
    _HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/122.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    }

    def source_id(self, url: str) -> str:
        """同一规范化 URL 共用一个来源 ID。"""
        canonical = self.source_uri(url)
        parsed = urlparse(canonical)
        readable = _slug(f"{parsed.netloc}{parsed.path}")[:60]
        return f"web/{readable}-{_fingerprint(canonical)}"

    def source_uri(self, url: str) -> str:
        """去掉 fragment、统一主机大小写与 query 顺序，避免同一网页出现多个来源。"""
        raw = url.strip()
        parsed = urlparse(raw)
        if not parsed.netloc:
            return raw
        scheme = (parsed.scheme or "https").lower()
        netloc = parsed.netloc.lower()
        path = parsed.path or "/"
        if path != "/" and path.endswith("/"):
            path = path.rstrip("/")
        query = urlencode(sorted(parse_qsl(parsed.query, keep_blank_values=True)))
        return urlunparse((scheme, netloc, path, "", query, ""))

    def load(self, url: str) -> list[Document]:
        safe_url = self._validate_url(url)
        normalized_url = self.source_uri(safe_url)
        source_id = self.source_id(safe_url)
        try:
            documents = [Document(text=self._fetch_page(safe_url))]
        except Exception as exc:
            logger.warning(f"Web fetch failed for {safe_url}: {exc}")
            documents = []

        usable: list[tuple[str, str, str]] = []
        for document in documents:
            text = (document.get_content() or "").strip()
            if not text or self._is_placeholder_page(text):
                continue
            if len(text) > settings.rag_settings.web_max_content_chars:
                raise ValueError("网页正文超过长度上限，暂不允许导入该页面。")
            usable.append(("", text, source_id))
        if not usable:
            raise ValueError(self._EMPTY_ERROR)
        if len(usable) == 1:
            named = [(source_id, usable[0][1], source_id)]
        else:
            named = [
                (f"{source_id}/{index}", text, source_id)
                for index, (_, text, _) in enumerate(usable)
            ]
        logger.info(f"Loaded {len(named)} documents from web page {safe_url}")
        documents_out = self._to_documents(named)
        for document in documents_out:
            document.metadata["source_uri"] = normalized_url
        return documents_out

    def _validate_url(self, url: str) -> str:
        """只允许公网 http/https，拒绝本机和私网地址，避免 SSRF。"""
        raw = url.strip()
        if not raw:
            raise ValueError("请提供网页地址")
        parsed = urlparse(raw)
        scheme = (parsed.scheme or "").lower()
        if scheme not in {"http", "https"}:
            raise ValueError("仅支持 http/https 网页地址")
        host = parsed.hostname
        if not host:
            raise ValueError("网页地址缺少主机名")
        if host.lower() == "localhost":
            raise ValueError(self._PRIVATE_HOST_ERROR)
        try:
            infos = socket.getaddrinfo(host, None, proto=socket.IPPROTO_TCP)
        except socket.gaierror as exc:
            raise ValueError(f"无法解析网页地址主机名: {host}") from exc
        for _, _, _, _, sockaddr in infos:
            if _is_blocked_ip(sockaddr[0]):
                raise ValueError(self._PRIVATE_HOST_ERROR)
        return raw

    def _fetch_page(self, url: str) -> str:
        """带 UA 抓取页面；不跟随跳转，避免校验过的公网 URL 再被重定向到内网。"""
        response = requests.get(
            url,
            headers=self._HEADERS,
            timeout=settings.rag_settings.web_fetch_timeout_seconds,
            allow_redirects=False,
        )
        if response.status_code != 200:
            raise ValueError(f"抓取失败，HTTP {response.status_code}")
        encoding = response.encoding
        if not encoding or encoding.lower() == "iso-8859-1":
            response.encoding = response.apparent_encoding or "utf-8"
        return html2text.html2text(response.text)

    def _is_placeholder_page(self, text: str) -> bool:
        """过滤“载入中 / 请开启 JavaScript”这类壳页面。"""
        compact = re.sub(r"\s+", "", text)
        if not compact:
            return True
        if not self._SHELL_HINTS.search(text):
            return False
        remainder = self._SHELL_HINTS.sub("", compact)
        return len(remainder) < 80

    def _to_documents(self, items: list[tuple[str, str, str]]) -> list[Document]:
        return [
            Document(
                text=text,
                doc_id=doc_id,
                metadata={"source_id": source_id, "source_type": "web"},
            )
            for doc_id, text, source_id in items
        ]


class DatabaseLoader:
    """把只读 SQL 结果同步为知识文档。"""

    def source_id(self, uri: str, query: str) -> str:
        """同一连接串 + 同一条 SQL 共用一个来源 ID。"""
        normalized_query = " ".join(query.split()).strip()
        return f"db/{_fingerprint(self.source_uri(uri), normalized_query)}"

    def source_uri(self, uri: str) -> str:
        """脱敏连接串，避免把明文密码带到引用面板。"""
        parsed = urlparse(uri.strip())
        if not parsed.password:
            return uri.strip()
        netloc = parsed.netloc.replace(f":{parsed.password}@", ":***@")
        return urlunparse(parsed._replace(netloc=netloc))

    def load(self, uri: str, query: str) -> list[Document]:
        safe_uri, safe_query = self._validate_query(uri, query)
        source_id = self.source_id(safe_uri, safe_query)
        used: dict[str, int] = {}

        def document_id(row: dict[str, Any]) -> str:
            key = self._row_key(row, len(used))
            count = used.get(key, 0)
            used[key] = count + 1
            row_id = key if count == 0 else f"{key}-{count}"
            return f"{source_id}/{row_id}"

        reader = DatabaseReader(uri=safe_uri)
        rows = list(reader.lazy_load_data(query=safe_query, document_id=document_id))
        if len(rows) > settings.rag_settings.db_max_rows:
            raise ValueError(
                f"数据库查询结果超过行数上限（{settings.rag_settings.db_max_rows} 行）"
            )
        named: list[Document] = []
        for document in rows:
            name = str(document.id_ or document.doc_id or "")
            if not name.startswith(source_id):
                name = f"{source_id}/{len(named)}"
            cleaned_text = self._validate_row_text(document.text)
            metadata = dict(document.metadata)
            metadata["source_id"] = source_id
            metadata["source_type"] = "database"
            metadata["source_uri"] = self.source_uri(safe_uri)
            named.append(
                Document(
                    text=cleaned_text,
                    doc_id=name,
                    metadata=metadata,
                    id_=str(document.id_ or name),
                )
            )
        logger.info(f"Loaded {len(named)} documents from database")
        return named

    def _validate_query(self, uri: str, query: str) -> tuple[str, str]:
        """只允许单条 SELECT，避免把写操作或批量语句送进数据库。"""
        trimmed_uri = uri.strip()
        if not trimmed_uri:
            raise ValueError("请提供数据库连接串")
        parsed = urlparse(trimmed_uri)
        if not parsed.scheme:
            raise ValueError("数据库连接串格式无效")

        normalized_query = query.strip()
        if not normalized_query:
            raise ValueError("请提供 SQL 查询语句")
        statements = [
            part.strip() for part in normalized_query.split(";") if part.strip()
        ]
        if len(statements) != 1:
            raise ValueError("仅允许执行单条 SELECT 查询")
        statement = statements[0]
        if not re.match(r"(?is)^select\b", statement):
            raise ValueError("仅允许执行 SELECT 查询")
        return trimmed_uri, statement

    def _row_key(self, row: dict[str, Any], index: int) -> str:
        """优先用主键类字段命名行；没有则回退到整行哈希。"""
        lowered = {str(key).lower(): value for key, value in row.items()}
        for key in ("id", "pk", "uuid", "guid"):
            value = lowered.get(key)
            if value is not None and str(value).strip():
                return _slug(str(value), fallback=str(index))
        payload = json.dumps(row, default=str, sort_keys=True, ensure_ascii=False)
        return _fingerprint(payload)

    def _validate_row_text(self, text: str) -> str:
        cleaned = text.strip()
        if not cleaned:
            raise ValueError("数据库查询结果中存在空记录")
        max_chars = settings.rag_settings.db_max_chars_per_row
        if len(cleaned) > max_chars:
            raise ValueError(f"单行数据库记录超过长度上限（{max_chars} 字符）")
        return cleaned
