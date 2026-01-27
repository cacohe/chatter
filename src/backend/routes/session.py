from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Annotated

from src.backend.database import get_db
from src.backend.repository.session_repository import SessionRepository
from src.backend.repository.message_repository import MessageRepository
from src.backend.schemas.session import SessionResponse, SessionDetail
from src.backend.models.user import User
from src.backend.dependencies import CurrentActiveUser

router = APIRouter(prefix="/sessions", tags=["会话管理"])


@router.get("", response_model=list[SessionResponse])
async def get_user_sessions(
    skip: int = 0,
    limit: int = 100,
    current_user: Annotated[User, Depends(get_current_user)] = None,
    db: Session = Depends(get_db)
):
    """获取当前用户的所有会话"""
    session_repo = SessionRepository(db)
    sessions = session_repo.get_user_sessions(current_user.id, skip=skip, limit=limit)
    return sessions


@router.get("/{session_id}", response_model=SessionDetail)
async def get_session_detail(
    session_id: str,
    current_user: Annotated[User, Depends(get_current_user)] = None,
    db: Session = Depends(get_db)
):
    """获取会话详情（包含所有消息）"""
    session_repo = SessionRepository(db)
    message_repo = MessageRepository(db)

    # 获取会话
    db_session = session_repo.get_by_session_id(session_id)
    if not db_session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="会话不存在"
        )

    # 验证权限
    if db_session.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权访问此会话"
        )

    # 获取消息
    messages = message_repo.get_session_messages(db_session.id)

    return SessionDetail(
        id=db_session.id,
        session_id=db_session.session_id,
        user_id=db_session.user_id,
        title=db_session.title,
        model_name=db_session.model_name,
        created_at=db_session.created_at,
        updated_at=db_session.updated_at,
        messages=messages
    )


@router.delete("/{session_id}")
async def delete_session(
    session_id: str,
    current_user: Annotated[User, Depends(get_current_user)] = None,
    db: Session = Depends(get_db)
):
    """删除会话"""
    session_repo = SessionRepository(db)

    # 获取会话
    db_session = session_repo.get_by_session_id(session_id)
    if not db_session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="会话不存在"
        )

    # 验证权限
    if db_session.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权删除此会话"
        )

    # 删除会话
    session_repo.delete_session(session_id)
    return {"success": True, "message": "会话已删除"}
