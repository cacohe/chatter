import argparse
import sys

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uuid

from src.backend.controller.chat_controller import AIChatController
from src.config import settings
from src.infra.log.logger import logger


app = FastAPI(title="Cacohe")


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


def main(host: str = None, port: int = None, reload: bool = False):
    """
    启动后端服务
    
    Args:
        host: 监听地址，默认从配置读取
        port: 监听端口，默认从配置读取
        reload: 是否启用自动重载（开发模式）
    """
    host = host or settings.backend_host
    port = port or settings.backend_port
    
    logger.info(f"启动后端服务: {host}:{port}")
    logger.info(f"API文档地址: http://{host}:{port}/docs")
    
    uvicorn.run(
        "src.backend.main:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="启动多模型AI聊天机器人后端服务")
    parser.add_argument(
        "--host",
        type=str,
        default=None,
        help=f"监听地址（默认: {settings.backend_host}）"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=None,
        help=f"监听端口（默认: {settings.backend_port}）"
    )
    parser.add_argument(
        "--reload",
        action="store_true",
        help="启用自动重载（开发模式）"
    )
    
    args = parser.parse_args()
    
    try:
        main(host=args.host, port=args.port, reload=args.reload)
    except KeyboardInterrupt:
        logger.info("服务已停止")
        sys.exit(0)
    except Exception as e:
        logger.error(f"启动失败: {e}")
        sys.exit(1)
