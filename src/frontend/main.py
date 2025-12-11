import streamlit as st
import requests

from src.config import settings
from src.frontend.routes import get_available_models, send_message, switch_model


st.set_page_config(
    page_title="多模型AI聊天助手",
    page_icon="😁",
    layout="wide"
)

# API基础URL
_API_BASE = f"http://{settings.backend_ip}:{settings.backend_port}"


def initialize_session():
    """初始化会话状态"""
    if "session_id" not in st.session_state:
        st.session_state.session_id = None
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "current_model" not in st.session_state:
        st.session_state.current_model = "qwen"


def main():
    """主界面"""
    st.title("😀 多模型AI聊天机器人")
    st.markdown("支持多模型切换、联网搜索和自定义MCP工具调用")

    initialize_session()

    # 侧边栏
    with st.sidebar:
        st.header("配置")

        # 模型选择
        available_models = get_available_models()
        if not available_models:
            st.warning("没有可用的模型，请检查后端服务")
            available_models = [st.session_state.current_model] if st.session_state.current_model else ["qwen"]
        
        current_model = st.selectbox(
            "选择AI模型",
            available_models,
            index=available_models.index(st.session_state.current_model)
            if st.session_state.current_model in available_models else 0
        )

        if current_model != st.session_state.current_model:
            if switch_model(current_model):
                st.session_state.current_model = current_model
                st.success(f"已切换到 {current_model} 模型")
            else:
                st.error("模型切换失败")

        # 工具设置
        st.subheader("工具设置")
        use_tools = st.checkbox("启用联网搜索", value=True)
        use_mcp = st.checkbox("启用MCP工具", value=True)

        # 会话管理
        st.subheader("会话管理")
        if st.button("清空对话历史"):
            if st.session_state.session_id:
                requests.post(f"{_API_BASE}/sessions/{st.session_state.session_id}/clear")
            st.session_state.messages = []
            st.session_state.session_id = None
            st.rerun()

    # 聊天主界面
    chat_container = st.container()

    with chat_container:
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
                if "model" in message:
                    st.caption(f"模型: {message['model']}")

    # 用户输入
    if prompt := st.chat_input("请输入您的问题..."):
        # 添加用户消息
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # 获取AI回复
        with st.chat_message("assistant"):
            with st.spinner("思考中..."):
                response = send_message(prompt, use_tools=use_tools or use_mcp)

                if response:
                    st.markdown(response["response"])
                    if response["tools_used"]:
                        st.caption("🔧 已使用工具获取信息")
                    st.caption(f"模型: {response['model_used']}")

                    # 添加AI回复到历史
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": response["response"],
                        "model": response["model_used"]
                    })

                    # 更新会话ID
                    if not st.session_state.session_id:
                        st.session_state.session_id = response["session_id"]
                else:
                    st.error("抱歉，请求大模型服务失败")


if __name__ == "__main__":
    main()
