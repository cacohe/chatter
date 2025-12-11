import pytest
import os
import logging
import tempfile
from unittest.mock import patch, MagicMock

# 添加src目录到Python路径中，以便正确导入
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from infra.log.logger import logger, host_name


def test_logger_creation():
    """测试logger实例是否正确创建"""
    # 验证logger对象已创建
    assert logger is not None
    assert isinstance(logger, logging.Logger)
    
    # 验证logger名称
    assert logger.name == "infra.log.logger"
    
    # 验证日志级别
    assert logger.level == logging.INFO


def test_host_name():
    """测试主机名获取"""
    # 验证主机名已获取
    assert host_name is not None
    assert isinstance(host_name, str)
    assert len(host_name) > 0


def test_logger_handlers():
    """测试logger处理器配置"""
    # 验证至少有两个处理器（文件和控制台）
    assert len(logger.handlers) >= 2
    
    # 检查是否存在文件处理器
    file_handler_exists = any(isinstance(handler, logging.FileHandler) for handler in logger.handlers)
    assert file_handler_exists
    
    # 检查是否存在控制台处理器
    console_handler_exists = any(isinstance(handler, logging.StreamHandler) for handler in logger.handlers)
    assert console_handler_exists


def test_log_format():
    """测试日志格式"""
    # 获取一个处理器来检查格式化器
    handler = logger.handlers[0]
    formatter = handler.formatter
    
    # 验证格式化器存在
    assert formatter is not None
    
    # 验证格式包含必要的字段
    format_string = formatter._fmt
    assert '%(asctime)s' in format_string
    assert '%(levelname)s' in format_string
    assert host_name in format_string
    assert '%(message)s' in format_string
    assert '%(filename)s' in format_string
    assert '%(lineno)d' in format_string


def test_log_file_creation(self):
    """测试日志文件是否正确创建"""
    with tempfile.TemporaryDirectory() as temp_dir:
        # 确保临时目录存在
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir)
        
        # 模拟日志目录
        with patch('infra.log.logger.LOG_DIR', temp_dir):
            # 创建logger实例
            logger_instance = setup_logger()
            
            # 记录一条日志
            logger_instance.info("Test log entry")
            
            # 验证日志文件是否存在
            log_files = os.listdir(temp_dir)
            self.assertGreaterEqual(len(log_files), 1)  # 可能有多个文件
            self.assertTrue(any(file.endswith('.log') for file in log_files))


def test_logger_output():
    """测试logger输出"""
    # 创建内存中的字符串IO来捕获日志输出
    from io import StringIO
    log_capture = StringIO()
    
    # 添加一个StreamHandler到logger来捕获输出
    capture_handler = logging.StreamHandler(log_capture)
    # 使用与原始格式相同的格式
    formatter = logging.Formatter('%(asctime)s\t%(levelname)s\t' + host_name +
                                '\t%(message)s\t[%(filename)s]\t[%(lineno)d]')
    capture_handler.setFormatter(formatter)
    logger.addHandler(capture_handler)
    
    # 记录一条测试消息
    test_message = "Test log message for unit test"
    logger.info(test_message)
    
    # 移除捕获处理器
    logger.removeHandler(capture_handler)
    
    # 验证日志消息被捕获
    log_contents = log_capture.getvalue()
    assert test_message in log_contents
    assert 'INFO' in log_contents
    assert host_name in log_contents


if __name__ == "__main__":
    pytest.main([__file__, "-v"])