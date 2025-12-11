from typing import Dict, Any, List

from langchain_core.messages import HumanMessage

from src.backend.manager.model_manager import ModelManager
from src.backend.manager.tool_manager import ToolManager
from src.backend.manager.context_manager import ContextManager


class AIChatController:
    """AI聊天机器人主控制器"""

    def __init__(self):
        self.model_manager = ModelManager()
        self.tool_manager = ToolManager()
        self.context_manager = ContextManager()

    async def process_message(self, session_id: str, user_input: str,
                              use_tools: bool = True, **kwargs) -> Dict[str, Any]:
        """处理用户消息并生成回复"""

        # 添加用户消息到上下文
        self.context_manager.add_message(session_id, "human", user_input)

        # 检查是否需要工具调用
        tool_result = ""
        if use_tools and self._needs_tool_assistance(user_input):
            tool_result = await self._handle_tool_calls(user_input)

        # 准备完整的消息上下文（创建副本以避免修改原始列表）
        messages = self.context_manager.get_messages(session_id).copy()

        if tool_result:
            # 将工具结果添加到消息上下文中（仅用于本次模型调用）
            tool_message = f"工具调用结果: {tool_result}"
            messages.append(HumanMessage(content=f"基于以下信息回答问题: {tool_message}\n\n原始问题: {user_input}"))

        # 调用模型生成回复
        response = await self.model_manager.generate_response(messages, **kwargs)

        # 添加AI回复到上下文
        self.context_manager.add_message(session_id, "ai", response)

        return {
            "response": response,
            "tools_used": bool(tool_result),
            "tool_result": tool_result,
            "model_used": self.model_manager.current_model
        }

    def _needs_tool_assistance(self, user_input: str) -> bool:
        """判断是否需要工具调用"""
        tool_keywords = [
            "天气", "新闻", "搜索", "查询", "计算", "最近", "最新",
            "weather", "news", "search", "current", "latest"
        ]
        return any(keyword in user_input.lower() for keyword in tool_keywords)

    async def _handle_tool_calls(self, user_input: str) -> str:
        """处理工具调用"""
        tool_results = []

        # 判断使用哪种工具
        if any(keyword in user_input for keyword in ["天气", "weather"]):
            result = await self.tool_manager.execute_tool("weather", user_input)
            tool_results.append(f"天气信息: {result}")

        if any(keyword in user_input for keyword in ["搜索", "查找", "search"]):
            result = await self.tool_manager.execute_tool("web_search", user_input)
            tool_results.append(f"搜索结果: {result}")

        return " ".join(tool_results) if tool_results else ""

    def switch_model(self, model_name: str) -> bool:
        """切换模型"""
        return self.model_manager.switch_model(model_name)

    def get_available_models(self) -> List[str]:
        """获取可用模型列表"""
        return self.model_manager.list_available_models()

    def get_available_tools(self) -> List[Dict]:
        """获取可用工具列表"""
        return self.tool_manager.list_tools()

    def clear_conversation(self, session_id: str):
        """清空对话"""
        self.context_manager.clear_session(session_id)
