import asyncio
import os
from typing import Dict, List, Any
from langchain_core.tools import BaseTool, Tool
from langchain_community.utilities import BingSearchAPIWrapper
import httpx

from src.infra.log.logger import logger

# 尝试导入 SerperAPIWrapper，如果不存在则设为 None
try:
    from langchain_community.utilities import SerperAPIWrapper
except ImportError:
    SerperAPIWrapper = None


class ToolManager:
    """管理联网搜索和自定义MCP工具"""

    def __init__(self):
        self.tools: Dict[str, BaseTool] = {}
        self.setup_tools()

    def setup_tools(self):
        """初始化工具集"""
        # 联网搜索工具 - 优先使用 Serper，如果没有则使用 Bing
        if os.getenv("SERPER_API_KEY") and SerperAPIWrapper is not None:
            try:
                search = SerperAPIWrapper(serper_api_key=os.getenv("SERPER_API_KEY"))
                self.tools["web_search"] = Tool(
                    name="web_search",
                    description="搜索网络获取最新信息",
                    func=search.run
                )
            except Exception:
                logger.warning("Serper API 未配置，请检查环境变量 SERPER_API_KEY")
        elif os.getenv("BING_SUBSCRIPTION_KEY"):
            try:
                search = BingSearchAPIWrapper(bing_subscription_key=os.getenv("BING_SUBSCRIPTION_KEY"))
                self.tools["web_search"] = Tool(
                    name="web_search",
                    description="搜索网络获取最新信息",
                    func=search.run
                )
            except Exception:
                logger.warning("Bing API 未配置，请检查环境变量 BING_SUBSCRIPTION_KEY")

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
            # 创建同步包装函数，因为 Tool 的 func 必须是同步的
            def make_sync_wrapper(ep: str):
                def sync_wrapper(query: str) -> str:
                    """同步包装器，调用异步 MCP 服务器"""
                    try:
                        # 尝试获取当前事件循环
                        try:
                            loop = asyncio.get_running_loop()
                            # 如果事件循环已经在运行，使用线程池在新线程中运行
                            import concurrent.futures
                            with concurrent.futures.ThreadPoolExecutor() as executor:
                                def run_async():
                                    new_loop = asyncio.new_event_loop()
                                    asyncio.set_event_loop(new_loop)
                                    try:
                                        return new_loop.run_until_complete(self._call_mcp_server_sync(ep, query))
                                    finally:
                                        new_loop.close()
                                future = executor.submit(run_async)
                                return future.result(timeout=30.0)
                        except RuntimeError:
                            # 没有运行中的事件循环，可以直接使用
                            loop = asyncio.get_event_loop()
                            return loop.run_until_complete(self._call_mcp_server_sync(ep, query))
                    except Exception as e:
                        return f"MCP调用失败: {str(e)}"
                return sync_wrapper
            
            self.tools[tool_name] = Tool(
                name=tool_name,
                description=f"通过MCP调用{tool_name}功能",
                func=make_sync_wrapper(endpoint)
            )

    async def _call_mcp_server_sync(self, endpoint: str, query: str) -> str:
        """调用自定义MCP服务器（内部异步方法）"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    endpoint,
                    json={"query": query},
                    timeout=30.0
                )
                return response.text
        except Exception as e:
            return f"MCP调用失败: {str(e)}"

    async def call_mcp_server(self, endpoint: str, request_data: Dict) -> str:
        """调用自定义MCP服务器（异步方法，保留用于直接调用）"""
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
