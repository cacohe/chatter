import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from dotenv import load_dotenv


def _apply_streamlit_secrets() -> None:
    try:
        import streamlit as st

        secrets = st.secrets
    except Exception:
        return

    def _flatten(obj: Any, prefix: str = "") -> None:
        if hasattr(obj, "items"):
            items = obj.items()
        elif isinstance(obj, dict):
            items = obj.items()
        else:
            return

        for key, value in items:
            env_key = f"{prefix}{key}" if not prefix else f"{prefix}_{key}"
            env_key = str(env_key).upper()
            if hasattr(value, "items") or isinstance(value, dict):
                _flatten(value, env_key)
            elif value is not None and env_key not in os.environ:
                os.environ[env_key] = str(value)

    try:
        _flatten(secrets)
    except Exception:
        return


def _load_env() -> None:
    root = Path(__file__).resolve().parents[1]  # frontend/
    repo_root = root.parent
    for base in (root, repo_root):
        for name in (".env.local", ".env"):
            path = base / name
            if path.exists():
                load_dotenv(dotenv_path=path, override=False)
                return


@dataclass(frozen=True)
class FrontendSettings:
    backend_api_url: str = "http://localhost:8000/api/v1.0"
    max_history_messages: int = 10


def load_settings() -> FrontendSettings:
    _apply_streamlit_secrets()
    _load_env()
    return FrontendSettings(
        backend_api_url=(
            os.getenv("BACKEND_API_URL") or "http://localhost:8000/api/v1.0"
        ).rstrip("/"),
        max_history_messages=int(os.getenv("MAX_HISTORY_MESSAGES") or "10"),
    )


settings = load_settings()
