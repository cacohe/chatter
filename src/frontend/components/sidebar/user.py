import streamlit as st

from src.frontend.logic.user import user_logic
from src.shared.schemas import auth as auth_schema


def _show_user_info(user_data):
    col1, col2 = st.columns([1, 3])
    with col1:
        # 模拟头像：商用应用通常使用用户首字母或 Gravatar
        initial = user_data.get("username", "U")[0].upper()
        st.markdown(
            f"""
                <div style="display: flex; align-items: center; justify-content: center; 
                width: 70px; height: 70px; background-color: #FF4B4B; color: white; 
                border-radius: 50%; font-size: 32px; font-weight: bold;">
                    {initial}
                </div>
                """,
            unsafe_allow_html=True
        )
    with col2:
        st.subheader(user_data.get("username", "未知用户"))
        st.caption(f"📧 {user_data.get('email')}")


def _show_account_statistics():
    m1, m2, m3 = st.columns(3)
    # 这里的数值应从数据库聚合查询获得，此处为模拟
    m1.metric("总对话", "128", help="您累计发起的会话总数")
    m2.metric("消息数", "1.2k")
    m3.metric("当前模型", "Qwen-Max")


def _show_account_settings(user_data):
    # 使用 tabs 节省弹窗空间
    tab_info, tab_security = st.tabs(["基本信息", "安全隐私"])

    with tab_info:
        new_name = st.text_input("修改昵称", value=user_data.get("username"))
        if st.button("更新个人资料", use_container_width=True):
            user_logic.update_user_info('username', new_name)
            st.toast("资料已更新！", icon="✅")
            st.rerun()

    with tab_security:
        st.write("注册时间:", str(user_data.get("created_at", "2024-01-01"))[:10])
        if st.button("重置密码", type="secondary", use_container_width=True):
            # TODO 实现真实逻辑
            st.info("重置邮件已发送至您的邮箱。")


def _show_dangerous_area():
    if st.button("退出登录", type="primary", icon="🚶", use_container_width=True):
        user_logic.logout()
        st.rerun()


@st.dialog("个人中心")
def show_user_profile_dialog(user_data: auth_schema.UserInfo) -> None:
    user_data = user_data.model_dump()

    # --- 第一部分：用户信息头部 ---
    _show_user_info(user_data)

    st.divider()

    st.markdown("##### 📊 使用概览")
    _show_account_statistics()


    st.divider()

    st.markdown("##### ⚙️ 账户设置")
    _show_account_settings(user_data)

    st.divider()

    _show_dangerous_area()
