from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer

from src.backend.app.services.auth import AuthService
from src.backend.app.services.chat import ChatService
from src.backend.app.services.llm import LLMService
from src.backend.app.services.session import SessionService
from src.backend.domain.repository_interfaces.auth import IAuthRepository
from src.backend.domain.repository_interfaces.chat import IChatRepository
from src.backend.domain.repository_interfaces.session import ISessionRepository
from src.shared.schemas.auth import UserInfo
from src.backend.infra.repositories.supabase.auth import SupabaseAuthRepository
from src.backend.infra.repositories.supabase.chat import SupabaseChatRepository
from src.backend.infra.repositories.supabase.session import SupabaseSessionRepository


_auth_map = {
    "supabase": SupabaseAuthRepository
}

_chat_map = {
    "supabase": SupabaseChatRepository,
}

_session_map = {
    "supabase": SupabaseSessionRepository,
}


def get_auth_repo(db_type: str = 'supabase'):
    return _auth_map.get(db_type, SupabaseAuthRepository)()


def get_chat_repo(db_type: str = 'supabase'):
    return _chat_map.get(db_type, SupabaseChatRepository)()


def get_session_repo(storage_type: str = 'supabase'):
    return _session_map.get(storage_type, SupabaseSessionRepository)()


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/login")


def get_auth_service(repo: IAuthRepository = Depends(get_auth_repo)) -> AuthService:
    # 每次请求进入路由，FastAPI 都会调用此函数创建一个新的 AuthService 实例
    return AuthService(auth_repo=repo)


def get_chat_service(chat_repo: IChatRepository = Depends(get_chat_repo),
                     session_repo: ISessionRepository = Depends(get_session_repo)):
    return ChatService(chat_repo=chat_repo, session_repo=session_repo)


def get_llm_service(repo: ISessionRepository = Depends(get_session_repo)):
    return LLMService(session_repo=repo)


def get_session_service(repo: ISessionRepository = Depends(get_session_repo)):
    return SessionService(session_repo=repo)


async def get_current_active_user(
    token: str = Depends(oauth2_scheme),
    auth_service: AuthService = Depends(get_auth_service)
) -> UserInfo:
    user = auth_service.get_current_user(token)
    return user
