"""网页 / 数据库来源的文档身份：规范化 URL、隐藏密码后的连接串 + SQL。"""

import hashlib
import re
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

_UNSAFE_NAME = re.compile(r"[^0-9A-Za-z\u4e00-\u9fff._-]+")


def slug(value: str, fallback: str = "source") -> str:
    cleaned = _UNSAFE_NAME.sub("-", value).strip("-._")
    return cleaned[:80] or fallback


def fingerprint(*parts: str) -> str:
    payload = "\n".join(parts)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:12]


def canonicalize_url(url: str) -> str:
    """去掉 fragment、统一主机大小写与 query 顺序。"""
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


def web_source_id(url: str) -> str:
    """同一规范化 URL 共用一个来源 ID。"""
    canonical = canonicalize_url(url)
    parsed = urlparse(canonical)
    readable = slug(f"{parsed.netloc}{parsed.path}")[:60]
    return f"web/{readable}-{fingerprint(canonical)}"


def hide_uri_password(uri: str) -> str:
    parsed = urlparse(uri.strip())
    if not parsed.password:
        return uri.strip()
    netloc = parsed.netloc.replace(f":{parsed.password}@", ":***@")
    return urlunparse(parsed._replace(netloc=netloc))


def database_source_id(uri: str, query: str) -> str:
    """同一连接串 + 同一条 SQL 共用一个来源 ID。"""
    normalized_query = " ".join(query.split()).strip()
    return f"db/{fingerprint(hide_uri_password(uri), normalized_query)}"
