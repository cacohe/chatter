import streamlit as st

from logger import logger
from logic.session import session_logic
from services.api_client import backend_api_client


def _render_new_conversation():
    if st.button("开启新对话", use_container_width=True, help="清空本轮对话记忆"):
        session_logic.clear_conversation()
        st.session_state["_needs_rerun"] = True


def _load_knowledge_status() -> dict | None:
    try:
        return backend_api_client.knowledge.get_status()
    except Exception as e:
        logger.exception(f"Failed to load knowledge status: {e}")
        return None


def _render_knowledge_panel():
    st.markdown("### 知识库")

    status = _load_knowledge_status()
    if status:
        st.caption(
            f"{status['document_count']} 个文档 · {status['chunk_count']} 个分块"
        )
        chunk_size = st.number_input(
            "分块大小（字符）",
            min_value=50,
            max_value=10000,
            value=int(status.get("chunk_size", 500)),
            step=50,
            help="每个分块最多包含多少字符",
        )
        chunk_overlap = st.number_input(
            "重叠长度（字符）",
            min_value=0,
            max_value=5000,
            value=int(status.get("chunk_overlap", 50)),
            step=10,
            help="相邻两个分块之间重复多少字符，需小于分块大小",
        )
    else:
        st.warning("无法连接后端知识库服务")
        chunk_size = st.number_input(
            "分块大小（字符）", min_value=50, max_value=10000, value=500
        )
        chunk_overlap = st.number_input(
            "重叠长度（字符）", min_value=0, max_value=5000, value=50
        )

    uploaded_files = st.file_uploader(
        "上传文档",
        type=["txt", "md", "markdown"],
        accept_multiple_files=True,
        help="支持 txt、md 等纯文本文件",
    )

    col_upload, col_reload = st.columns(2)
    with col_upload:
        upload_clicked = st.button("上传并入库", use_container_width=True)
    with col_reload:
        reload_clicked = st.button(
            "按新参数重新分块", use_container_width=True, help="对已有文档重新切分"
        )

    if upload_clicked:
        if not uploaded_files:
            st.error("请先选择要上传的文件")
        else:
            try:
                files = [(f.name, f.getvalue()) for f in uploaded_files]
                result = backend_api_client.knowledge.upload_files(
                    files,
                    chunk_size=int(chunk_size),
                    chunk_overlap=int(chunk_overlap),
                )
                st.success(
                    f"上传成功：{result['document_count']} 个文档，"
                    f"{result['chunk_count']} 个分块"
                )
                st.session_state["_needs_rerun"] = True
            except Exception as e:
                st.error(f"上传失败: {e}")

    if reload_clicked:
        try:
            result = backend_api_client.knowledge.reload(
                chunk_size=int(chunk_size),
                chunk_overlap=int(chunk_overlap),
            )
            st.success(
                f"已重新分块：{result['document_count']} 个文档，"
                f"{result['chunk_count']} 个分块"
            )
            st.session_state["_needs_rerun"] = True
        except Exception as e:
            st.error(f"重新分块失败: {e}")

    if status and status.get("documents"):
        with st.expander("文档与分块预览", expanded=False):
            for doc in status["documents"]:
                st.markdown(f"**{doc['name']}** · {doc['chunk_count']} 块")
            try:
                previews = backend_api_client.knowledge.list_chunks(limit=20)
                for item in previews:
                    preview_text = item["content"][:120]
                    if len(item["content"]) > 120:
                        preview_text += "……"
                    st.text(
                        f"《{item['doc_name']}》第 {item['chunk_index'] + 1} 块："
                        f"{preview_text}"
                    )
            except Exception as e:
                st.caption(f"分块预览加载失败: {e}")


def render_sidebar():
    try:
        with st.sidebar:
            _render_new_conversation()
            st.divider()
            _render_knowledge_panel()
    except Exception as e:
        logger.exception(f"Exception when rendering sidebar: {e}")
        st.markdown("### 侧边栏暂时不可用")
