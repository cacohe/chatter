from fastapi import APIRouter, Depends

from src.backend.api.deps import get_current_active_user, get_session_service
from src.backend.app.services.session import SessionService
from src.shared.schemas.session import (
    SessionRead,
    SessionListResponse,
    SessionDeleteRequest,
    SessionRenameRequest,
)


session_router = APIRouter(prefix="/api/v1.0/session", tags=["Session Management"])


@session_router.post("/create", description="创建新会话", response_model=SessionRead)
async def create_session(
    service: SessionService = Depends(get_session_service),
    current_user=Depends(get_current_active_user),
) -> SessionRead:
    return await service.create_session(user_id=current_user.id)


@session_router.post("/rename", description="重命名会话", response_model=bool)
async def rename_session(
    request: SessionRenameRequest,
    service: SessionService = Depends(get_session_service),
) -> bool:
    return await service.rename_session(
        session_id=request.session_id, new_title=request.new_title
    )


@session_router.get(
    "/history", description="获取历史会话", response_model=SessionListResponse
)
async def get_history(
    service: SessionService = Depends(get_session_service),
    current_user=Depends(get_current_active_user),
) -> SessionListResponse:
    return await service.get_history(user_id=current_user.id)


@session_router.post("/delete", description="删除会话", response_model=bool)
async def delete_session(
    request: SessionDeleteRequest,
    service: SessionService = Depends(get_session_service),
    current_user=Depends(get_current_active_user),
) -> bool:
    return await service.delete_session(request.session_id, current_user.id)
