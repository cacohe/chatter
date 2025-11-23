import asyncio
import os
from typing import Dict, List
from langchain_core.tools import BaseTool, Tool
from langchain_community.utilities import BingSearchAPIWrapper
import httpx


class ToolManager:
    """管理联网搜索和自定义MCP工具"""

    def __init__(self):
        self.tools: Dict[str, BaseTool] = {}
        self.setup_tools()

    def setup_tools(self):
        """初始化工具集"""
        # 联网搜索工具
        if os.getenv("SERPER_API_KEY"):
            search = BingSearchAPIWrapper()
            self.tools["web_search"] = Tool(
                name="web_search",
                description="搜索网络获取最新信息",
                func=search.run
            )

        # 添加自定义MCP工具
        self.setup_mcp_tools()

    def setup_mcp_tools(self):
        """设置自定义MCP工具"""
        # MCP服务器配置
        self.mcp_servers = {
            "calculator": "http://localhost:8080/mcp",
            "weather": "http://localhost:8081/mcp",
            "database": "http://localhost:8082/mcp"
        }

        for tool_name, endpoint in self.mcp_servers.items():
            self.tools[tool_name] = Tool(
                name=tool_name,
                description=f"通过MCP调用{tool_name}功能",
                func=lambda x, ep=endpoint: self.call_mcp_server(ep, x)
            )

    async def call_mcp_server(self, endpoint: str, request_data: Dict) -> str:
        """调用自定义MCP服务器"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    endpoint,
                    json=request_data,
                    timeout=30.0
                )
                return response.text
        except Exception as e:
            return f"MCP调用失败: {str(e)}"

    async def execute_tool(self, tool_name: str, input_data: str) -> str:
        """执行指定工具"""
        if tool_name not in self.tools:
            return f"工具 {tool_name} 不存在"

        try:
            tool = self.tools[tool_name]
            result = await asyncio.get_event_loop().run_in_executor(
                None, tool.run, input_data
            )
            return result
        except Exception as e:
            return f"工具执行失败: {str(e)}"

    def list_tools(self) -> List[Dict]:
        """获取可用工具列表"""
        return [{"name": name, "description": tool.description}
                for name, tool in self.tools.items()]
