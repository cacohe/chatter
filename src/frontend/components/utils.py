import streamlit as st


def show_error_info():
    st.markdown("### 应用遇到问题")
    st.markdown("抱歉，应用遇到了一些问题。请尝试：")
    st.markdown("1. 刷新页面")
    st.markdown("2. 检查网络连接")
    st.markdown("3. 稍后重试")