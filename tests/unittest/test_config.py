import pytest
import sys
import os

# 将src目录添加到Python路径中，以便正确导入
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from config import BACKEND_IP, BACKEND_PORT


def test_config_values():
    """测试配置文件中的常量值"""
    # 验证BACKEND_IP的值
    assert BACKEND_IP == "localhost"
    
    # 验证BACKEND_PORT的值
    assert BACKEND_PORT == 8000


def test_config_types():
    """测试配置值的类型"""
    # 验证BACKEND_IP是字符串类型
    assert isinstance(BACKEND_IP, str)
    
    # 验证BACKEND_PORT是整数类型
    assert isinstance(BACKEND_PORT, int)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])