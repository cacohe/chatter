"""侧边栏：分块参数、文件/数据库/网页导入、文档预览与删除。"""

import streamlit as st

from logger import logger
from logic.session import session_logic
from services.api_client import backend_api_client


def _render_new_conversation():
    if st.button("开启新对话", use_container_width=True, help="清空本轮对话记忆"):
        session_logic.clear_conversation()
        st.session_state["_needs_rerun"] = True


def _load_knowledge_summary() -> dict | None:
    try:
        return backend_api_client.knowledge.get_summary()
    except Exception as e:
        logger.exception(f"Failed to load knowledge summary: {e}")
        return None


def _mark_success(message: str) -> None:
    # Streamlit rerun 会清掉瞬时 toast，先写入 session 再在下一轮显示
    st.session_state["_kb_notice"] = message
    st.session_state["_needs_rerun"] = True


def _show_kb_notice() -> None:
    message = st.session_state.pop("_kb_notice", None)
    if message:
        st.success(message)


def _chunk_controls(summary: dict | None) -> tuple[int, int]:
    if summary:
        st.caption(
            f"{summary['document_count']} 个文档 · {summary['chunk_count']} 个分块"
        )
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
            help="每个分块的目标长度（按句子切分）",
        )
    with col_overlap:
        chunk_overlap = st.number_input(
            "重叠长度",
            min_value=0,
            max_value=5000,
            value=overlap_default,
            step=10,
            help="相邻两个分块之间重复的内容长度，需小于分块大小",
        )
    return int(chunk_size), int(chunk_overlap)


def _render_file_source(chunk_size: int, chunk_overlap: int) -> None:
    uploaded_files = st.file_uploader(
        "上传文档",
        type=["pdf", "md", "markdown", "txt"],
        accept_multiple_files=True,
        help="支持 PDF、Markdown 和 TXT",
    )
    upload_clicked = st.button("上传并入库", use_container_width=True)
    if not upload_clicked:
        return
    if not uploaded_files:
        st.error("请先选择要上传的文件")
        return
    try:
        files = [(f.name, f.getvalue()) for f in uploaded_files]
        result = backend_api_client.knowledge.upload_files(
            files,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )
        _mark_success(
            f"上传成功：{result['document_count']} 个文档，{result['chunk_count']} 个分块"
        )
    except Exception as e:
        st.error(f"上传失败: {e}")


def _render_database_source(chunk_size: int, chunk_overlap: int) -> None:
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
            return
        try:
            result = backend_api_client.knowledge.sync_database(
                uri.strip(),
                query.strip(),
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
            )
            _mark_success(
                f"同步成功：{result['document_count']} 个文档，"
                f"{result['chunk_count']} 个分块"
            )
        except Exception as e:
            st.error(f"同步失败: {e}")


def _render_web_source(chunk_size: int, chunk_overlap: int) -> None:
    url = st.text_input(
        "网页链接",
        placeholder="https://example.com/article",
        key="web_url",
    )
    if st.button("从网页导入", use_container_width=True):
        if not url.strip():
            st.error("请填写网页链接")
            return
        try:
            result = backend_api_client.knowledge.ingest_web(
                url.strip(),
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
            )
            _mark_success(
                f"导入成功：{result['document_count']} 个文档，"
                f"{result['chunk_count']} 个分块"
            )
        except Exception as e:
            st.error(f"导入失败: {e}")


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
                    _mark_success(f"已删除：{name}")
                except Exception as e:
                    st.error(f"删除失败: {e}")
                continue
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
    _show_kb_notice()
    summary = _load_knowledge_summary()
    chunk_size, chunk_overlap = _chunk_controls(summary)

    if st.button(
        "按新参数重新分块", use_container_width=True, help="对已有文档重新切分"
    ):
        try:
            result = backend_api_client.knowledge.reload(
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
            )
            _mark_success(
                f"已重新分块：{result['document_count']} 个文档，"
                f"{result['chunk_count']} 个分块"
            )
        except Exception as e:
            st.error(f"重新分块失败: {e}")

    file_tab, db_tab, web_tab = st.tabs(["文件", "数据库", "网页"])
    with file_tab:
        _render_file_source(chunk_size, chunk_overlap)
    with db_tab:
        _render_database_source(chunk_size, chunk_overlap)
    with web_tab:
        _render_web_source(chunk_size, chunk_overlap)

    _render_preview(summary)


def render_sidebar():
    """渲染左侧知识库面板。"""
    try:
        with st.sidebar:
            _render_new_conversation()
            st.divider()
            _render_knowledge_panel()
    except Exception as e:
        logger.exception(f"Exception when rendering sidebar: {e}")
        st.markdown("### 侧边栏暂时不可用")
