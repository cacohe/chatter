from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Annotated
from pydantic import BaseModel
import uuid

from src.backend.database import get_db
from src.backend.controller.db_chat_controller import DBChatController
from src.backend.models.user import User
from src.backend.dependencies import CurrentActiveUser

router = APIRouter(prefix="/chat", tags=["聊天"])


class ChatRequest(BaseModel):
    """聊天请求模型"""
    message: str
    session_id: str = None
    use_tools: bool = True
    temperature: float = 0.7


class ChatResponse(BaseModel):
    """聊天响应模型"""
    response: str
    session_id: str
    tools_used: bool
    tool_result: str = ""
    model_used: str


class ModelSwitchRequest(BaseModel):
    """模型切换请求"""
    model_name: str


@router.post("/message", response_model=ChatResponse)
async def chat_message(
    request: ChatRequest,
    current_user: Annotated[User, Depends(get_current_user)] = None,
    db: Session = Depends(get_db)
):
    """
    发送聊天消息（需要认证）

    如果不提供session_id，会自动创建一个新会话
    """
    try:
        # 如果没有提供session_id，生成一个新的
        if not request.session_id:
            request.session_id = str(uuid.uuid4())

        # 创建控制器实例
        controller = DBChatController(db)

        # 处理消息
        result = await controller.process_message(
            session_id=request.session_id,
            user_id=current_user.id,
            user_input=request.message,
            use_tools=request.use_tools,
            temperature=request.temperature
        )

        return ChatResponse(
            response=result["response"],
            session_id=request.session_id,
            tools_used=result["tools_used"],
            tool_result=result.get("tool_result", ""),
            model_used=result["model_used"]
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"处理消息失败: {str(e)}"
        )


@router.post("/models/switch")
async def switch_model(
    request: ModelSwitchRequest,
    current_user: Annotated[User, Depends(get_current_user)] = None,
    db: Session = Depends(get_db)
):
    """切换模型（需要认证）"""
    controller = DBChatController(db)
    success = controller.switch_model(request.model_name)
    return {"success": success, "current_model": request.model_name}


@router.get("/models")
async def get_models(
    current_user: Annotated[User, Depends(get_current_user)] = None,
    db: Session = Depends(get_db)
):
    """获取可用模型列表（需要认证）"""
    controller = DBChatController(db)
    models = controller.get_available_models()
    return {"models": models}


@router.get("/tools")
async def get_tools(
    current_user: Annotated[User, Depends(get_current_user)] = None,
    db: Session = Depends(get_db)
):
    """获取可用工具列表（需要认证）"""
    controller = DBChatController(db)
    tools = controller.get_available_tools()
    return {"tools": tools}


@router.post("/sessions/{session_id}/clear")
async def clear_session(
    session_id: str,
    current_user: Annotated[User, Depends(get_current_user)] = None,
    db: Session = Depends(get_db)
):
    """
    清空会话历史（需要认证）

    只清空消息历史，保留session和system消息
    """
    controller = DBChatController(db)

    # 验证权限
    db_session = controller.session_repo.get_by_session_id(session_id)
    if not db_session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="会话不存在"
        )

    if db_session.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权操作此会话"
        )

    controller.clear_conversation(session_id)
    return {"success": True, "message": "会话历史已清空"}
