import streamlit as st

from src.frontend.logic.user import user_logic
from src.frontend.utils.validator import AuthValidator
from src.shared.logger import logger
from src.shared.schemas import auth as auth_schema


def _handle_register(username: str, email: str, password: str, confirm_password: str):
    with st.spinner("注册中..."):
        form_data = {
            "username": username,
            "email": email,
            "password": password,
            "confirm_password": confirm_password,
        }
        result = AuthValidator.validate_registration(form_data)

        if result.is_valid:
            register_data = auth_schema.UserCreate(
                email=email, username=username, password=password
            )
            try:
                user_result, error_msg = user_logic.register(register_data)
                if user_result:
                    st.success("注册成功！请登录您的账号。")
                    st.rerun()
                else:
                    if isinstance(error_msg, dict):
                        for field, msg in error_msg.items():
                            st.error(f"{field}: {msg}")
                    else:
                        st.error(f"注册失败: {error_msg}")
            except Exception as e:
                logger.exception(f"Exception when register user: {e}")
                st.error("注册失败，请稍后重试")
        else:
            for field, error in result.errors.items():
                field_labels = {
                    "username": "用户名",
                    "email": "邮箱",
                    "password": "密码",
                    "confirm_password": "确认密码",
                }
                label = field_labels.get(field, field)
                st.error(f"{label}: {error}")


def render_register_content():
    """独立的注册对话框"""
    st.subheader("注册新账号")
    new_username = st.text_input("用户名", key="register_username")
    new_email = st.text_input("邮箱", key="register_email")
    new_password = st.text_input("设置密码", type="password", key="register_password")
    confirm_password = st.text_input(
        "确认密码", type="password", key="confirm_password"
    )

    if st.button(
        "提交注册", key="register_button", type="primary", use_container_width=True
    ):
        _handle_register(new_username, new_email, new_password, confirm_password)


def _handle_login(email: str, password: str):
    """处理登录逻辑"""
    form_data = {
        "email": email,
        "password": password,
    }
    result = AuthValidator.validate_login(form_data)

    if not result.is_valid:
        for field, error in result.errors.items():
            field_labels = {"email": "邮箱", "password": "密码"}
            label = field_labels.get(field, field)
            st.error(f"{label}: {error}")
        return

    with st.spinner("正在登录"):
        try:
            login_data = auth_schema.LoginRequest(email=email, password=password)
            success, error_msg = user_logic.login(login_data)
            if success:
                user_logic.get_me()
                st.rerun()
            else:
                st.error(error_msg or "登录失败，请检查邮箱和密码")
        except Exception as e:
            logger.exception(f"Exception when render login: {e}")
            st.error("登录失败，请稍后重试")


def _handle_oauth_login(auth_provider: str):
    """处理 OAuth 登录"""
    try:
        auth_url = user_logic.oauth_login(auth_provider)
        if auth_url:
            st.session_state["oauth_provider"] = auth_provider
            provider_name = "Google" if auth_provider == "google" else "微信"
            st.success(f"✅ 获取登录链接成功！请点击下方按钮跳转")
            st.page_link(auth_url, label=f"使用 {provider_name} 账号登录", icon="🔗")
        else:
            st.error(f"获取{auth_provider}登录链接失败")
    except Exception as e:
        logger.exception(f"Exception when OAuth login: {e}")
        st.error(f"{auth_provider}登录失败: {e}")


def render_login_content():
    email = st.text_input("邮箱", key="login_email", help="请输入您的注册邮箱")
    password = st.text_input("密码", type="password", key="login_password")

    if st.button(
        "立即登录", key="login_button", type="primary", use_container_width=True
    ):
        _handle_login(email, password)

    st.divider()
    st.markdown("**其他登录方式**")

    col1, col2 = st.columns(2)
    with col1:
        if st.button(
            "Google 登录", key="google_login", use_container_width=True, disabled=True
        ):
            _handle_oauth_login("google")

    with col2:
        if st.button(
            "微信登录", key="wechat_login", use_container_width=True, disabled=True
        ):
            _handle_oauth_login("wechat")

    st.caption("微信和Google登录正在开发中")


@st.dialog("用户认证")
def show_authentication_dialog():
    tab1, tab2 = st.tabs(["登录", "注册"])

    with tab1:
        render_login_content()

    with tab2:
        render_register_content()
