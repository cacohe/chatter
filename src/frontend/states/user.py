import uuid
from typing import List, Dict

import streamlit as st

from src.shared.schemas import session as session_schema
from src.shared.schemas import auth as auth_schema


class UserState:
    @property
    def is_authenticated(self) -> bool:
        return bool(st.session_state.get("access_token"))

    @staticmethod
    def authenticate(
        access_token: str,
        refresh_token: str,
        user_info: auth_schema.UserInfo | None = None,
    ) -> None:
        st.session_state.access_token = access_token
        st.session_state.refresh_token = refresh_token
        st.session_state.user_info = user_info

    @staticmethod
    def unauthenticate() -> None:
        keys_to_clear = ["access_token", "refresh_token", "user_info", "messages"]
        for key in keys_to_clear:
            if key in st.session_state:
                del st.session_state[key]

    @property
    def user_info(self) -> auth_schema.UserInfo | None:
        return (
            st.session_state.get("user_info")
            if st.session_state.get("user_info")
            else None
        )

    @user_info.setter
    def user_info(self, value: auth_schema.UserInfo) -> None:
        st.session_state["user_info"] = value

    def create_session(self) -> bool:
        if not st.session_state.get("current_session"):
            return True

        self.add_session(st.session_state.get("current_session"))
        self.current_session = None
        return True

    @staticmethod
    def add_session(session: Dict) -> bool:
        if not st.session_state.get("sessions"):
            st.session_state["sessions"] = []

        st.session_state.get("sessions").append(session)
        return True

    @staticmethod
    def rename_session(session_id: uuid.UUID, new_title: str) -> None:
        for session in st.session_state.get("sessions", []):
            if session.get("id") == session_id:
                session["title"] = new_title

    @staticmethod
    def delete_session(session_id: uuid.UUID) -> None:
        for session in st.session_state.get("sessions", []):
            if session.id == session_id:
                del st.session_state["sessions"][session_id]

    @property
    def current_session(self) -> session_schema.SessionRead:
        return (
            st.session_state.get("current_session")
            if st.session_state.get("current_session")
            else None
        )

    @current_session.setter
    def current_session(self, session: session_schema.SessionRead) -> None:
        st.session_state["current_session"] = session

    @property
    def sessions(self) -> List[session_schema.SessionRead]:
        return (
            st.session_state.get("sessions") if st.session_state.get("sessions") else []
        )

    @sessions.setter
    def sessions(self, value: List[session_schema.SessionRead]) -> None:
        st.session_state["sessions"] = value

    @property
    def available_models(self) -> List:
        return (
            st.session_state.get("available_models")
            if st.session_state.get("available_models")
            else []
        )

    @available_models.setter
    def available_models(self, value: List) -> None:
        st.session_state["available_models"] = value


user_state = UserState()
