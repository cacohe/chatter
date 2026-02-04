import streamlit as st
from src.frontend.state import state_manager
from src.frontend.components.sidebar import render_sidebar
from src.frontend.api_client import backend_api_client


# 页面配置
st.set_page_config(page_title="Cacohe", layout="wide")


def render_welcome_screen():
    """渲染未对话时的欢迎界面"""
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown("<h1 style='text-align: center;'>你好，我是 Cacohe</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: gray;'>我可以帮你写代码、答疑解惑或提供创意建议。</p>",
                unsafe_allow_html=True)


def handle_user_input():
    """处理核心交互逻辑"""
    prompt = st.chat_input("在 Cacohe 中输入内容...", disabled=not st.session_state.current_model)

    if prompt:
        # 1. 用户端展示
        state_manager.add_message("user", prompt)
        st.rerun()  # 立即刷新展示用户消息


def main():
    state_manager.init()
    render_sidebar()

    # 展示逻辑
    if not state_manager.messages:
        render_welcome_screen()
    else:
        for msg in state_manager.messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

    # 逻辑判断：是否需要生成 AI 回复
    if state_manager.messages and state_manager.messages[-1]["role"] == "user":
        with st.chat_message("assistant", avatar="✨"):
            stream = backend_api_client.chat_stream(
                prompt=state_manager.messages[-1]["content"],
                model=st.session_state.current_model
            )
            full_response = st.write_stream(stream)
            state_manager.add_message("assistant", full_response)

    handle_user_input()


if __name__ == "__main__":
    main()
