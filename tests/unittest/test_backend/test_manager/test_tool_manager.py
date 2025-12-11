import pytest
from unittest.mock import Mock, patch, AsyncMock
import os
from src.backend.manager.tool_manager import ToolManager


class TestToolManager:
    """测试ToolManager类"""

    @patch.dict(os.environ, {"SERPER_API_KEY": "test_key"})
    @patch('src.backend.manager.tool_manager.BingSearchAPIWrapper')
    def test_setup_tools_with_search(self, mock_search_wrapper):
        """测试初始化工具集（包含搜索工具）"""
        # 设置mock返回值
        mock_search_instance = Mock()
        mock_search_wrapper.return_value = mock_search_instance
        
        # 创建ToolManager实例
        manager = ToolManager()
        
        # 验证搜索工具被正确初始化
        mock_search_wrapper.assert_called_once()
        
        # 验证工具字典中包含了搜索工具
        assert "web_search" in manager.tools
        # 验证包含了MCP工具
        mcp_tools = ["calculator", "weather", "database"]
        for tool in mcp_tools:
            assert tool in manager.tools
        
        # 验证工具总数
        assert len(manager.tools) == 4  # web_search + 3个MCP工具

    @patch.dict(os.environ, {}, clear=True)  # 清除环境变量
    def test_setup_tools_without_search(self):
        """测试初始化工具集（不包含搜索工具）"""
        # 创建ToolManager实例
        manager = ToolManager()
        
        # 验证工具字典中不包含搜索工具
        assert "web_search" not in manager.tools
        # 但仍应包含MCP工具
        mcp_tools = ["calculator", "weather", "database"]
        for tool in mcp_tools:
            assert tool in manager.tools
        
        # 验证工具总数
        assert len(manager.tools) == 3  # 3个MCP工具

    def test_setup_mcp_tools(self):
        """测试设置MCP工具"""
        manager = ToolManager()
        
        # 验证MCP工具被正确设置
        mcp_tools = ["calculator", "weather", "database"]
        for tool in mcp_tools:
            assert tool in manager.tools
            assert manager.tools[tool].name == tool
            assert f"通过MCP调用{tool}功能" in manager.tools[tool].description

    @pytest.mark.asyncio
    async def test_call_mcp_server_success(self):
        """测试成功调用MCP服务器"""
        manager = ToolManager()
        
        # 使用patch模拟httpx.AsyncClient
        with patch('src.backend.manager.tool_manager.httpx.AsyncClient') as mock_client:
            # 设置mock返回值
            mock_response = Mock()
            mock_response.text = "MCP服务器响应"
            mock_async_client_instance = AsyncMock()
            mock_async_client_instance.__aenter__.return_value = mock_async_client_instance
            mock_async_client_instance.post = AsyncMock(return_value=mock_response)
            mock_client.return_value = mock_async_client_instance
            
            # 调用方法
            result = await manager.call_mcp_server("http://localhost:8080/mcp", {"test": "data"})
            
            # 验证调用
            mock_client.assert_called_once()
            mock_async_client_instance.post.assert_awaited_once_with(
                "http://localhost:8080/mcp",
                json={"test": "data"},
                timeout=30.0
            )
            
            # 验证返回值
            assert result == "MCP服务器响应"

    @pytest.mark.asyncio
    async def test_call_mcp_server_exception(self):
        """测试调用MCP服务器时发生异常"""
        manager = ToolManager()
        
        # 使用patch模拟httpx.AsyncClient抛出异常
        with patch('src.backend.manager.tool_manager.httpx.AsyncClient') as mock_client:
            # 设置mock抛出异常
            mock_async_client_instance = AsyncMock()
            mock_async_client_instance.__aenter__.return_value = mock_async_client_instance
            mock_async_client_instance.post = AsyncMock(side_effect=Exception("网络错误"))
            mock_client.return_value = mock_async_client_instance
            
            # 调用方法
            result = await manager.call_mcp_server("http://localhost:8080/mcp", {"test": "data"})
            
            # 验证返回值包含错误信息
            assert "MCP调用失败" in result
            assert "网络错误" in result

    @pytest.mark.asyncio
    async def test_execute_tool_success(self):
        """测试成功执行工具"""
        manager = ToolManager()
        
        # 创建一个mock工具
        mock_tool = Mock()
        mock_tool.run = Mock(return_value="工具执行结果")
        manager.tools["test_tool"] = mock_tool
        
        # 使用patch模拟asyncio.get_event_loop
        with patch('src.backend.manager.tool_manager.asyncio.get_event_loop') as mock_loop:
            # 设置mock返回值
            mock_loop_instance = Mock()
            mock_loop.return_value = mock_loop_instance
            mock_loop_instance.run_in_executor = AsyncMock(return_value="工具执行结果")
            
            # 调用方法
            result = await manager.execute_tool("test_tool", "测试输入")
            
            # 验证调用
            mock_loop.assert_called_once()
            mock_loop_instance.run_in_executor.assert_awaited_once()
            
            # 验证返回值
            assert result == "工具执行结果"

    @pytest.mark.asyncio
    async def test_execute_tool_nonexistent(self):
        """测试执行不存在的工具"""
        manager = ToolManager()
        
        # 调用不存在的工具
        result = await manager.execute_tool("nonexistent_tool", "测试输入")
        
        # 验证返回值
        assert "工具 nonexistent_tool 不存在" in result

    @pytest.mark.asyncio
    async def test_execute_tool_exception(self):
        """测试执行工具时发生异常"""
        manager = ToolManager()
        
        # 创建一个mock工具
        mock_tool = Mock()
        mock_tool.run = Mock(side_effect=Exception("工具执行错误"))
        manager.tools["test_tool"] = mock_tool
        
        # 使用patch模拟asyncio.get_event_loop
        with patch('src.backend.manager.tool_manager.asyncio.get_event_loop') as mock_loop:
            # 设置mock返回值
            mock_loop_instance = Mock()
            mock_loop.return_value = mock_loop_instance
            mock_loop_instance.run_in_executor = AsyncMock(side_effect=Exception("工具执行错误"))
            
            # 调用方法
            result = await manager.execute_tool("test_tool", "测试输入")
            
            # 验证返回值包含错误信息
            assert "工具执行失败" in result
            assert "工具执行错误" in result

    def test_list_tools(self):
        """测试获取可用工具列表"""
        manager = ToolManager()
        
        # 手动添加一个测试工具
        mock_tool = Mock()
        mock_tool.description = "测试工具描述"
        manager.tools["test_tool"] = mock_tool
        
        # 调用方法
        result = manager.list_tools()
        
        # 验证返回值
        assert isinstance(result, list)
        # 至少应包含我们添加的测试工具和默认的MCP工具
        assert len(result) >= 1
        # 验证测试工具在列表中
        test_tool_found = False
        for tool_info in result:
            if tool_info["name"] == "test_tool":
                assert tool_info["description"] == "测试工具描述"
                test_tool_found = True
        assert test_tool_found


if __name__ == "__main__":
    pytest.main([__file__, "-v"])