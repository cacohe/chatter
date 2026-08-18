"""主区聊天：展示历史通过 API 从后端获取，本页只负责渲染。"""

import streamlit as st

from logger import logger
from logic.session import session_logic


def _render_citations(message: dict) -> None:
    """渲染回答的参考来源面板。

    根据 used 字段区分「已引用」与「检索到但未引用」两组，
    帮助用户判断回答的证据覆盖情况。
    """
    citations = message.get("citations") or []
    if not citations:
        return
    # 按校验结果分三组：已引用 / 未引用 / 未校验
    used = [c for c in citations if c.get("used") is True]
    unused = [c for c in citations if c.get("used") is False]
    unvalidated = [c for c in citations if c.get("used") is None]

    with st.expander("参考来源", expanded=False):
        if used:
            for citation in used:
                _render_single_citation(citation)
        if unused:
            st.divider()
            st.caption("以下来源已检索到但未被回答引用：")
            for citation in unused:
                _render_single_citation(citation)
        if unvalidated:
            st.divider()
            st.caption("以下来源未经引用校验：")
            for citation in unvalidated:
                _render_single_citation(citation)


def _render_single_citation(citation: dict) -> None:
    """渲染单条引用信息：编号、文档名、来源地址、相关度、摘要。"""
    doc_name = citation.get("doc_name") or "未知来源"
    chunk_index = int(citation.get("chunk_index") or 0) + 1
    st.caption(f"[{citation.get('index')}] {doc_name} · 第 {chunk_index} 块")
    source_uri = citation.get("source_uri") or ""
    score = citation.get("score")
    # 来源链接与相关度是机器生成的证据信息，单独展示便于人工核验。
    if source_uri:
        st.caption(f"来源地址：{source_uri}")
    if isinstance(score, int | float):
        st.caption(f"相关度：{float(score):.4f}")
    snippet = citation.get("snippet") or ""
    if snippet:
        st.text(snippet)


def _render_chat_history():
    try:
        messages = session_logic.load_display_history()
    except Exception as e:
        logger.exception(f"Failed to load display history: {e}")
        st.error("加载对话历史失败")
        return

    for msg in messages:
        role = msg.get("role")
        if hasattr(role, "value"):
            role = role.value
        with st.chat_message(str(role)):
            st.markdown(msg.get("content") or "")
            if str(role) == "assistant":
                _render_citations(msg)


def _render_chat_content():
    _render_chat_history()

    prompt = st.chat_input("基于知识库提问…")

    if prompt:
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            response_placeholder = st.empty()
            full_response = ""

            try:
                for chunk, error_msg in session_logic.chat_stream(content=prompt):
                    if error_msg:
                        st.error(error_msg)
                        break
                    if chunk:
                        if chunk.startswith("Error:"):
                            st.error(
                                chunk.removeprefix("Error:").strip() or "发生未知错误"
                            )
                            break
                        full_response += chunk
                        response_placeholder.markdown(full_response)
            except Exception as e:
                st.error(f"请求失败: {e!s}")

        st.session_state["_needs_rerun"] = True


def render_chat_interface():
    """渲染主区问答界面。"""
    _render_chat_content()
