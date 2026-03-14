from typing import Optional, List, Dict, Tuple
import uuid

from src.frontend.services.api_client import backend_api_client
from src.frontend.states.session import session_state
from src.frontend.states.user import user_state
from src.shared.logger import logger
from src.shared.schemas import auth as auth_schema


class UserLogic:
    @staticmethod
    def register(
        user_data: auth_schema.UserCreate,
    ) -> Tuple[auth_schema.UserRegisterResponse | None, str | None]:
        """用户注册
        Returns:
            Tuple of (result, error_message)
        """
        try:
            response = backend_api_client.user.register(user_data)

            if response.status_code in (200, 201):
                return (auth_schema.UserRegisterResponse(**response.json()), None)
            else:
                logger.error(
                    f"Error when register, Status Code: {response.status_code}, "
                    f"Message: {response.json().get('detail')}"
                )
                error_data = response.json()
                error_msg = error_data.get("detail", "注册失败，请稍后重试")
                if isinstance(error_data, dict) and "detail" in error_data:
                    if isinstance(error_data["detail"], dict):
                        field_errors = {}
                        field_labels = {
                            "email": "邮箱",
                            "username": "用户名",
                            "password": "密码",
                        }
                        for field, msg in error_data["detail"].items():
                            label = field_labels.get(field, field)
                            field_errors[label] = msg
                        return (None, field_errors)
                return (None, error_msg)
        except Exception as e:
            logger.exception(f"Exception when register: {e}")
            return (None, "注册失败，请稍后重试")

    @staticmethod
    def login(login_data: auth_schema.LoginRequest) -> Tuple[bool, str | None]:
        """用户登录
        成功后将 Token 写入 session_state
        Returns:
            Tuple of (success, error_message)
        """
        try:
            response = backend_api_client.user.login(login_data)

            if response.status_code == 200:
                res = auth_schema.LoginResponse(**response.json())

                access_token = res.access_token
                refresh_token = res.refresh_token
                user_info = res.user_info
                user_state.authenticate(access_token, refresh_token, user_info)

                logger.info("login success")
                return (True, None)
            else:
                logger.error(
                    f"Error when login, Status Code: {response.status_code}, "
                    f"Message: {response.json().get('detail')}"
                )
                error_data = response.json()
                error_msg = error_data.get("detail", "登录失败，请检查邮箱和密码")
                return (False, error_msg)
        except Exception as e:
            logger.exception(f"Exception when login: {e}")
            return (False, "登录失败，请稍后重试")

    @staticmethod
    def get_me() -> Optional[auth_schema.UserInfo]:
        """获取当前用户信息"""
        try:
            response = backend_api_client.user.get_me()
            if response.status_code == 200:
                user_info = auth_schema.UserInfo(**response.json())
                user_state.user_info = user_info
                return user_info
            logger.error(
                f"Error when get user info, Status Code: {response.status_code}, "
                f"Message: {response.json().get('detail')}"
            )
            return None
        except Exception as e:
            logger.exception(f"Exception when get user info: {e}")
            return None

    @staticmethod
    def update_user_info(field_key, field_value) -> Optional[auth_schema.UserInfo]:
        """更新当前用户信息"""
        try:
            user_update = auth_schema.UserUpdate(key=field_key, value=field_value)
            response = backend_api_client.user.update_me(user_update)
            if response.status_code == 200:
                user_info = auth_schema.UserInfo(**response.json())
                user_state.user_info = user_info
                return user_info
            logger.error(
                f"Error when update user info, Status Code: {response.status_code}, "
                f"Message: {response.json().get('detail')}"
            )
            return None
        except Exception as e:
            logger.exception(f"Exception when update user info: {e}")
            return None

    @staticmethod
    def logout() -> bool:
        """退出登录"""
        try:
            backend_api_client.user.logout()
            user_state.unauthenticate()
            return True
        except Exception as e:
            logger.exception(f"Exception when logout: {e}")
            return False

    @staticmethod
    def get_available_models() -> List:
        try:
            response = backend_api_client.user.get_available_models()
            if response.status_code == 200:
                user_state.available_models = response.json().get("models")
                return user_state.available_models
            logger.error(
                f"Error when get available models, Status Code: {response.status_code}, "
                f"Message: {response.json().get('detail')}"
            )
            return []
        except Exception as e:
            logger.exception(f"Exception when get available models: {e}")
            return []

    @staticmethod
    def get_history_sessions() -> List[Dict] | None:
        try:
            if user_state.is_authenticated:
                response = backend_api_client.user.get_history()
                if response.status_code == 200:
                    user_state.sessions = response.json().get("sessions")
                    return user_state.sessions
                logger.error(
                    f"Error when get sessions, Status Code: {response.status_code}, "
                    f"Message: {response.json().get('detail')}"
                )
                return user_state.sessions
            else:
                return user_state.sessions
        except Exception as e:
            logger.exception(f"Exception when get sessions: {e}")
            return user_state.sessions

    @staticmethod
    def create_session():
        try:
            user_state.create_session()
            session_state.messages = []
            session_state.session_id = None
            return True
        except Exception as e:
            logger.exception(f"Exception when create session: {e}")
            return False

    @staticmethod
    def rename_session(session_id: uuid.UUID, new_title: str) -> bool:
        try:
            if user_state.is_authenticated:
                response = backend_api_client.user.rename_session(session_id, new_title)
                if response.status_code == 200:
                    user_state.rename_session(session_id, new_title)
                    return True
                else:
                    logger.error(
                        f"Error when rename session, Status Code: {response.status_code}, "
                        f"Message: {response.json().get('detail')}"
                    )
                    return False
            else:
                user_state.rename_session(session_id, new_title)
                return True
        except Exception as e:
            logger.exception(f"Exception when rename session: {e}")
            return False

    @staticmethod
    def delete_session(session_id: uuid.UUID):
        try:
            if user_state.is_authenticated:
                response = backend_api_client.user.delete_session(session_id)
                if response.status_code == 200:
                    user_state.delete_session(session_id)
                    return True
                logger.error(
                    f"Error when delete session, Status Code: {response.status_code}, "
                    f"Message: {response.json().get('detail')}"
                )
                return False
            else:
                user_state.delete_session(session_id)
                return True
        except Exception as e:
            logger.exception(f"Exception when delete session: {e}")
            return False


def get_user_logic():
    return UserLogic()


user_logic = get_user_logic()
