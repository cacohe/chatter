from pathlib import Path

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uuid

from src.backend.controller.chat_controller import AIChatController


app = FastAPI(title="多模型AI聊天机器人")
env_path = Path(__file__).parent.parent.parent.resolve() / ".env"
load_dotenv(dotenv_path=env_path)


# CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局控制器实例
controller = AIChatController()


# Pydantic模型
class ChatRequest(BaseModel):
    message: str
    session_id: str = None
    use_tools: bool = True
    temperature: float = 0.7


class ChatResponse(BaseModel):
    response: str
    session_id: str
    tools_used: bool
    tool_result: str = ""
    model_used: str


class ModelSwitchRequest(BaseModel):
    model_name: str


@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """聊天端点"""
    try:
        if not request.session_id:
            request.session_id = str(uuid.uuid4())

        result = await controller.process_message(
            session_id=request.session_id,
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
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/models/switch")
async def switch_model(request: ModelSwitchRequest):
    """切换模型"""
    success = controller.switch_model(request.model_name)
    return {"success": success, "current_model": request.model_name}


@app.get("/models")
async def get_models():
    """获取可用模型列表"""
    models = controller.get_available_models()
    return {"models": models}


@app.get("/tools")
async def get_tools():
    """获取可用工具列表"""
    return {"tools": controller.get_available_tools()}


@app.post("/sessions/{session_id}/clear")
async def clear_session(session_id: str):
    """清空会话"""
    controller.clear_conversation(session_id)
    return {"success": True}


def main():
    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
