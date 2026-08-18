"""侧边栏：分块参数、文件/数据库/网页导入、文档预览与删除。"""

import streamlit as st

from logger import logger
from logic.session import session_logic
from services.api_client import backend_api_client


def _render_new_chat():
    if st.button("开启新聊天", use_container_width=True, help="开始一轮新的问答"):
        session_logic.start_new_chat()
        st.session_state["_needs_rerun"] = True


def _load_knowledge_summary() -> dict | None:
    try:
        return backend_api_client.knowledge.get_summary()
    except Exception as e:
        logger.exception(f"Failed to load knowledge summary: {e}")
        return None


def _chunk_controls(summary: dict | None) -> tuple[int, int]:
    if summary:
        size_default = int(summary.get("chunk_size", 500))
        overlap_default = int(summary.get("chunk_overlap", 50))
    else:
        st.warning("无法连接后端知识库服务")
        size_default = 500
        overlap_default = 50

    col_size, col_overlap = st.columns(2)
    with col_size:
        chunk_size = st.number_input(
            "分块大小",
            min_value=50,
            max_value=10000,
            value=size_default,
            step=50,
            help="仅作用于之后上传、同步或导入的内容，不会改写已有分块",
        )
    with col_overlap:
        chunk_overlap = st.number_input(
            "重叠长度",
            min_value=0,
            max_value=5000,
            value=overlap_default,
            step=10,
            help="仅作用于之后入库的内容；需小于分块大小，不会改写已有分块",
        )
    return int(chunk_size), int(chunk_overlap)


def _render_summary_caption(summary: dict | None) -> None:
    """文档/分块计数。须在入库动作之后渲染，才能反映最新状态。"""
    if not summary:
        return
    st.caption(f"{summary['document_count']} 个文档 · {summary['chunk_count']} 个分块")


def _render_file_source(chunk_size: int, chunk_overlap: int) -> bool:
    """上传并入库；返回是否成功，调用方据此刷新摘要与预览。"""
    uploaded_files = st.file_uploader(
        "上传文档",
        type=["pdf", "md", "markdown", "txt"],
        accept_multiple_files=True,
        help="支持 PDF、Markdown 和 TXT",
    )
    upload_clicked = st.button("上传并入库", use_container_width=True)
    if not upload_clicked:
        return False
    if not uploaded_files:
        st.error("请先选择要上传的文件")
        return False
    try:
        files = [(f.name, f.getvalue()) for f in uploaded_files]
        result = backend_api_client.knowledge.upload_files(
            files,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )
        st.toast(
            f"上传成功：{result['document_count']} 个文档，{result['chunk_count']} 个分块"
        )
        return True
    except Exception as e:
        st.error(f"上传失败: {e}")
        return False


def _render_database_source(chunk_size: int, chunk_overlap: int) -> bool:
    """从数据库同步；返回是否成功，调用方据此刷新摘要与预览。"""
    uri = st.text_input(
        "数据库连接",
        placeholder="sqlite:///./data/source.db",
        help="SQLAlchemy 连接串",
        key="db_uri",
    )
    query = st.text_area(
        "查询语句",
        placeholder="SELECT title, content FROM articles",
        key="db_query",
    )
    if st.button("从数据库同步", use_container_width=True):
        if not uri.strip() or not query.strip():
            st.error("请填写数据库连接和查询语句")
            return False
        try:
            result = backend_api_client.knowledge.sync_database(
                uri.strip(),
                query.strip(),
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
            )
            st.toast(
                f"同步成功：{result['document_count']} 个文档，"
                f"{result['chunk_count']} 个分块"
            )
            return True
        except Exception as e:
            st.error(f"同步失败: {e}")
            return False
    return False


def _render_web_source(chunk_size: int, chunk_overlap: int) -> bool:
    """从网页导入；返回是否成功，调用方据此刷新摘要与预览。"""
    url = st.text_input(
        "网页链接",
        placeholder="https://example.com/article",
        key="web_url",
    )
    if st.button("从网页导入", use_container_width=True):
        if not url.strip():
            st.error("请填写网页链接")
            return False
        try:
            result = backend_api_client.knowledge.ingest_web(
                url.strip(),
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
            )
            st.toast(
                f"导入成功：{result['document_count']} 个文档，"
                f"{result['chunk_count']} 个分块"
            )
            return True
        except Exception as e:
            st.error(f"导入失败: {e}")
            return False
    return False


def _render_preview(summary: dict | None) -> None:
    documents = (summary or {}).get("documents") or []
    if not documents:
        return

    st.markdown("#### 文档与分块预览")
    try:
        previews = backend_api_client.knowledge.list_chunks(limit=200)
    except Exception as e:
        st.caption(f"分块预览加载失败: {e}")
        return

    chunks_by_doc: dict[str, list[dict]] = {}
    for item in previews:
        chunks_by_doc.setdefault(item["doc_name"], []).append(item)

    for doc in documents:
        name = doc["name"]
        with st.expander(f"{name} · {doc['chunk_count']} 块", expanded=False):
            if st.button(
                "删除此文档", key=f"delete_doc_{name}", use_container_width=True
            ):
                try:
                    backend_api_client.knowledge.delete_document(name)
                except Exception as e:
                    st.error(f"删除失败: {e}")
                    continue
                # 删除成功后立即整页刷新：文档从列表消失本身就是反馈，
                # 且刷新后的摘要/预览才是最新状态（st.toast 会被 rerun 清掉，故不用）
                st.rerun()
            items = chunks_by_doc.get(name) or []
            if not items:
                st.caption("暂无分块预览")
                continue
            for item in items:
                preview_text = item["content"][:120]
                if len(item["content"]) > 120:
                    preview_text += "……"
                st.text(f"第 {item['chunk_index'] + 1} 块：{preview_text}")


def _render_knowledge_panel():
    st.markdown("### 知识库")
    # 参数输入在前：动作执行时需要用到
    summary = _load_knowledge_summary()
    chunk_size, chunk_overlap = _chunk_controls(summary)

    # 动作区在摘要显示之前执行；成功后同一次运行内即可看到最新数据，无需 rerun
    file_tab, db_tab, web_tab = st.tabs(["文件", "数据库", "网页"])
    changed = False
    with file_tab:
        changed |= _render_file_source(chunk_size, chunk_overlap)
    with db_tab:
        changed |= _render_database_source(chunk_size, chunk_overlap)
    with web_tab:
        changed |= _render_web_source(chunk_size, chunk_overlap)

    # 入库/导入成功后摘要已变化，重新拉取；无动作时复用上方快照
    if changed:
        summary = _load_knowledge_summary()
    _render_summary_caption(summary)
    _render_preview(summary)


def render_sidebar():
    """渲染左侧知识库面板。"""
    try:
        with st.sidebar:
            _render_new_chat()
            st.divider()
            _render_knowledge_panel()
    except Exception as e:
        logger.exception(f"Exception when rendering sidebar: {e}")
        st.markdown("### 侧边栏暂时不可用")
