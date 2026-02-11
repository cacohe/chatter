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
            "confirm_password": confirm_password
        }
        result = AuthValidator.validate_registration(form_data)

        if result.is_valid:
            register_data = auth_schema.UserCreate(
                email=email, username=username, password=password
            )
            try:
                if user_logic.register(register_data):
                    st.success("注册成功！请登录您的账号。")
                    st.rerun()
            except Exception as e:
                logger.exception(f"Exception when register user: {e}")
                st.error(f"注册失败: {e}")
        else:
            logger.error(f'Error when render register: {result.is_valid}, error: {result.errors}')
            st.rerun()


def render_register_content():
    """独立的注册对话框"""
    st.subheader("注册新账号")
    new_username = st.text_input("用户名", key="register_username")
    new_email = st.text_input("邮箱", key="register_email")
    new_password = st.text_input(
        "设置密码", type="password", key="register_password"
    )
    confirm_password = st.text_input(
        "确认密码", type="password", key="confirm_password"
    )

    if st.button("提交注册", key="register_button", type="primary", use_container_width=True):
        _handle_register(
            new_username, new_email, new_password, confirm_password
        )


def _handle_login(email: str, password: str):
    """处理登录逻辑"""
    # TODO: 表单输入数据的格式验证

    # 尝试登录
    with st.spinner("正在登录"):
        try:
            login_data = auth_schema.LoginRequest(email=email, password=password)
            if user_logic.login(login_data):
                user_logic.get_me()
                st.rerun()
            else:
                logger.error('Error when render login')
        except Exception as e:
            logger.exception(f"Exception when render login: {e}")


def render_login_content():
    email = st.text_input(
        "邮箱", key="login_email", help="请输入您的注册邮箱"
    )
    password = st.text_input(
        "密码", type="password", key="login_password"
    )

    if st.button("立即登录", key="login_button", type="primary", use_container_width=True):
        _handle_login(email, password)


@st.dialog('用户认证')
def show_authentication_dialog():
    tab1, tab2 = st.tabs(["登录", "注册"])

    with tab1:
        render_login_content()

    with tab2:
        render_register_content()
